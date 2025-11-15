"""
Authentication models for CollabSpace AI.

Custom User model with extended fields and functionality.
"""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel
import uuid


class UserManager(BaseUserManager):
    """
    Custom user manager for creating users and superusers.
    """
    
    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a regular user with the given email and password.
        """
        if not email:
            raise ValueError(_('The Email field must be set'))
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and save a superuser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    """
    Custom User model for CollabSpace AI.
    
    Uses email instead of username for authentication.
    """
    
    # Unique identifier
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Authentication fields
    email = models.EmailField(
        _('email address'),
        unique=True,
        db_index=True,
        error_messages={
            'unique': _("A user with that email already exists."),
        }
    )
    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        db_index=True,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        error_messages={
            'unique': _("A user with that username already exists."),
        }
    )
    
    # Personal information
    first_name = models.CharField(_('first name'), max_length=150, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)
    avatar = models.URLField(_('avatar URL'), max_length=500, blank=True, null=True)
    bio = models.TextField(_('bio'), max_length=500, blank=True)
    location = models.CharField(_('location'), max_length=100, blank=True)
    user_timezone = models.CharField(_('timezone'), max_length=50, default='UTC')

    
    # Contact information
    phone_number = models.CharField(_('phone number'), max_length=20, blank=True)
    
    # Account status
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Designates whether this user should be treated as active. '
                    'Unselect this instead of deleting accounts.')
    )
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.')
    )
    is_superuser = models.BooleanField(
        _('superuser status'),
        default=False,
        help_text=_('Designates that this user has all permissions without explicitly assigning them.')
    )
    
    # Email verification
    is_email_verified = models.BooleanField(_('email verified'), default=False)
    email_verification_token = models.CharField(max_length=255, blank=True, null=True)
    email_verification_sent_at = models.DateTimeField(blank=True, null=True)
    
    # Two-Factor Authentication
    two_factor_enabled = models.BooleanField(_('2FA enabled'), default=False)
    two_factor_secret = models.CharField(max_length=32, blank=True, null=True)
    
    # Account metadata
    last_login = models.DateTimeField(_('last login'), blank=True, null=True)
    last_activity = models.DateTimeField(_('last activity'), auto_now=True)
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    
    # Subscription/Plan
    plan_type = models.CharField(
        max_length=20,
        choices=[
            ('free', 'Free'),
            ('pro', 'Pro'),
            ('enterprise', 'Enterprise'),
        ],
        default='free'
    )
    
    # Manager
    objects = UserManager()
    
    # Configuration
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        db_table = 'users'
        ordering = ['-date_joined']
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = f'{self.first_name} {self.last_name}'
        return full_name.strip() or self.username
    
    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name or self.username
    
    @property
    def full_name(self):
        """Property shortcut for get_full_name()."""
        return self.get_full_name()
    
    def update_last_activity(self):
        """Update the last activity timestamp."""
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])


class PasswordResetToken(TimeStampedModel):
    """
    Model to store password reset tokens.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reset_tokens')
    token = models.CharField(max_length=255, unique=True, db_index=True)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'password_reset_tokens'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Reset token for {self.user.email}"
    
    def is_valid(self):
        """Check if token is still valid (not used and not expired)."""
        return not self.is_used and timezone.now() < self.expires_at
    
    def mark_as_used(self):
        """Mark token as used."""
        self.is_used = True
        self.save(update_fields=['is_used'])


class UserSession(TimeStampedModel):
    """
    Model to track user sessions for security purposes.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=255, unique=True, db_index=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    device_info = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    last_activity = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'user_sessions'
        ordering = ['-last_activity']
    
    def __str__(self):
        return f"{self.user.email} - {self.ip_address}"
    
    def is_valid(self):
        """Check if session is still valid."""
        return self.is_active and timezone.now() < self.expires_at
    
    def deactivate(self):
        """Deactivate the session."""
        self.is_active = False
        self.save(update_fields=['is_active'])