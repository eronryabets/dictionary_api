
from dictionary_service.models import Dictionary, Word

from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Разрешает доступ только владельцам объекта.

    Проверяет, что текущий пользователь является владельцем объекта.
    Поддерживаются модели Dictionary и Word.
    """

    def has_object_permission(self, request, view, obj):
        """
        Проверяет, является ли текущий пользователь владельцем объекта.
        Поддерживаются объекты моделей Dictionary и Word.

        :param request: HTTP-запрос, содержащий информацию о пользователе
        :param view: Текущий view
        :param obj: Объект, для которого проверяется разрешение
        :return: True, если пользователь является владельцем объекта, иначе False
        """
        if isinstance(obj, Dictionary):
            is_owner = str(obj.user_id) == str(request.user.id)
        elif isinstance(obj, Word):
            # Получаем user_id через связанный Dictionary
            is_owner = str(obj.dictionary.user_id) == str(request.user.id)
        else:
            is_owner = False
        print(f"User ID: {request.user.id}, Object User ID:"
              f" {obj.user_id if isinstance(obj, Dictionary) else obj.dictionary.user_id}, Is Owner: {is_owner}")
        return is_owner
