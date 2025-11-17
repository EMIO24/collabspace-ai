"""
Project serializers for CollabSpace AI.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Project, ProjectMember, ProjectLabel, ProjectTemplate, ProjectActivity

User = get_user_model()


class ProjectMemberSerializer(serializers.ModelSerializer):
    """Serializer for project members."""
    
    user = serializers.SerializerMethodField()
    added_by_name = serializers.CharField(source='added_by.get_full_name', read_only=True)
    
    class Meta:
        model = ProjectMember
        fields = [
            'id', 'user', 'role', 'added_by_name', 'added_at', 'created_at'
        ]
        read_only_fields = ['id', 'added_at', 'created_at']
    
    def get_user(self, obj):
        """Get limited user information."""
        return {
            'id': str(obj.user.id),
            'email': obj.user.email,
            'username': obj.user.username,
            'full_name': obj.user.get_full_name(),
            'avatar': obj.user.avatar,
        }


class ProjectLabelSerializer(serializers.ModelSerializer):
    """Serializer for project labels."""
    
    task_count = serializers.IntegerField(read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = ProjectLabel
        fields = [
            'id', 'name', 'color', 'description', 'task_count',
            'created_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'task_count', 'created_at']
    
    def validate_color(self, value):
        """Validate color is hex format."""
        if not value.startswith('#') or len(value) != 7:
            raise serializers.ValidationError('Color must be a valid hex code (e.g., #FF5733)')
        return value


class ProjectListSerializer(serializers.ModelSerializer):
    """Serializer for project list view."""
    
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    workspace_name = serializers.CharField(source='workspace.name', read_only=True)
    member_count = serializers.IntegerField(read_only=True)
    task_count = serializers.IntegerField(read_only=True)
    completed_task_count = serializers.IntegerField(read_only=True)
    progress = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    user_role = serializers.SerializerMethodField()
    is_overdue = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'slug', 'description', 'workspace', 'workspace_name',
            'owner', 'owner_name', 'status', 'priority', 'color', 'icon',
            'start_date', 'end_date', 'is_public', 'member_count', 'task_count',
            'completed_task_count', 'progress', 'user_role', 'is_overdue',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'slug', 'member_count', 'task_count', 'completed_task_count',
            'progress', 'created_at', 'updated_at'
        ]
    
    def get_user_role(self, obj):
        """Get current user's role in project."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.get_member_role(request.user)
        return None


class ProjectDetailSerializer(serializers.ModelSerializer):
    """Serializer for project detail view."""
    
    owner = serializers.SerializerMethodField()
    workspace = serializers.SerializerMethodField()
    members = ProjectMemberSerializer(many=True, read_only=True)
    labels = ProjectLabelSerializer(many=True, read_only=True)
    statistics = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    user_permissions = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'slug', 'description', 'workspace', 'owner',
            'status', 'priority', 'color', 'icon', 'start_date', 'end_date',
            'is_public', 'settings', 'members', 'labels', 'statistics',
            'user_role', 'user_permissions', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']
    
    def get_owner(self, obj):
        """Get owner information."""
        return {
            'id': str(obj.owner.id),
            'email': obj.owner.email,
            'username': obj.owner.username,
            'full_name': obj.owner.get_full_name(),
            'avatar': obj.owner.avatar,
        }
    
    def get_workspace(self, obj):
        """Get workspace information."""
        return {
            'id': str(obj.workspace.id),
            'name': obj.workspace.name,
            'slug': obj.workspace.slug,
        }
    
    def get_statistics(self, obj):
        """Get project statistics."""
        return obj.get_statistics()
    
    def get_user_role(self, obj):
        """Get current user's role."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.get_member_role(request.user)
        return None
    
    def get_user_permissions(self, obj):
        """Get current user's permissions."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return {
                'can_edit': obj.is_admin(request.user),
                'can_delete': obj.is_owner(request.user),
                'can_manage_members': obj.is_admin(request.user),
                'can_create_tasks': obj.is_member(request.user),
            }
        return {}


class ProjectCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating projects."""
    
    template_id = serializers.UUIDField(required=False, write_only=True)
    
    class Meta:
        model = Project
        fields = [
            'name', 'description', 'workspace', 'status', 'priority',
            'color', 'icon', 'start_date', 'end_date', 'is_public',
            'settings', 'template_id'
        ]
    
    def validate_workspace(self, value):
        """Validate user has access to workspace."""
        request = self.context.get('request')
        if not value.is_member(request.user):
            raise serializers.ValidationError('You are not a member of this workspace')
        return value
    
    def validate(self, attrs):
        """Validate dates."""
        if attrs.get('start_date') and attrs.get('end_date'):
            if attrs['end_date'] < attrs['start_date']:
                raise serializers.ValidationError('End date must be after start date')
        return attrs
    
    def create(self, validated_data):
        """Create project with owner."""
        template_id = validated_data.pop('template_id', None)
        request = self.context.get('request')
        
        # Set owner to current user
        validated_data['owner'] = request.user
        
        # Create project
        project = Project.objects.create(**validated_data)
        
        # Add owner as project member
        project.add_member(request.user, role='owner')
        
        # Apply template if provided
        if template_id:
            try:
                template = ProjectTemplate.objects.get(id=template_id)
                template.apply_to_project(project)
            except ProjectTemplate.DoesNotExist:
                pass
        
        return project


class ProjectUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating projects."""
    
    class Meta:
        model = Project
        fields = [
            'name', 'description', 'status', 'priority', 'color', 'icon',
            'start_date', 'end_date', 'is_public', 'settings'
        ]
    
    def validate(self, attrs):
        """Validate dates."""
        instance = self.instance
        start_date = attrs.get('start_date', instance.start_date)
        end_date = attrs.get('end_date', instance.end_date)
        
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError('End date must be after start date')
        
        return attrs


class AddProjectMemberSerializer(serializers.Serializer):
    """Serializer for adding members to project."""
    
    user_id = serializers.UUIDField(required=True)
    role = serializers.ChoiceField(
        choices=['admin', 'member'],
        default='member'
    )
    
    def validate_user_id(self, value):
        """Validate user exists."""
        try:
            user = User.objects.get(id=value)
            return user
        except User.DoesNotExist:
            raise serializers.ValidationError('User not found')


class ProjectStatsSerializer(serializers.Serializer):
    """Serializer for project statistics."""
    
    total_tasks = serializers.IntegerField()
    completed_tasks = serializers.IntegerField()
    pending_tasks = serializers.IntegerField()
    progress_percentage = serializers.FloatField()
    total_members = serializers.IntegerField()
    status = serializers.CharField()
    priority = serializers.CharField()
    days_active = serializers.IntegerField()
    is_overdue = serializers.BooleanField()


class ProjectActivitySerializer(serializers.ModelSerializer):
    """Serializer for project activities."""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_avatar = serializers.URLField(source='user.avatar', read_only=True)
    
    class Meta:
        model = ProjectActivity
        fields = [
            'id', 'action', 'description', 'user_name', 'user_avatar',
            'metadata', 'created_at'
        ]
        read_only_fields = fields


class ProjectTemplateSerializer(serializers.ModelSerializer):
    """Serializer for project templates."""
    
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = ProjectTemplate
        fields = [
            'id', 'name', 'description', 'workspace', 'template_data',
            'is_public', 'use_count', 'created_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'use_count', 'created_at']

