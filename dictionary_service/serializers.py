from rest_framework import serializers
from .models import Dictionary, Word, Tag, UserWord
from .pagination import WordPagination


class TagSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Tag. Возвращает идентификатор, название и временные метки создания и обновления тега.
    """

    class Meta:
        model = Tag
        fields = ['id', 'name', 'created_at', 'updated_at']


class WordSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Word.
    - Включает связанные теги через `TagSerializer`.
    - Позволяет добавлять теги по именам через поле `tag_names`.
    - Обрабатывает изображение слова и связанные данные из модели `UserWord` (count и progress).
    """
    tags = TagSerializer(many=True, read_only=True)
    tag_names = serializers.ListField(
        child=serializers.CharField(max_length=100),
        write_only=True,
        required=False
    )
    image_path = serializers.ImageField(required=False, allow_null=True)

    # Поля из UserWord
    count = serializers.IntegerField(required=False, write_only=True)
    progress = serializers.FloatField(required=False, write_only=True)
    highlight_disabled = serializers.BooleanField(
        required=False,
        write_only=True,
        default=False
    )

    class Meta:
        model = Word
        fields = [
            'id',
            'dictionary',
            'word',
            'translation',
            'image_path',
            'tags',
            'tag_names',
            'count',
            'progress',
            'highlight_disabled',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        """
        Создаёт новый объект Word вместе с связанными тегами и записью в UserWord.

        :param validated_data: Валидированные данные для создания Word.
        :return: Созданный экземпляр Word.
        """
        tag_names = validated_data.pop('tag_names', [])
        progress = validated_data.pop('progress', None)
        count = validated_data.pop('count', None)

        # Получаем флаг, если передали (либо False)
        highlight_disabled = validated_data.pop('highlight_disabled', False)

        word = Word.objects.create(**validated_data)
        tags = []
        for name in tag_names:
            tag, created = Tag.objects.get_or_create(name=name)
            tags.append(tag)
        word.tags.set(tags)

        # Создание записи в UserWord
        UserWord.objects.create(
            word=word,
            count=count if count is not None else 0,
            progress=progress if progress is not None else 0.0,
            highlight_disabled=highlight_disabled
        )

        return word

    def update(self, instance, validated_data):
        """
        Обновляет существующий объект Word вместе с тегами и связанными данными UserWord.

        :param instance: Экземпляр Word для обновления.
        :param validated_data: Валидированные данные для обновления.
        :return: Обновлённый экземпляр Word.
        """
        # Извлекаем значения
        tag_names = validated_data.pop('tag_names', None)
        progress = validated_data.pop('progress', None)
        count = validated_data.pop('count', None)
        # Получаем флаг, если передали
        highlight_disabled = validated_data.pop('highlight_disabled', None)

        # Сначала обновляем поля самой модели Word
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Обновляем теги, если они были предоставлены
        if tag_names is not None:
            tags = []
            for name in tag_names:
                tag, created = Tag.objects.get_or_create(name=name)
                tags.append(tag)
            instance.tags.set(tags)

        # --- ВАЖНО: теперь обновляем UserWord
        # Пытаемся получить связанную запись
        try:
            userword = instance.userword
        except UserWord.DoesNotExist:
            # Если её нет, создаём
            userword = UserWord.objects.create(word=instance)

        # Обновляем нужные поля, если они пришли
        if progress is not None:
            userword.progress = progress
        if count is not None:
            userword.count = count
        if highlight_disabled is not None:
            userword.highlight_disabled = highlight_disabled

        userword.save()
        return instance

    def to_representation(self, instance):
        """
        Добавляет поля `progress`,`count` и 'highlight_disabled' из связанной модели UserWord в представление.

        :param instance: Экземпляр Word.
        :return: Сериализованные данные с добавленными полями `progress`,`count` и 'highlight_disabled'.
        """
        ret = super().to_representation(instance)
        # Добавляем progress, count, highlight_disabled из userword
        if hasattr(instance, 'userword') and instance.userword:
            ret['progress'] = instance.userword.progress
            ret['count'] = instance.userword.count
            ret['highlight_disabled'] = instance.userword.highlight_disabled
        else:
            ret['progress'] = 0.0
            ret['count'] = 0
            ret['highlight_disabled'] = False
        return ret


# Возвращает только основные поля словаря без вложенных слов
class DictionaryListSerializer(serializers.ModelSerializer):
    """
    Сериализатор для списка словарей (Dictionary).
    Возвращает основные поля словаря без вложенных слов.
    """

    class Meta:
        model = Dictionary
        fields = [
            'id',
            'user_id',
            'language',
            'name',
            'cover_image',
            'word_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user_id', 'word_count', 'created_at', 'updated_at']


# Включает вложенное поле words, которое представляет собой пагинированный список слов
class DictionaryDetailSerializer(serializers.ModelSerializer):
    """
    Сериализатор для детального представления словаря (Dictionary).
    Включает вложенное поле `words`, представляющее собой пагинированный список слов.
    """
    words = serializers.SerializerMethodField()
    cover_image = serializers.ImageField(required=False, allow_null=True)
    word_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Dictionary
        fields = [
            'id',
            'user_id',
            'language',
            'name',
            'cover_image',
            'word_count',
            'words',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user_id', 'word_count', 'created_at', 'updated_at']

    def get_words(self, obj):
        """
        Получает пагинированный список слов, связанных с данным словарем.

        :param obj: Экземпляр Dictionary.
        :return: Сериализованные данные пагинированного списка слов.
        """
        request = self.context.get('request')
        words = obj.words.all().order_by('-created_at')  # Сортировка по убыванию даты создания
        paginator = WordPagination()
        paginated_words = paginator.paginate_queryset(words, request)
        serializer = WordSerializer(paginated_words, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data).data


# Для выдачи word и progress
class WordProgressSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Word, предназначенный для выдачи слова и прогресса пользователя.
    Включает поле `progress` из связанной модели UserWord.
    """
    progress = serializers.FloatField(source='userword.progress', default=0.0)

    class Meta:
        model = Word
        fields = ['word', 'progress', 'id']
