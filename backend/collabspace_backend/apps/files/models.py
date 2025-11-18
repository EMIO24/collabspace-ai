from django.db import models
from django.conf import settings
from uuid import uuid4

# Placeholder base models (Assume these are defined in a core app or similar)
class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True
        
# Get User model based on settings
User = settings.AUTH_USER_MODEL

class File(BaseModel):
    """File metadata"""
    # Assuming 'Workspace' model is defined elsewhere
    workspace = models.ForeignKey('workspaces.Workspace', on_delete=models.CASCADE) 
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_files')
    file_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField()  # bytes
    file_type = models.CharField(max_length=100)  # MIME type
    s3_key = models.CharField(max_length=1024, unique=True) # S3 object key
    s3_url = models.URLField(max_length=512) # Signed or public URL
    thumbnail_url = models.URLField(max_length=512, null=True, blank=True)
    
    # Generic relationship fields
    RELATED_TO_CHOICES = (
        ('task', 'Task'),
        ('project', 'Project'),
        ('message', 'Message'),
    )
    related_to_type = models.CharField(max_length=50, choices=RELATED_TO_CHOICES, null=True, blank=True)
    related_to_id = models.UUIDField(null=True, blank=True)
    
    is_public = models.BooleanField(default=False)
    download_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return self.file_name

class FileVersion(TimeStampedModel):
    """File version history"""
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='versions')
    version_number = models.IntegerField()
    s3_key = models.CharField(max_length=1024)
    file_size = models.BigIntegerField()
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    change_description = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('file', 'version_number')
        ordering = ['-version_number']

class SharedLink(TimeStampedModel):
    """Public file sharing"""
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='shared_links')
    token = models.CharField(max_length=64, unique=True, default=lambda: uuid4().hex)
    expires_at = models.DateTimeField(null=True, blank=True)
    password = models.CharField(max_length=128, null=True, blank=True)
    max_downloads = models.IntegerField(null=True, blank=True)
    download_count = models.IntegerField(default=0)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"Link for {self.file.file_name} (Token: {self.token[:8]}...)"