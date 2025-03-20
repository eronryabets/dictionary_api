from django_filters import rest_framework as filters
from .models import Word, Tag


class PartialTagFilter(filters.Filter):
    """
    Фильтр для частичного поиска по тегам.

    Этот фильтр извлекает все значения параметра 'tags' из данных запроса и применяет фильтрацию к QuerySet.
    Он проверяет наличие непустых значений в параметрах, а затем для каждого тега выполняет фильтрацию по подстроке
    (case-insensitive) в поле tags__name.

    Как работает:
    1. Извлекается список значений параметра 'tags' с помощью self.parent.data.getlist('tags').
    2. Если список пуст или все значения состоят только из пробелов, фильтрация не применяется и возвращается
    исходный QuerySet.
    3. Для каждого переданного тега:
       - Значение очищается от лишних пробелов.
       - QuerySet фильтруется с использованием метода filter(tags__name__icontains=tag),
         что позволяет найти объекты, у которых имя тега содержит данное значение (без учёта регистра).
    4. Итоговый отфильтрованный QuerySet возвращается.

    Пример использования:
      Если в URL присутствует параметр tags, например:
        ?tags=python,redux
      Фильтр выполнит последовательное применение:
        qs = qs.filter(tags__name__icontains='python').filter(tags__name__icontains='redux')
    """

    def filter(self, qs, value):
        # Получаем список всех значений параметра 'tags' из запроса
        raw_tags = self.parent.data.getlist('tags')
        # Если параметр отсутствует или состоит только из пустых значений – фильтр не применяется
        if not raw_tags or all(not t.strip() for t in raw_tags):
            return qs
        # Для каждого переданного значения применяем фильтрацию по подстроке
        for tag in raw_tags:
            tag = tag.strip()
            qs = qs.filter(tags__name__icontains=tag)
        return qs


class WordFilter(filters.FilterSet):
    """
    Фильтр для модели Word.

    Позволяет фильтровать объекты Word по различным критериям, включая теги, прогресс, количество (просмотры) и дату создания.
    """

    # Используем наш кастомный фильтр для тегов
    tags = PartialTagFilter()

    # # Фильтр по названиям тегов
    # tags = filters.ModelMultipleChoiceFilter(
    #     field_name='tags__name',  # Поле модели Word, по которому происходит фильтрация
    #     to_field_name='name',  # Поле модели Tag, по которому осуществляется сопоставление
    #     queryset=Tag.objects.all(),  # Набор данных для фильтрации
    #     conjoined=True,  # Требует наличие всех указанных тегов (логическое И)
    #     label='Tags'  # Читаемое название фильтра
    # )

    # Фильтры по прогрессу пользователя в словах
    progress_min = filters.NumberFilter(
        field_name='userword__progress',  # Поле модели UserWord, связанное с прогрессом
        lookup_expr='gte',  # Оператор фильтрации: больше или равно
        label='Progress (Min)'  # Читаемое название фильтра
    )
    progress_max = filters.NumberFilter(
        field_name='userword__progress',
        lookup_expr='lte',  # Оператор фильтрации: меньше или равно
        label='Progress (Max)'
    )

    # Фильтры по количеству повторений слова пользователем
    count_min = filters.NumberFilter(
        field_name='userword__count',  # Поле модели UserWord, связанное с количеством
        lookup_expr='gte',
        label='Count (Min)'
    )
    count_max = filters.NumberFilter(
        field_name='userword__count',
        lookup_expr='lte',
        label='Count (Max)'
    )

    # Фильтры по дате добавления слова
    created_at_after = filters.DateTimeFilter(
        field_name='created_at',  # Поле модели Word, связанное с датой создания
        lookup_expr='gte',  # Оператор фильтрации: после или равно
        label='Created At (After)'
    )
    created_at_before = filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte',  # Оператор фильтрации: до или равно
        label='Created At (Before)'
    )

    class Meta:
        model = Word
        fields = [
            'dictionary',  # Фильтр по словарю, к которому принадлежит слово
            'tags',  # Фильтр по тегам
            'progress_min',  # Минимальный прогресс
            'progress_max',  # Максимальный прогресс
            'count_min',  # Минимальное количество повторений
            'count_max',  # Максимальное количество повторений
            'created_at_after',  # Дата создания после
            'created_at_before',  # Дата создания до
        ]
