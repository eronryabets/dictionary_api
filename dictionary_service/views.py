from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Dictionary, Word, Tag, UserWord, DictionaryProgress
from .pagination import DictionaryPagination, WordPagination
from .serializers import (
    DictionaryListSerializer,
    DictionaryDetailSerializer,
    WordSerializer,
    WordProgressSerializer,
    TagSerializer, DictionaryProgressSerializer
)
from .utils.permissions import IsOwner
from django_filters.rest_framework import DjangoFilterBackend
from .filters import WordFilter
from django.db.models import F


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

    @action(detail=True, methods=['get'], url_path='progress',
            permission_classes=[permissions.IsAuthenticated, IsOwner])
    def progress(self, request, pk=None):
        """
        Возвращает статистику прогресса для выбранного словаря.
        URL: /dictionaries/<id>/progress/
        Выполняет ОДИН SQL-запрос, исключая ненужные предзагрузки связанных объектов.
        """
        progress_data = DictionaryProgress.objects.filter(dictionary_id=pk).values(
            'dictionary_id',
            'total_progress',
            'overall_progress',
            'group_0_2',
            'group_3_4',
            'group_5_6',
            'group_7_8',
            'group_9_10'
        ).first()

        if not progress_data:
            return Response({"detail": "Dictionary progress not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(progress_data)


class BulkDictionaryProgressView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        *.space/dictionary_progress/bulk/
        Принимает JSON вида:
        {
          "dictionary_ids": ["id1", "id2", ...]
        }
        Возвращает массив с данными прогресса для каждого словаря.
        """
        dictionary_ids = request.data.get("dictionary_ids", [])
        if not dictionary_ids or not isinstance(dictionary_ids, list):
            return Response(
                {"detail": "dictionary_ids must be a non-empty list"},
                status=status.HTTP_400_BAD_REQUEST
            )

        progress_data = DictionaryProgress.objects.filter(dictionary_id__in=dictionary_ids).values(
            'dictionary_id',
            'total_progress',
            'overall_progress',
            'group_0_2',
            'group_3_4',
            'group_5_6',
            'group_7_8',
            'group_9_10'
        )
        return Response(list(progress_data), status=status.HTTP_200_OK)


class WordViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы со словами (Word).

    - Позволяет просматривать, создавать, редактировать и удалять слова.
    - Использует WordSerializer для сериализации данных.
    - Применяет кастомные разрешения для обеспечения доступа только владельцам слов.
    - Подключает Пагинацию (в сериалайзере), Фильтрацию и Поиск для списка слов.
    - Поддерживает сортировку по `count`, `progress` и `created_at`.
    """
    serializer_class = WordSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = WordFilter  # Фильтр
    search_fields = ['word', 'translation']  # Поиск по слову, или его переводу
    ordering_fields = ['word', 'created_at', 'count', 'progress']
    ordering = ['-created_at']  # Дефолтная сортировка
    pagination_class = WordPagination  # Устанавливаем класс пагинации

    def get_queryset(self):
        """
        Возвращает только слова, принадлежащие текущему пользователю.
        Аннотирует `count` и `progress` для возможности сортировки по этим полям.
        """
        return Word.objects.filter(dictionary__user_id=self.request.user.id) \
            .select_related('userword') \
            .prefetch_related('tags') \
            .annotate(
            count=F('userword__count'),
            progress=F('userword__progress')
        )

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


class BulkWordActionView(APIView):
    """
    APIView для массовых действий со словами.

    Поддерживает следующие действия:
      - "delete": Массовое удаление слов.
      - "disable_highlight": Выключает подсветку для выбранных слов.
      - "enable_highlight": Включает подсветку для выбранных слов.
    """

    def post(self, request, *args, **kwargs):
        """
               Обрабатывает POST-запрос для выполнения массового действия над словами.

               Ожидает:
                 - action: строка с действием ("delete", "disable_highlight", "enable_highlight").
                 - word_ids: непустой список идентификаторов слов.
               принимает JSON вида:
                            {
                              "action": "delete", //или "disable_highlight" или "enable_highlight",
                              "word_ids": ["uuid1", "uuid2", ...]
                            }
               Возвращает сообщение об успешном выполнении действия или ошибку при неправильных данных.
        """
        action = request.data.get("action")
        word_ids = request.data.get("word_ids", [])

        if not word_ids or not isinstance(word_ids, list):
            return Response({"detail": "word_ids must be a non-empty list"}, status=status.HTTP_400_BAD_REQUEST)

        if action == "delete":
            # Массовое удаление
            Word.objects.filter(pk__in=word_ids).delete()
            return Response({"detail": f"Deleted {len(word_ids)} words."}, status=status.HTTP_200_OK)

        elif action == "disable_highlight":
            # Выставляем highlight_disabled = True для всех
            UserWord.objects.filter(word_id__in=word_ids).update(highlight_disabled=True)
            return Response({"detail": f"Disabled highlight for {len(word_ids)} words."}, status=status.HTTP_200_OK)

        elif action == "enable_highlight":
            # Выставляем highlight_disabled = False
            UserWord.objects.filter(word_id__in=word_ids).update(highlight_disabled=False)
            return Response({"detail": f"Enabled highlight for {len(word_ids)} words."}, status=status.HTTP_200_OK)

        else:
            return Response({"detail": f"Unknown action: {action}"}, status=status.HTTP_400_BAD_REQUEST)
