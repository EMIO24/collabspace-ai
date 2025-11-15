"""
Core abstract models for CollabSpace AI.

These base models provide common functionality across all apps.
"""

from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    """
    Abstract model that provides self-updating
    'created_at' and 'updated_at' fields.
    """
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        """Override save to ensure updated_at is set."""
        if self.pk:
            self.updated_at = timezone.now()
        super().save(*args, **kwargs)


class SoftDeleteModel(models.Model):
    """
    Abstract model that provides soft delete functionality.
    Records are marked as deleted instead of being removed from the database.
    """
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_deleted_items'
    )
    
    class Meta:
        abstract = True
    
    def soft_delete(self, user=None):
        """Mark the record as deleted."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        if user:
            self.deleted_by = user
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])
    
    def restore(self):
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])


class BaseModel(TimeStampedModel, SoftDeleteModel):
    """
    Base model combining timestamp and soft delete functionality.
    Most models should inherit from this.
    """
    
    class Meta:
        abstract = True
    
    def __str__(self):
        if hasattr(self, 'name'):
            return self.name
        elif hasattr(self, 'title'):
            return self.title
        return f"{self.__class__.__name__} {self.pk}"