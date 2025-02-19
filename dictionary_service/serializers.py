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
        Дополнительно обновляет word_count словаря и инкрементально обновляет статистику прогресса словаря.
        """
        tag_names = validated_data.pop('tag_names', [])
        progress = validated_data.pop('progress', None)
        count = validated_data.pop('count', None)
        highlight_disabled = validated_data.pop('highlight_disabled', False)

        # Если прогресс не передан, устанавливаем его в 0.0
        if progress is None:
            progress = 0.0

        # Создаём слово
        word = Word.objects.create(**validated_data)

        # Обрабатываем теги
        tags = []
        for name in tag_names:
            tag, created = Tag.objects.get_or_create(name=name)
            tags.append(tag)
        word.tags.set(tags)

        # Создаём запись в UserWord с переданным или дефолтным прогрессом (0.0)
        UserWord.objects.create(
            word=word,
            count=count if count is not None else 0,
            progress=progress,
            highlight_disabled=highlight_disabled
        )

        # # Обновление word_count словаря в сигналах!
        dictionary = word.dictionary

        # Обновляем статистику словаря в DictionaryProgress
        if hasattr(dictionary, 'progress'):
            dictionary.progress.add_word(progress)

        return word

    def update(self, instance, validated_data):
        tag_names = validated_data.pop('tag_names', None)
        progress = validated_data.pop('progress', None)
        count = validated_data.pop('count', None)
        highlight_disabled = validated_data.pop('highlight_disabled', None)

        # Обновляем поля модели Word
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Обновляем теги, если они были переданы
        if tag_names is not None:
            tags = []
            for name in tag_names:
                tag, created = Tag.objects.get_or_create(name=name)
                tags.append(tag)
            instance.tags.set(tags)

        # Обновляем связанные данные в UserWord
        try:
            userword = instance.userword
        except UserWord.DoesNotExist:
            userword = UserWord.objects.create(word=instance)

        # Если обновляется прогресс, получаем старое значение
        if progress is not None:
            old_progress = userword.progress  # запоминаем старое значение прогресса
            if old_progress != progress:
                # Если слово меняет свою группу (метод update_word внутри DictionaryProgress проверит это)
                dictionary = instance.dictionary
                if hasattr(dictionary, 'progress'):
                    dictionary.progress.update_word(old_progress, progress)
            userword.progress = progress

        if count is not None:
            userword.count = count
        if highlight_disabled is not None:
            userword.highlight_disabled = highlight_disabled

        userword.save()
        return instance

    def to_representation(self, instance):
        """
        Добавляет поля `progress`, `count` и `highlight_disabled` из связанной модели UserWord в представление.
        """
        ret = super().to_representation(instance)
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


# Включает вложенное поле words, представляющее собой пагинированный список слов
class DictionaryDetailSerializer(serializers.ModelSerializer):
    """
    Сериализатор для детального представления словаря (Dictionary).
    Включает вложенное поле `words` – пагинированный список слов.
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
        """
        request = self.context.get('request')
        words = obj.words.all().order_by('-created_at')
        paginator = WordPagination()
        paginated_words = paginator.paginate_queryset(words, request)
        serializer = WordSerializer(paginated_words, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data).data


# Для выдачи word и progress
class WordProgressSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Word, предназначенный для выдачи слова и прогресса пользователя,
    а также флага highlight_disabled из связанной модели UserWord.
    """
    progress = serializers.FloatField(source='userword.progress', default=0.0)
    highlight_disabled = serializers.BooleanField(source='userword.highlight_disabled', default=False)

    class Meta:
        model = Word
        fields = ['id', 'word', 'progress', 'highlight_disabled']
