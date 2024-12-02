from rest_framework import serializers
from .models import Dictionary, Word, Tag
from .pagination import WordPagination


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'created_at', 'updated_at']


class WordSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    tag_names = serializers.ListField(
        child=serializers.CharField(max_length=100),
        write_only=True,
        required=False  # Сделать поле необязательным
    )
    image_path = serializers.ImageField(required=False, allow_null=True)

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
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        tag_names = validated_data.pop('tag_names', [])
        word = Word.objects.create(**validated_data)
        tags = []
        for name in tag_names:
            tag, created = Tag.objects.get_or_create(name=name)
            tags.append(tag)
        word.tags.set(tags)
        return word

    def update(self, instance, validated_data):
        tag_names = validated_data.pop('tag_names', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tag_names is not None:
            tags = []
            for name in tag_names:
                tag, created = Tag.objects.get_or_create(name=name)
                tags.append(tag)
            instance.tags.set(tags)
        return instance

# Возвращает только основные поля словаря без вложенных слов
class DictionaryListSerializer(serializers.ModelSerializer):
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

    # Метод, который использует WordPagination для пагинации слов внутри словаря
    def get_words(self, obj):
        request = self.context.get('request')
        words = obj.words.all().order_by('created_at')  # Опционально: сортировка - TODO сделать под разные условия.
        paginator = WordPagination()
        paginated_words = paginator.paginate_queryset(words, request)
        serializer = WordSerializer(paginated_words, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data).data
