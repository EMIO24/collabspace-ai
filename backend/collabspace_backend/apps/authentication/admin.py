"""
Django admin configuration for authentication models.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, PasswordResetToken, UserSession


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin interface for User model.
    """
    list_display = [
        'email', 'username', 'full_name', 'plan_type',
        'is_email_verified', 'is_active', 'date_joined'
    ]
    list_filter = [
        'is_active', 'is_staff', 'is_superuser',
        'is_email_verified', 'plan_type', 'date_joined'
    ]
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {
            'fields': ('email', 'username', 'password')
        }),
        (_('Personal info'), {
            'fields': ('first_name', 'last_name', 'avatar', 'bio', 'location', 'timezone', 'phone_number')
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        (_('Email Verification'), {
            'fields': ('is_email_verified', 'email_verification_token', 'email_verification_sent_at')
        }),
        (_('Two-Factor Auth'), {
            'fields': ('two_factor_enabled', 'two_factor_secret')
        }),
        (_('Subscription'), {
            'fields': ('plan_type',)
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'last_activity', 'date_joined')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ['date_joined', 'last_login', 'last_activity']


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    """
    Admin interface for PasswordResetToken model.
    """
    list_display = ['user', 'is_used', 'expires_at', 'created_at']
    list_filter = ['is_used', 'created_at']
    search_fields = ['user__email', 'token']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """
    Admin interface for UserSession model.
    """
    list_display = ['user', 'ip_address', 'is_active', 'last_activity', 'expires_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__email', 'ip_address']
    readonly_fields = ['created_at', 'updated_at', 'last_activity']
    ordering = ['-last_activity']