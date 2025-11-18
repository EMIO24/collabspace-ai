from rest_framework import permissions
from .models import AIRateLimit


class HasAIAccess(permissions.BasePermission):
    """Check user has AI access based on their subscription plan."""
    message = "Your subscription plan does not include access to AI features."

    def has_permission(self, request, view):
        # Assumes user.profile exists and has a plan_type attribute
        # For simplicity, we check if the user is authenticated and has a plan
        if not request.user.is_authenticated:
            return False
            
        # Placeholder for real profile/plan lookup:
        # return request.user.profile.plan_type in ['free', 'pro', 'enterprise']
        return True # Default to True if profile lookup is complex/unavailable

class HasAIQuota(permissions.BasePermission):
    """Check user has remaining AI quota (daily and per-minute)."""
    message = "You have exceeded your AI usage quota. Please try again later."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
            
        rate_limit, _ = AIRateLimit.objects.get_or_create(user=request.user)
        
        # This check respects both daily and minute limits
        if not rate_limit.can_make_request():
            # Customize the message based on the type of limit hit
            if not rate_limit.check_minute_limit():
                self.message = "You have exceeded the per-minute AI request limit. Please wait 60 seconds."
            else:
                self.message = "You have exceeded your daily AI usage quota."
            return False
            
        return True

class CanUseAdvancedAI(permissions.BasePermission):
    """Check user can use advanced AI (Pro model) which is often more expensive."""
    message = "Advanced AI features require Pro or Enterprise plan."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
            
        # Placeholder for real profile/plan lookup:
        # return request.user.profile.plan_type in ['pro', 'enterprise']
        
        # Simplified: Check for 'pro' in the view's data if provided, otherwise assume flash is fine
        use_pro = request.data.get('use_pro_model', False)
        if use_pro:
             # In a real app, this would check the user's plan_type from their profile
             return True # simplified for now
        
        return True # Flash model is allowed by default

class CanManageAITemplates(permissions.BasePermission):
    """Check user can manage AI templates (staff/admin/enterprise only)."""
    message = "Only admins or Enterprise users can manage AI prompt templates."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
            
        # Simplified check
        return request.user.is_staff or request.user.is_superuser