from rest_framework import viewsets, permissions
from .models import Dictionary, Word, Tag
from .pagination import DictionaryPagination
from .serializers import DictionaryListSerializer, DictionaryDetailSerializer, WordSerializer, TagSerializer
from .utils.permissions import IsOwner


class DictionaryViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_serializer_class(self):
        if self.action == 'list':
            return DictionaryListSerializer
        return DictionaryDetailSerializer

    def get_queryset(self):
        # Возвращаем только словари текущего пользователя с предварительной выборкой связанных слов и их UserWord
        return (Dictionary.objects.filter(user_id=self.request.user.id)
                .prefetch_related('words__userword', 'words__tags'))

    # Устанавливаем пагинацию только для списка словарей
    pagination_class = DictionaryPagination


class WordViewSet(viewsets.ModelViewSet):
    serializer_class = WordSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        # Возвращаем только слова, принадлежащие текущему пользователю
        return Word.objects.filter(dictionary__user_id=self.request.user.id).select_related('userword')

    def perform_create(self, serializer):
        # Автоматически устанавливаем user_id через словарь
        serializer.save()


class TagViewSet(viewsets.ModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    permission_classes = [permissions.IsAuthenticated]