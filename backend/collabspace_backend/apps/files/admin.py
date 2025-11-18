from django.contrib import admin
from .models import File, FileVersion, SharedLink

@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'workspace', 'uploaded_by', 'file_type', 'file_size', 'download_count', 'created_at']
    list_filter = ['file_type', 'is_public', 'created_at', 'workspace']
    search_fields = ['file_name', 'uploaded_by__username', 'related_to_type']
    readonly_fields = ['cloudinary_public_id', 'cloudinary_url', 'thumbnail_url', 'download_count', 'width', 'height', 'duration']

@admin.register(FileVersion)
class FileVersionAdmin(admin.ModelAdmin):
    list_display = ['file', 'version_number', 'uploaded_by', 'file_size', 'created_at']
    list_filter = ['created_at']
    search_fields = ['file__file_name']
    readonly_fields = ['cloudinary_public_id', 'cloudinary_url', 'file_size']

@admin.register(SharedLink)
class SharedLinkAdmin(admin.ModelAdmin):
    list_display = ['file', 'token', 'created_by', 'expires_at', 'download_count', 'max_downloads', 'is_valid']
    list_filter = ['expires_at', 'created_at', 'max_downloads']
    readonly_fields = ['token', 'download_count', 'password', 'created_by']

    def is_valid(self, obj):
        return obj.is_valid()
    is_valid.boolean = True