from django.contrib import admin

class MockAdmin:
    def register(self, model):
        pass

class MockModelAdmin:
    def __init__(self, model):
        self.model = model
    list_display: tuple = ()
    list_filter: tuple = ()
    search_fields: tuple = ()
    actions: list = []

# Mock database model classes for context
class AIUsage:
    """Represents the AIUsage model (from models.py)"""
    pass
class AIPromptTemplate:
    """Represents the AIPromptTemplate model (from models.py)"""
    pass
class AIRateLimit:
    """Mock model to manage rate limits per plan type/user"""
    pass 

# Assume 'admin' is the globally available admin object (like django.contrib.admin)
admin = MockAdmin()


# --- 1. AIUsage Admin (Updated to include STT fields) ---

class AIUsageAdmin(MockModelAdmin):
    """Admin interface for monitoring and auditing AI usage."""
    
    list_display = (
        'user_id', 
        'provider', 
        'service_type', # New field: 'text_generation', 'code_review', 'transcription'
        'model_name', 
        'input_tokens', 
        'output_tokens', 
        'audio_minutes', # New field for STT/Audio
        'cost_usd', 
        'timestamp'
    )
    
    list_filter = (
        'provider', 
        'model_name', 
        'service_type', # New filter for transcription tasks
        'timestamp'
    )
    
    search_fields = (
        'user_id', 
        'model_name',
        'context_id'
    )

    # Custom action to export selected usage records
    def export_as_csv(self, request, queryset):
        # In a real implementation, this generates a CSV file from the queryset
        self.message_user(request, f"Exported {queryset.count()} usage records.")
    
    export_as_csv.short_description = "Export Selected Usage to CSV"
    
    actions = ['export_as_csv']
    
    # Custom display fields (mocked functions for cost summary)
    def total_tokens(self, obj):
        return obj.input_tokens + obj.output_tokens
    
    def formatted_cost(self, obj):
        return f"${obj.cost_usd:.5f}"


# --- 2. AIPromptTemplate Admin ---

class AIPromptTemplateAdmin(MockModelAdmin):
    """Admin interface for creating and managing reusable prompt templates."""
    
    list_display = (
        'name', 
        'key', 
        'model_name', 
        'is_active'
    )
    
    list_filter = (
        'is_active',
        'model_name'
    )
    
    search_fields = (
        'name', 
        'key', 
        'description',
        'system_prompt'
    )

    # Fieldsets or grouping (mocked structure)
    fieldsets = (
        ('Identification', {'fields': ('name', 'key', 'description')}),
        ('Prompts', {'fields': ('system_prompt', 'user_prompt_template')}),
        ('Configuration', {'fields': ('is_active', 'required_parameters', 'model_name')}),
    )


# --- 3. AIRateLimit Admin ---

class AIRateLimitAdmin(MockModelAdmin):
    """Admin interface for managing plan-based rate limits."""

    list_display = (
        'plan_type', 
        'daily_limit',
        'enforced'
    )
    
    list_editable = (
        'daily_limit',
        'enforced'
    )
    
    search_fields = ('plan_type',)
    
# --- Register models with the mock admin system ---

admin.register(AIUsage, AIUsageAdmin)
admin.register(AIPromptTemplate, AIPromptTemplateAdmin)
admin.register(AIRateLimit, AIRateLimitAdmin)