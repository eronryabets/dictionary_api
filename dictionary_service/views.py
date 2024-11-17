from rest_framework import viewsets, permissions
from .models import Dictionary, Word, Tag
from .serializers import DictionarySerializer, WordSerializer, TagSerializer
from .utils.permissions import IsOwner


class DictionaryViewSet(viewsets.ModelViewSet):
    serializer_class = DictionarySerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]  # TODO IsOwner

    def get_queryset(self):
        # Возвращаем только словари, принадлежащие текущему пользователю
        return Dictionary.objects.filter(user_id=self.request.user.id)

    def perform_create(self, serializer):
        # Автоматически устанавливаем user_id при создании словаря
        serializer.save(user_id=self.request.user.id)


class WordViewSet(viewsets.ModelViewSet):
    serializer_class = WordSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]     # TODO IsOwner

    def get_queryset(self):
        # Возвращаем только слова, принадлежащие текущему пользователю
        return Word.objects.filter(dictionary__user_id=self.request.user.id)

    def perform_create(self, serializer):
        # Автоматически устанавливаем user_id через словарь
        serializer.save()


class TagViewSet(viewsets.ModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    permission_classes = [permissions.IsAuthenticated]
