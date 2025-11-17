from rest_framework import permissions

class IsProjectMember(permissions.BasePermission):
    """
    Allows access only to members of the project.
    Requires the view to have a 'project' instance available (e.g., self.get_object()).
    """
    message = 'You must be a member of this project to perform this action.'

    def has_permission(self, request, view):
        # Allow read-only access if the project is public, regardless of membership.
        # However, for project-level actions, we often need to check membership
        # or rely on object-level permission in has_object_permission.
        return True

    def has_object_permission(self, request, view, obj):
        # 'obj' will be a Project instance in most Project-related views.
        if request.user.is_superuser or request.user.is_staff:
            return True

        if request.method in permissions.SAFE_METHODS:
            # Allow SAFE_METHODS if the project is public or user is a member
            if obj.is_public:
                return True
            
            # Check for ProjectMember relationship
            return obj.is_member(request.user)

        # For write methods (POST, PUT, PATCH, DELETE), require membership
        return obj.is_member(request.user)


class IsProjectOwnerOrAdmin(permissions.BasePermission):
    """
    Allows access only to the owner or an admin of the project.
    This permission is typically used for managing project settings, members, or deletion.
    """
    message = 'You must be the project owner or an admin to perform this action.'

    def has_object_permission(self, request, view, obj):
        # 'obj' will be a Project instance.
        if request.user.is_superuser or request.user.is_staff:
            return True

        # Owners and Admins have full access
        return obj.is_admin(request.user)


class IsProjectLabelCreatorOrAdmin(permissions.BasePermission):
    """
    Allows access only to the label creator or a project admin/owner.
    Used for modifying or deleting specific labels.
    """
    message = 'You must be the label creator or a project admin to perform this action.'

    def has_object_permission(self, request, view, obj):
        # 'obj' will be a ProjectLabel instance.
        if request.user.is_superuser or request.user.is_staff:
            return True

        # Project owner/admin can manage all labels
        if obj.project.is_admin(request.user):
            return True
        
        # Label creator can manage their own labels
        return obj.created_by == request.user