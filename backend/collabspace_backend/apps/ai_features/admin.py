import csv
from django.contrib import admin
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta
from .models import AIUsage, AIPromptTemplate, AIRateLimit, AICache


@admin.register(AIUsage)
class AIUsageAdmin(admin.ModelAdmin):
    list_display = ['user', 'feature_type', 'model_used', 'total_tokens', 'success', 'created_at']
    list_filter = ['feature_type', 'model_used', 'success', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'request_data', 'response_data', 'error_message', 'processing_time']
    date_hierarchy = 'created_at'

    actions = ['export_usage_csv']

    @admin.action(description='Export selected usage data to CSV')
    def export_usage_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=ai_usage_export.csv'
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in field_names])

        return response


@admin.register(AIPromptTemplate)
class AIPromptTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'default_model', 'is_active', 'created_by']
    list_filter = ['category', 'default_model', 'is_active']
    search_fields = ['name', 'description']
    readonly_fields = ['created_by']
    
    actions = ['duplicate_template', 'test_template']

    @admin.action(description='Duplicate selected templates')
    def duplicate_template(self, request, queryset):
        for template in queryset:
            template.pk = None  # Force creation of new object
            template.name = f"{template.name} (Copy)"
            template.created_by = request.user
            template.save()
        self.message_user(request, f"Duplicated {queryset.count()} templates.")

    @admin.action(description='Test selected templates (View only)')
    def test_template(self, request, queryset):
        self.message_user(request, "This action typically requires a dedicated endpoint or Celery task to execute a live test.")


@admin.register(AIRateLimit)
class AIRateLimitAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan_type', 'requests_today', 'daily_limit', 'last_reset', 'requests_this_minute']
    list_filter = ['plan_type', 'last_reset']
    search_fields = ['user__username', 'user__email']

    actions = ['reset_limits']

    @admin.action(description='Reset selected users\' daily and minute limits')
    def reset_limits(self, request, queryset):
        queryset.update(
            requests_today=0, 
            tokens_today=0, 
            requests_this_minute=0, 
            last_reset=timezone.now(),
            minute_reset_at=timezone.now()
        )
        self.message_user(request, f"Reset limits for {queryset.count()} users.")


@admin.register(AICache)
class AICacheAdmin(admin.ModelAdmin):
    list_display = ['request_hash', 'model_used', 'access_count', 'created_at', 'last_accessed', 'is_expired']
    list_filter = ['model_used', 'created_at']
    search_fields = ['request_hash', 'prompt']
    readonly_fields = ['created_at', 'last_accessed']

    actions = ['clear_expired_cache']

    @admin.action(description='Clear expired cache entries')
    def clear_expired_cache(self, request, queryset):
        now = timezone.now()
        expired_count = 0
        
        # Manually iterate to use the is_expired method
        for cache_entry in queryset:
            if cache_entry.is_expired():
                cache_entry.delete()
                expired_count += 1
                
        self.message_user(request, f"Cleaned up {expired_count} expired cache entries.")