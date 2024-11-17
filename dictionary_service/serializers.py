
from rest_framework import serializers
from .models import Dictionary, Word, Tag


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


class DictionarySerializer(serializers.ModelSerializer):
    words = WordSerializer(many=True, read_only=True)
    cover_image = serializers.ImageField(required=False, allow_null=True)
    word_count = serializers.IntegerField(read_only=True)  # Новое поле для счетчика слов

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

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user_id'] = user.id  # Устанавливаем user_id из текущего пользователя
        return super().create(validated_data)

    def validate_cover_image(self, value):
        if value and len(value.name) > 100:
            raise serializers.ValidationError("Имя файла слишком длинное.")
        return value
