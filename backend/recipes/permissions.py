from rest_framework import permissions


class IsAuthorOrAdmin(permissions.BasePermission):
    """Разрешения изменений для авторов и админов"""
    def has_object_permission(self, request, view, obj):
        if request.user.is_authenticated:
            if (request.user.is_admin
               or obj.author == request.user):
                return True
        return request.method in permissions.SAFE_METHODS
