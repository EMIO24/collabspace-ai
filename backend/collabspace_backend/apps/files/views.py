from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db import transaction
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.db.models import Q
import secrets

from .models import File, FileVersion, SharedLink
from .serializers import *
from .services.cloudinary_service import CloudinaryService

class FileViewSet(viewsets.ModelViewSet):
    """File operations"""
    serializer_class = FileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def _get_allowed_workspace_ids(self):
        """
        Get a set of workspace IDs that the current user has access to.
        Checks both 'owned_workspaces' and 'workspace_memberships'.
        """
        user = self.request.user
        
        # 1. IDs of workspaces the user owns
        owned_ids = user.owned_workspaces.values_list('id', flat=True)
        
        # 2. IDs of workspaces where user is an ACTIVE member
        # Note: We filter by is_active=True based on your WorkspaceMember model
        member_ids = user.workspace_memberships.filter(is_active=True).values_list('workspace_id', flat=True)
        
        # 3. Return union of IDs
        return owned_ids.union(member_ids)

    def get_queryset(self):
        # Use the ID list to filter. This avoids the "Cannot use QuerySet for File" error
        # because we are passing raw UUIDs, which Django handles perfectly for ForeignKeys.
        allowed_ids = self._get_allowed_workspace_ids()
        
        queryset = File.objects.filter(workspace_id__in=allowed_ids).select_related('uploaded_by', 'workspace')

        # Filter by specific workspace if requested
        workspace_id = self.request.query_params.get('workspace')
        if workspace_id:
            queryset = queryset.filter(workspace_id=workspace_id)

        # Filter by related object (polymorphic association)
        related_type = self.request.query_params.get('related_type')
        related_id = self.request.query_params.get('related_id')
        if related_type and related_id:
            queryset = queryset.filter(
                related_to_type=related_type,
                related_to_id=related_id
            )
        return queryset

    def create(self, request):
        """Upload file to Cloudinary and create file record"""
        file_obj = request.FILES.get('file')
        workspace_id = request.data.get('workspace') 
        
        if not file_obj or not workspace_id:
            return Response({'error': 'File and workspace ID are required'}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Validate permissions
        # We explicitly check if the requested workspace_id is in the user's allowed list
        allowed_ids = self._get_allowed_workspace_ids()
        # Convert workspace_id to string for comparison if it's a UUID object, or rely on QuerySet check
        # simpler: check if the specific ID exists in our allowed list query
        if str(workspace_id) not in [str(uid) for uid in allowed_ids]:
            return Response({'error': 'Permission denied. You do not have access to this workspace.'}, status=status.HTTP_403_FORBIDDEN)

        # 2. Validate file against size/type limits
        is_valid, message = CloudinaryService.validate_file(file_obj)
        if not is_valid:
            return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Optional: Compress image
        if file_obj.content_type.startswith('image/'):
            file_obj = CloudinaryService.compress_image(file_obj)

        folder = f"workspace_{workspace_id}/uploads"
        
        # 4. Upload to Cloudinary
        upload_result = CloudinaryService.upload_file(file_obj, folder=folder)

        if not upload_result['success']:
            return Response({'error': upload_result['error']}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 5. Create File record with Cleanup Strategy
        try:
            with transaction.atomic():
                file_record = File.objects.create(
                    workspace_id=workspace_id,
                    uploaded_by=request.user,
                    file_name=file_obj.name,
                    file_size=file_obj.size,
                    file_type=file_obj.content_type,
                    cloudinary_public_id=upload_result['public_id'],
                    cloudinary_url=upload_result['url'],
                    width=upload_result.get('width'),
                    height=upload_result.get('height'),
                    duration=upload_result.get('duration'),
                    related_to_type=request.data.get('related_to_type'),
                    related_to_id=request.data.get('related_to_id'),
                    is_public=request.data.get('is_public', False)
                )

                # Generate thumbnail
                thumbnail_url = CloudinaryService.generate_thumbnail(
                    upload_result['public_id'], file_record.file_type
                )
                if thumbnail_url:
                    file_record.thumbnail_url = thumbnail_url
                    file_record.save(update_fields=['thumbnail_url'])

                serializer = self.get_serializer(file_record)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            # CLEANUP STRATEGY:
            # Database creation failed, so we must delete the orphaned file from Cloudinary
            CloudinaryService.delete_file(upload_result['public_id'], file_obj.content_type)
            return Response({'error': f'Database error, upload rolled back: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def destroy(self, request, pk=None):
        """Delete file from Cloudinary and database"""
        file_obj = self.get_object()

        # Check deletion permission
        workspace = file_obj.workspace
        is_owner = workspace.owner == request.user
        is_uploader = file_obj.uploaded_by == request.user
        
        # Also check if user is an 'admin' in the workspace via WorkspaceMember
        is_admin = request.user.workspace_memberships.filter(
            workspace=workspace, 
            role__in=['admin', 'owner'],
            is_active=True
        ).exists()
        
        if not (is_uploader or is_owner or is_admin):
            return Response({'error': 'Permission denied. Only the uploader, admin, or workspace owner can delete files.'}, status=status.HTTP_403_FORBIDDEN)

        with transaction.atomic():
            # Delete versions from Cloudinary first
            for version in file_obj.versions.all():
                CloudinaryService.delete_file(version.cloudinary_public_id, file_obj.file_type)

            # Delete main file from Cloudinary
            file_obj.delete_from_cloudinary()

            # Delete from database (versions and shared links are cascaded)
            file_obj.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Track download and return file URL"""
        file_obj = self.get_object()
        file_obj.increment_download_count()

        return Response({
            'url': file_obj.cloudinary_url,
            'filename': file_obj.file_name
        })

    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        """Create shared link for file"""
        file_obj = self.get_object()

        token = secrets.token_urlsafe(32)
        password = request.data.get('password')
        
        # Use Django make_password for secure hashing
        hashed_password = make_password(password) if password else None

        shared_link = SharedLink.objects.create(
            file=file_obj,
            token=token,
            expires_at=request.data.get('expires_at'),
            max_downloads=request.data.get('max_downloads'),
            password=hashed_password,
            created_by=request.user
        )

        serializer = SharedLinkSerializer(shared_link, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def create_version(self, request, pk=None):
        """Upload new version of file"""
        file_obj = self.get_object()
        new_file = request.FILES.get('file')

        if not new_file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        # Permission check: Ensure user still has access to the workspace of this file
        allowed_ids = self._get_allowed_workspace_ids()
        if file_obj.workspace_id not in allowed_ids:
             return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        # Validation
        is_valid, message = CloudinaryService.validate_file(new_file)
        if not is_valid:
            return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)

        if new_file.content_type.startswith('image/'):
            new_file = CloudinaryService.compress_image(new_file)

        # Upload first
        upload_result = CloudinaryService.upload_file(
            new_file,
            folder=f"workspace_{file_obj.workspace_id}/versions/{file_obj.id}"
        )

        if not upload_result['success']:
            return Response({'error': upload_result['error']}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            with transaction.atomic():
                version_number = file_obj.versions.count() + 1
                version = FileVersion.objects.create(
                    file=file_obj,
                    version_number=version_number,
                    cloudinary_public_id=upload_result['public_id'],
                    cloudinary_url=upload_result['url'],
                    file_size=new_file.size,
                    uploaded_by=request.user,
                    change_description=request.data.get('description', '')
                )
                serializer = FileVersionSerializer(version, context={'request': request})
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            # Cleanup Orphaned Cloudinary file
            CloudinaryService.delete_file(upload_result['public_id'], new_file.content_type)
            return Response({'error': f'Database error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def versions(self, request, pk=None):
        """Get file version history"""
        file_obj = self.get_object()
        versions = file_obj.versions.all()
        serializer = FileVersionSerializer(versions, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search files by name"""
        query = request.query_params.get('q', '')
        workspace_id = request.query_params.get('workspace')
        
        # Start with the queryset filtered by user's workspaces
        files = self.get_queryset() 

        if workspace_id:
            files = files.filter(workspace_id=workspace_id)

        if query:
            files = files.filter(file_name__icontains=query)

        serializer = self.get_serializer(files, many=True)
        return Response(serializer.data)

class SharedFileView(APIView):
    """Access shared file via token"""
    permission_classes = [AllowAny]

    def get(self, request, token):
        try:
            shared_link = SharedLink.objects.select_related('file').get(token=token)

            # Check validity
            if not shared_link.is_valid():
                return Response({'error': 'Link expired or download limit reached'}, status=status.HTTP_403_FORBIDDEN)

            # Check password
            password = request.query_params.get('password')
            if shared_link.password:
                # Use the model's check_password method (wraps django.contrib.auth.hashers)
                if not password or not shared_link.check_password(password):
                    return Response({'error': 'Invalid password'}, status=status.HTTP_403_FORBIDDEN)

            # Increment counts in a transaction
            with transaction.atomic():
                shared_link.increment_download()
                shared_link.file.increment_download_count()

            return Response({
                'file_name': shared_link.file.file_name,
                'file_size': shared_link.file.file_size,
                'file_type': shared_link.file.file_type,
                'url': shared_link.file.cloudinary_url,
                'thumbnail_url': shared_link.file.thumbnail_url
            })

        except SharedLink.DoesNotExist:
            return Response({'error': 'Invalid link'}, status=status.HTTP_404_NOT_FOUND)

class FileStorageStatsView(APIView):
    """Get storage statistics for workspace"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        workspace_id = request.query_params.get('workspace')

        if not workspace_id:
            return Response({'error': 'Workspace ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Check permission: Manually verify against user's owned/member workspaces
        user = request.user
        
        # 1. Check ownership
        is_owner = user.owned_workspaces.filter(id=workspace_id).exists()
        
        # 2. Check membership
        is_member = user.workspace_memberships.filter(workspace_id=workspace_id, is_active=True).exists()
        
        if not (is_owner or is_member):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        from django.db.models import Sum, Count
        stats = File.objects.filter(workspace_id=workspace_id).aggregate(
            total_files=Count('id'),
            total_size=Sum('file_size')
        )

        # Cloudinary free tier limit (customize as needed)
        free_tier_limit = 25 * 1024 * 1024 * 1024  # 25GB in bytes
        total_size_bytes = stats['total_size'] or 0
        percentage_used = round((total_size_bytes / free_tier_limit * 100), 2) if free_tier_limit > 0 else 0

        # Helper to format bytes
        def format_bytes(num):
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if num < 1024.0:
                    return f"{num:.1f} {unit}"
                num /= 1024.0
            return f"{num:.1f} PB"

        return Response({
            'total_files': stats['total_files'] or 0,
            'total_size_bytes': total_size_bytes,
            'total_size_human_readable': format_bytes(total_size_bytes),
            'limit_bytes': free_tier_limit,
            'limit_human_readable': format_bytes(free_tier_limit),
            'percentage_used': percentage_used
        })