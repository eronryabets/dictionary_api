from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Dictionary, Word, Tag
from .pagination import DictionaryPagination, WordPagination
from .serializers import (
    DictionaryListSerializer,
    DictionaryDetailSerializer,
    WordSerializer,
    WordProgressSerializer,
    TagSerializer
)
from .utils.permissions import IsOwner
from django_filters.rest_framework import DjangoFilterBackend
from .filters import WordFilter


class DictionaryViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы со словарями (Dictionary).

    - Позволяет просматривать, создавать, редактировать и удалять словари.
    - Использует разные сериализаторы для списка и детального представления.
    - Применяет кастомные разрешения для обеспечения доступа только владельцам словарей.
    - Подключает пагинацию для списка словарей.

    Дополнительные действия:
        - `words_progress`: Возвращает все слова из выбранного словаря вместе с их значениями progress без пагинации.
    """
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_serializer_class(self):
        """
        Возвращает класс сериализатора в зависимости от действия.

        - Для действия 'list' используется DictionaryListSerializer.
        - Для всех остальных действий используется DictionaryDetailSerializer.

        :return: Класс сериализатора.
        """
        if self.action == 'list':
            return DictionaryListSerializer
        return DictionaryDetailSerializer

    def get_queryset(self):
        """
        Возвращает только словари текущего пользователя с предварительной выборкой связанных слов и их UserWord.

        :return: QuerySet словарей, принадлежащих текущему пользователю.
        """
        return (Dictionary.objects.filter(user_id=self.request.user.id)
                .order_by('-updated_at')  # Сортировка по updated_at убывающим порядком
                .prefetch_related('words__userword', 'words__tags'))

    def perform_create(self, serializer):
        """
        Устанавливает user_id на основе аутентифицированного пользователя при создании нового словаря.

        :param serializer: Сериализатор, содержащий данные для создания словаря.
        """
        serializer.save(user_id=self.request.user.id)

    # Устанавливаем пагинацию только для списка словарей
    pagination_class = DictionaryPagination

    # Для выдачи word, progress.
    @action(detail=True, methods=['get'], url_path='words_progress',
            permission_classes=[permissions.IsAuthenticated, IsOwner])
    def words_progress(self, request, pk=None):
        """
        Возвращает все слова из выбранного словаря вместе с их значениями progress без пагинации.

        URL: /dictionaries/<id>/words_progress/

        :param request: HTTP-запрос.
        :param pk: Идентификатор словаря.
        :return: Response объект с сериализованными данными слов и их прогрессом.
        """
        dictionary = self.get_object()
        words = dictionary.words.all().select_related('userword')
        serializer = WordProgressSerializer(words, many=True)
        return Response(serializer.data)


class WordViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы со словами (Word).

    - Позволяет просматривать, создавать, редактировать и удалять слова.
    - Использует WordSerializer для сериализации данных.
    - Применяет кастомные разрешения для обеспечения доступа только владельцам слов.
    - Подключает пагинацию, фильтрацию и поиск для списка слов.
    """
    serializer_class = WordSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = WordFilter  # кастомный фильтр
    search_fields = ['word', 'translation']
    ordering_fields = ['word', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Возвращает только слова, принадлежащие текущему пользователю.
        """
        return Word.objects.filter(dictionary__user_id=self.request.user.id).select_related('userword').prefetch_related('tags')

    def perform_create(self, serializer):
        """
        Автоматически устанавливает user_id через связанный словарь при создании нового слова.
        """
        serializer.save()


class TagViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с тегами (Tag).

    - Позволяет просматривать, создавать, редактировать и удалять теги.
    - Использует TagSerializer для сериализации данных.
    - Применяет стандартные разрешения для аутентифицированных пользователей.
    - Сортирует теги по алфавиту.
    """
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    permission_classes = [permissions.IsAuthenticated]
