# views.py
from rest_framework import viewsets, permissions
from .models import Dictionary, Word, Tag
from .serializers import DictionarySerializer, WordSerializer, TagSerializer


class IsOwner(permissions.BasePermission):
    """
    Разрешение, позволяющее доступ только владельцу объекта.
    """

    def has_object_permission(self, request, view, obj):
        return obj.user_id == request.user.id


class DictionaryViewSet(viewsets.ModelViewSet):
    """
    Вьюсет для управления словарями.
    """
    serializer_class = DictionarySerializer
    permission_classes = [permissions.IsAuthenticated]  # IsOwner

    def get_queryset(self):
        return Dictionary.objects.filter(user_id=self.request.user.id)

    def perform_create(self, serializer):
        serializer.save(user_id=self.request.user.id)


class WordViewSet(viewsets.ModelViewSet):
    """
    Вьюсет для управления словами.
    """
    serializer_class = WordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Word.objects.filter(dictionary__user_id=self.request.user.id)

    def perform_create(self, serializer):
        dictionary = serializer.validated_data.get('dictionary')
        # if dictionary.user_id != self.request.user.id:    #TODO
        #     raise permissions.PermissionDenied("Вы не можете добавлять слова в этот словарь.")
        serializer.save()


class TagViewSet(viewsets.ModelViewSet):
    """
    Вьюсет для управления тегами.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticated]
