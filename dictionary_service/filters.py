from django_filters import rest_framework as filters
from .models import Word, Tag


class WordFilter(filters.FilterSet):
    """
     Фильтр для модели `Word`, позволяющий фильтровать слова по словарю и тегам.

     Этот фильтр предоставляет возможность пользователям фильтровать слова на основе выбранного словаря и
     набора тегов. Использование `ModelMultipleChoiceFilter` с параметром `conjoined=True` позволяет
     искать только те слова, которые содержат **все** указанные теги.
     """
    # Фильтр по названиям тегов. Используем ModelMultipleChoiceFilter с to_field_name='name' и conjoined=True
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__name',  # Поле для фильтрации
        to_field_name='name',  # Фильтрация по названию тега
        queryset=Tag.objects.all(),  # Запрос для выборки тегов
        conjoined=True,  # Требует наличия всех указанных тегов у слова
        label='Tags'  # Метка для документации
    )

    class Meta:
        model = Word
        fields = ['dictionary', 'tags']
