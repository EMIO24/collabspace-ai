from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db import transaction
from django.conf import settings
import secrets
import hashlib # For password hashing in SharedLink

from .models import File, FileVersion, SharedLink
from .serializers import *
from .services.cloudinary_service import CloudinaryService

class FileViewSet(viewsets.ModelViewSet):
    """File operations"""
    serializer_class = FileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        # Filter files by workspaces the user belongs to (requires proper User/Workspace relationship)
        user_workspaces = self.request.user.workspaces.all() # Assuming User.workspaces is the relationship
        queryset = File.objects.filter(workspace__in=user_workspaces).select_related('uploaded_by', 'workspace')

        workspace_id = self.request.query_params.get('workspace')
        if workspace_id:
            queryset = queryset.filter(workspace_id=workspace_id)

        # Filter by related object
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

        # 1. Validate permissions (ensure user belongs to the workspace)
        # Add your actual permission check here, e.g.,
        # if not self.request.user.workspaces.filter(id=workspace_id).exists():
        #     return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

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

        # 5. Create File record in transaction
        with transaction.atomic():
            file_record = File.objects.create(
                workspace_id=workspace_id,
                uploaded_by=request.user,
                file_name=file_obj.name,
                file_size=file_obj.size, # Use Django file size for consistency
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

    def destroy(self, request, pk=None):
        """Delete file from Cloudinary and database"""
        file_obj = self.get_object()

        # Check deletion permission (e.g., owner or uploaded_by)
        # if file_obj.uploaded_by != request.user and file_obj.workspace.owner != request.user:
        #     return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

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
        hashed_password = hashlib.sha256(password.encode()).hexdigest() if password else None

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

        # Validation (re-use the main validation logic)
        is_valid, message = CloudinaryService.validate_file(new_file)
        if not is_valid:
            return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)

        if new_file.content_type.startswith('image/'):
            new_file = CloudinaryService.compress_image(new_file)

        with transaction.atomic():
            # Upload new version
            upload_result = CloudinaryService.upload_file(
                new_file,
                folder=f"workspace_{file_obj.workspace_id}/versions/{file_obj.id}"
            )

            if not upload_result['success']:
                return Response({'error': upload_result['error']}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Create version record
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
                if not password or hashlib.sha256(password.encode()).hexdigest() != shared_link.password:
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

        # Check permission (ensure user belongs to the workspace)
        # if not request.user.workspaces.filter(id=workspace_id).exists():
        #     return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

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