import uuid
from django.db import models
from django.conf import settings
from apps.core.models import BaseModel
from django.contrib.auth.hashers import make_password, check_password as django_check_password

class File(BaseModel):
    """File metadata"""
    workspace = models.ForeignKey('workspaces.Workspace', on_delete=models.CASCADE, related_name='files')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='uploaded_files')
    file_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField()
    file_type = models.CharField(max_length=100)
    cloudinary_public_id = models.CharField(max_length=255, unique=True)
    cloudinary_url = models.URLField()
    thumbnail_url = models.URLField(null=True, blank=True)

    related_to_type = models.CharField(max_length=50, null=True, blank=True)
    related_to_id = models.UUIDField(null=True, blank=True)

    is_public = models.BooleanField(default=False)
    download_count = models.IntegerField(default=0)

    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    duration = models.FloatField(null=True, blank=True)

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
    password = models.CharField(max_length=128, null=True, blank=True) # Now stores standard Django hash
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
        if self.expires_at and self.expires_at < timezone.now():
            return False
        if self.max_downloads and self.download_count >= self.max_downloads:
            return False
        return True

    def increment_download(self):
        self.download_count += 1
        self.save(update_fields=['download_count'])
    
    def set_password(self, raw_password):
        """Hashes the password using Django's standard hashers."""
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        """Checks the password using Django's standard hashers."""
        return django_check_password(raw_password, self.password)