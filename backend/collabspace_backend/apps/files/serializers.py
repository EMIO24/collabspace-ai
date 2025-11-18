from rest_framework import serializers
from .models import File, FileVersion, SharedLink

class FileSerializer(serializers.ModelSerializer):
    uploaded_by = serializers.SerializerMethodField()
    size_formatted = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()
    workspace_name = serializers.CharField(source='workspace.name', read_only=True)

    class Meta:
        model = File
        fields = [
            'id', 'workspace', 'workspace_name', 'uploaded_by', 'file_name',
            'file_size', 'size_formatted', 'file_type', 'cloudinary_public_id',
            'cloudinary_url', 'thumbnail_url', 'thumbnail', 'related_to_type',
            'related_to_id', 'is_public', 'download_count', 'width', 'height',
            'duration', 'created_at', 'updated_at'
        ]
        read_only_fields = [f for f in fields if f not in ['workspace', 'file_name', 'related_to_type', 'related_to_id', 'is_public']]

    def get_uploaded_by(self, obj):
        if obj.uploaded_by:
            return {
                'id': str(obj.uploaded_by.id),
                'username': obj.uploaded_by.username,
                'full_name': obj.uploaded_by.get_full_name() if hasattr(obj.uploaded_by, 'get_full_name') else obj.uploaded_by.username
            }
        return None

    def get_size_formatted(self, obj):
        # Format bytes to human readable
        num = obj.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if num < 1024.0:
                return f"{num:.1f} {unit}"
            num /= 1024.0
        return f"{num:.1f} TB"

    def get_thumbnail(self, obj):
        # Use thumbnail_url field directly, it's generated on create/update
        return obj.thumbnail_url

class FileVersionSerializer(serializers.ModelSerializer):
    uploaded_by = serializers.SerializerMethodField()
    size_formatted = serializers.SerializerMethodField()

    class Meta:
        model = FileVersion
        fields = '__all__'

    def get_uploaded_by(self, obj):
        if obj.uploaded_by:
            return {
                'id': str(obj.uploaded_by.id),
                'username': obj.uploaded_by.username,
                'full_name': obj.uploaded_by.get_full_name() if hasattr(obj.uploaded_by, 'get_full_name') else obj.uploaded_by.username
            }
        return None

    def get_size_formatted(self, obj):
        # Format bytes to human readable
        num = obj.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if num < 1024.0:
                return f"{num:.1f} {unit}"
            num /= 1024.0
        return f"{num:.1f} TB"

class SharedLinkSerializer(serializers.ModelSerializer):
    share_url = serializers.SerializerMethodField()
    is_valid = serializers.SerializerMethodField()
    file_name = serializers.CharField(source='file.file_name', read_only=True)

    class Meta:
        model = SharedLink
        fields = '__all__'
        read_only_fields = ['token', 'created_by', 'download_count']

    def get_share_url(self, obj):
        request = self.context.get('request')
        if request:
            # Assumes the URL is mounted under /api/files/
            return request.build_absolute_uri(f'/api/files/shared/{obj.token}/')
        return None

    def get_is_valid(self, obj):
        return obj.is_valid()