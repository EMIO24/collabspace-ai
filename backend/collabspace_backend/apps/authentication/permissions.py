"""
Custom permissions for authentication module.
"""

from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Permission to only allow owners of an object to access it.
    """
    
    def has_object_permission(self, request, view, obj):
        """
        Check if the requesting user is the owner of the object.
        """
        return obj == request.user


class IsEmailVerified(permissions.BasePermission):
    """
    Permission to only allow users with verified email.
    """
    message = 'Email verification required. Please verify your email address.'
    
    def has_permission(self, request, view):
        """
        Check if user's email is verified.
        """
        return request.user.is_authenticated and request.user.is_email_verified


class IsActive(permissions.BasePermission):
    """
    Permission to only allow active users.
    """
    message = 'Your account has been deactivated. Please contact support.'
    
    def has_permission(self, request, view):
        """
        Check if user is active.
        """
        return request.user.is_authenticated and request.user.is_active


class IsPremiumUser(permissions.BasePermission):
    """
    Permission to only allow premium (Pro or Enterprise) users.
    """
    message = 'This feature requires a Pro or Enterprise plan. Please upgrade your account.'
    
    def has_permission(self, request, view):
        """
        Check if user has premium plan.
        """
        if not request.user.is_authenticated:
            return False
        
        return request.user.plan_type in ['pro', 'enterprise']


class IsEnterpriseUser(permissions.BasePermission):
    """
    Permission to only allow Enterprise plan users.
    """
    message = 'This feature requires an Enterprise plan. Please upgrade your account.'
    
    def has_permission(self, request, view):
        """
        Check if user has Enterprise plan.
        """
        if not request.user.is_authenticated:
            return False
        
        return request.user.plan_type == 'enterprise'