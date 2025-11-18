import uuid
from django.db import models
from django.conf import settings
from apps.core.models import BaseModel # Assuming this is available

class File(BaseModel):
    """File metadata"""
    workspace = models.ForeignKey('workspaces.Workspace', on_delete=models.CASCADE, related_name='files')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='uploaded_files')
    file_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField()  # bytes
    file_type = models.CharField(max_length=100)  # MIME type
    cloudinary_public_id = models.CharField(max_length=255, unique=True)
    cloudinary_url = models.URLField()
    thumbnail_url = models.URLField(null=True, blank=True)

    # Generic relation to attach to any model
    related_to_type = models.CharField(max_length=50, null=True, blank=True)  # task, project, message
    related_to_id = models.UUIDField(null=True, blank=True)

    is_public = models.BooleanField(default=False)
    download_count = models.IntegerField(default=0)

    # Metadata
    width = models.IntegerField(null=True, blank=True)  # for images
    height = models.IntegerField(null=True, blank=True)  # for images
    duration = models.FloatField(null=True, blank=True)  # for videos/audio

    class Meta:
        db_table = 'files'
        indexes = [
            models.Index(fields=['workspace', 'uploaded_by']),
            models.Index(fields=['related_to_type', 'related_to_id']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return self.file_name

    def increment_download_count(self):
        self.download_count += 1
        self.save(update_fields=['download_count'])

    def delete_from_cloudinary(self):
        """Delete file from Cloudinary"""
        import cloudinary.uploader
        
        # Helper to determine resource_type based on MIME type
        def _get_resource_type(file_type):
            if file_type.startswith('image/'):
                return 'image'
            elif file_type.startswith('video/') or file_type.startswith('audio/'):
                return 'video'
            else:
                return 'raw'

        resource_type = _get_resource_type(self.file_type)
        try:
            cloudinary.uploader.destroy(self.cloudinary_public_id, resource_type=resource_type)
        except Exception as e:
            # In a real app, use proper logging
            print(f"Error deleting from Cloudinary: {e}")

class FileVersion(models.Model):
    """File version history"""
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='versions')
    version_number = models.IntegerField()
    cloudinary_public_id = models.CharField(max_length=255)
    cloudinary_url = models.URLField()
    file_size = models.BigIntegerField()
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    change_description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'file_versions'
        ordering = ['-version_number']
        unique_together = ['file', 'version_number']

    def __str__(self):
        return f"{self.file.file_name} v{self.version_number}"

class SharedLink(models.Model):
    """Public file sharing links"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='shared_links')
    token = models.CharField(max_length=64, unique=True, db_index=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    password = models.CharField(max_length=128, null=True, blank=True)  # Hashed password
    max_downloads = models.IntegerField(null=True, blank=True)
    download_count = models.IntegerField(default=0)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'shared_links'

    def __str__(self):
        return f"Share link for {self.file.file_name}"

    def is_valid(self):
        from django.utils import timezone
        # Check expiration
        if self.expires_at and self.expires_at < timezone.now():
            return False
        # Check download limit
        if self.max_downloads and self.download_count >= self.max_downloads:
            return False
        return True

    def increment_download(self):
        self.download_count += 1
        self.save(update_fields=['download_count'])