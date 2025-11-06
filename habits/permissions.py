from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Пользователь может редактировать только свои привычки."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS and obj.is_public:
            return True
        return obj.user == request.user
