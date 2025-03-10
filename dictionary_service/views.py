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

from collections import defaultdict
from django.db import transaction
from django.utils import timezone
from rest_framework import status



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

    def update(self, request, *args, **kwargs):
        """
        Обновляет существующий словарь с помощью частичного или полного обновления.

        Этот метод предназначен для обновления данных словаря, принадлежащего текущему пользователю.
        Основные шаги метода:
          1. Извлекает параметр 'partial' из kwargs, чтобы определить, выполнять ли частичное обновление.
          2. Получает объект словаря напрямую (без prefetch_related) с использованием ID из URL и проверяет,
             что словарь принадлежит аутентифицированному пользователю.
          3. Инициализирует сериализатор с извлеченным объектом и входными данными из запроса.
          4. Валидирует данные с помощью serializer.is_valid(raise_exception=True).
          5. Обновляет словарь в базе данных с помощью метода update() для непосредственного применения изменений.
          6. Возвращает Response с сообщением об успешном обновлении и HTTP статусом 200.

        Параметры:
          request (HttpRequest): HTTP-запрос, содержащий данные обновления.
          *args: Дополнительные позиционные аргументы.
          **kwargs: Дополнительные именованные аргументы, включая 'partial' (True для частичного обновления).

        Возвращает:
          Response: Объект ответа с JSON-данными, например, {"detail": "Dictionary updated successfully."} и статусом 200.

        Исключения:
          Если данные не проходят валидацию, будет выброшено исключение, и клиент получит сообщение об ошибке.
        """
        partial = kwargs.pop('partial', False)
        # Получаем объект напрямую без prefetch_related:
        instance = Dictionary.objects.get(pk=kwargs['pk'], user_id=request.user.id)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        Dictionary.objects.filter(pk=instance.pk).update(**serializer.validated_data)
        # return Response(serializer.data) //Облегчили ответ - состояние локально обновляем на фронте при успехе.
        return Response({"detail": "Dictionary updated successfully."}, status=status.HTTP_200_OK)

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
            'max_progress',
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
        *.space/dictionaries/progress/bulk/
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
            'max_progress',
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
        qs = Word.objects.filter(dictionary__user_id=self.request.user.id).order_by('-created_at')
        # Для операций обновления не загружаем связанные объекты
        if self.action not in ['update', 'partial_update']:
            qs = qs.select_related('userword').prefetch_related('tags')
        return qs.annotate(
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
        action = request.data.get("action")
        word_ids = request.data.get("word_ids", [])

        if not word_ids or not isinstance(word_ids, list):
            return Response({"detail": "word_ids must be a non-empty list"}, status=status.HTTP_400_BAD_REQUEST)

        if action == "delete":
            with transaction.atomic():
                # Получаем QuerySet слов для удаления с нужными связями.
                words_qs = (
                    Word.objects.filter(pk__in=word_ids)
                    .select_related('dictionary', 'userword')
                )

                # Группируем слова по словарям.
                # Для каждого словаря накапливаем:
                # - delete_count: общее число удаляемых слов,
                # - progress_sum: сумма прогресса этих слов,
                # - groups: для каждой группы – количество удаляемых слов.
                updates = defaultdict(lambda: {"delete_count": 0, "progress_sum": 0.0, "groups": defaultdict(int)})
                for word in words_qs:
                    dict_id = word.dictionary_id
                    updates[dict_id]["delete_count"] += 1
                    try:
                        p = word.userword.progress
                    except Exception:
                        p = 0.0
                    updates[dict_id]["progress_sum"] += p
                    # Определяем группу слова с помощью метода _get_group из DictionaryProgress.
                    # Для этого получаем текущий объект DictionaryProgress (предполагается, что он уже создан)
                    dp = word.dictionary.progress
                    group = dp._get_group(p)
                    if group:
                        updates[dict_id]["groups"][group] += 1

                # Для каждого словаря обновляем статистику.
                for dict_id, data in updates.items():
                    delete_count = data["delete_count"]
                    progress_sum = data["progress_sum"]
                    groups_deleted = data["groups"]

                    # Обновляем word_count в Dictionary.
                    Dictionary.objects.filter(pk=dict_id).update(
                        word_count=F('word_count') - delete_count,
                        updated_at=timezone.now()
                    )

                    # Получаем текущий объект DictionaryProgress.
                    dp = DictionaryProgress.objects.get(dictionary_id=dict_id)
                    # Обновляем total_progress и max_progress.
                    new_total = dp.total_progress - progress_sum
                    new_max = dp.max_progress - (delete_count * 10)
                    # Обновляем групповые счетчики: вычитаем количество удаленных слов для каждой группы.
                    # Например, для группы "0_2":
                    dp.group_0_2 = max(0, dp.group_0_2 - groups_deleted.get('0_2', 0))
                    dp.group_3_4 = max(0, dp.group_3_4 - groups_deleted.get('3_4', 0))
                    dp.group_5_6 = max(0, dp.group_5_6 - groups_deleted.get('5_6', 0))
                    dp.group_7_8 = max(0, dp.group_7_8 - groups_deleted.get('7_8', 0))
                    dp.group_9_10 = max(0, dp.group_9_10 - groups_deleted.get('9_10', 0))

                    # Пересчитываем overall_progress
                    if new_max > 0:
                        new_overall = round((new_total / new_max) * 100, 3)
                    else:
                        new_overall = 0
                        new_total = 0

                    # Сохраняем обновления.
                    dp.total_progress = new_total
                    dp.max_progress = new_max
                    dp.overall_progress = new_overall
                    dp.save()

                # Теперь выполняем массовое удаление слов.
                Word.objects.filter(pk__in=word_ids).delete()

            return Response({"detail": f"Deleted {len(word_ids)} words."}, status=status.HTTP_200_OK)

        elif action == "disable_highlight":
            UserWord.objects.filter(word_id__in=word_ids).update(highlight_disabled=True)
            return Response({"detail": f"Disabled highlight for {len(word_ids)} words."}, status=status.HTTP_200_OK)

        elif action == "enable_highlight":
            UserWord.objects.filter(word_id__in=word_ids).update(highlight_disabled=False)
            return Response({"detail": f"Enabled highlight for {len(word_ids)} words."}, status=status.HTTP_200_OK)

        else:
            return Response({"detail": f"Unknown action: {action}"}, status=status.HTTP_400_BAD_REQUEST)
