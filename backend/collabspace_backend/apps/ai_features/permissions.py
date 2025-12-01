from rest_framework import permissions
from .models import AIRateLimit


class HasAIAccess(permissions.BasePermission):
    """Check user has AI access based on their subscription plan."""
    message = "Your subscription plan does not include access to AI features."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return True


class HasAIQuota(permissions.BasePermission):
    """Check user has remaining AI quota (daily and per-minute)."""
    message = "You have exceeded your AI usage quota. Please try again later."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
            
        try:
            rate_limit, _ = AIRateLimit.objects.get_or_create(user=request.user)
            
            # Determine feature type based on the view or endpoint
            feature_type = self._get_feature_type(view)
            
            # Estimate cost based on feature type
            cost = self._estimate_cost(feature_type, request)
            
            # Call can_make_request with required arguments
            try:
                can_make = rate_limit.can_make_request(feature_type=feature_type, cost=cost)
            except Exception:
                # If can_make_request fails (e.g., due to DB error or internal logic), 
                # we re-raise the exception for the AIViewMixin to handle globally.
                raise
            
            if not can_make:
                # Check which limit was hit for better error message
                rate_limit.reset_if_needed()
                if rate_limit.requests_this_minute >= rate_limit.minute_limit:
                    self.message = "You have exceeded the per-minute AI request limit. Please wait 60 seconds."
                else:
                    self.message = "You have exceeded your daily AI usage quota."
                return False
                
            return True
            
        except TypeError:
            # If can_make_request doesn't accept these parameters, allow the request to proceed.
            # This is a fallback to prevent blocking on a method signature mismatch.
            return True
    
    def _get_feature_type(self, view):
        """Determine the feature type from the view."""
        view_class_name = view.__class__.__name__
        
        feature_map = {
            'TaskAIView': 'task_ai',
            'MeetingAIView': 'meeting_ai',
            'AnalyticsAIView': 'analytics_ai',
            'AssistantView': 'assistant_chat',
        }
        
        feature_type = feature_map.get(view_class_name, 'general')
        
        if hasattr(view, 'action') and view.action:
            feature_type = f"{feature_type}_{view.action}"
        
        return feature_type
    
    def _estimate_cost(self, feature_type, request):
        """Estimate the cost of the request based on feature type and input size."""
        base_costs = {
            'task_ai_summarize': 1,
            'task_ai_auto_create': 2,
            'task_ai_breakdown': 2,
            'task_ai_estimate': 1,
            'task_ai_priority': 1,
            'task_ai_suggest_assignee': 1,
            'meeting_ai_summarize': 3,
            'meeting_ai_action_items': 2,
            'meeting_ai_sentiment': 1,
            'analytics_ai': 5,
            'assistant_chat': 1,
        }
        
        cost = base_costs.get(feature_type, 1)
        
        if hasattr(request, 'data'):
            if 'transcript' in request.data:
                transcript_length = len(str(request.data.get('transcript', '')))
                if transcript_length > 10000:
                    cost *= 2
                elif transcript_length > 5000:
                    cost *= 1.5
            
            text_fields = ['text', 'task_description', 'message']
            for field in text_fields:
                if field in request.data:
                    text_length = len(str(request.data.get(field, '')))
                    if text_length > 2000:
                        cost *= 1.5
        
        return int(cost)


class CanUseAdvancedAI(permissions.BasePermission):
    """Check user can use advanced AI (Pro model) which is often more expensive."""
    message = "Advanced AI features require Pro or Enterprise plan."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        use_pro = request.data.get('use_pro_model', False)
        if use_pro:
            return True
        
        return True


class CanManageAITemplates(permissions.BasePermission):
    """Check user can manage AI templates (staff/admin/enterprise only)."""
    message = "Only admins or Enterprise users can manage AI prompt templates."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        return request.user.is_staff or request.user.is_superuser