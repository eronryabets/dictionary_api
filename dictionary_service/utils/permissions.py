from rest_framework import permissions

from dictionary_service.models import Dictionary, Word


class IsOwner(permissions.BasePermission):
    """
    Разрешает доступ только владельцам объекта.
    """

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Dictionary):
            is_owner = str(obj.user_id) == str(request.user.id)
        elif isinstance(obj, Word):
            is_owner = str(obj.dictionary.user_id) == str(request.user.id)
        else:
            is_owner = False
        print(f"User ID: {request.user.id}, Object User ID: {obj.user_id}, Is Owner: {is_owner}")
        return is_owner
