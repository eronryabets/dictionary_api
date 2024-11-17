
from django.db import models
import uuid
import os
from django.core.exceptions import ValidationError
from PIL import Image


def validate_image_extension(value):
    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    if ext not in valid_extensions:
        raise ValidationError('Unsupported file extension.')


def dictionary_cover_upload_to(instance, filename):
    """
    Определяет путь для загрузки обложки словаря:
    media/users/user_id/dictionaries/dictionary_id/cover_filename.ext
    """
    ext = os.path.splitext(filename)[1].lower()
    filename = f"cover{ext}"  # Короткое имя файла
    return os.path.join(
        'users',
        str(instance.user_id),
        'dictionaries',
        str(instance.id),
        filename
    )


def word_image_upload_to(instance, filename):
    """
    Определяет путь для загрузки изображений слова:
    media/users/user_id/dictionaries/dictionary_id/words/uuid_filename.ext
    """
    unique_filename = f"{uuid.uuid4()}_{filename}"
    return os.path.join(
        'users',
        str(instance.dictionary.user_id),
        'dictionaries',
        str(instance.dictionary.id),
        'words',
        unique_filename
    )


class Dictionary(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField()  # Идентификатор пользователя из другого сервиса
    language = models.CharField(max_length=100)
    name = models.CharField(max_length=255, unique=True)  # Сделано уникальным
    cover_image = models.ImageField(
        upload_to=dictionary_cover_upload_to,
        blank=True,
        null=True,
        max_length=255,  # Увеличиваем длину пути
        validators=[validate_image_extension]
    )
    word_count = models.PositiveIntegerField(default=0)  # Новое поле для счетчика слов
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['language']),
        ]
        verbose_name = "Dictionary"
        verbose_name_plural = "Dictionaries"

    def clean(self):
        if self.word_count < 0:
            raise ValidationError({'word_count': "Word count cannot be negative."})

    def save(self, *args, **kwargs):
        self.clean()
        super(Dictionary, self).save(*args, **kwargs)
        if self.cover_image:
            try:
                img = Image.open(self.cover_image.path)
                if img.height > 300 or img.width > 300:
                    output_size = (300, 300)
                    img.thumbnail(output_size)
                    img.save(self.cover_image.path)
            except Exception as e:
                # Логирование или обработка ошибки
                print(f"Error processing image: {e}")

    def __str__(self):
        return f"Dictionary({self.language}, {self.name}, User: {self.user_id})"


class Tag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)  # Уникальное название тега
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Word(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dictionary = models.ForeignKey(Dictionary, on_delete=models.CASCADE, related_name='words')
    word = models.CharField(max_length=255)
    translation = models.CharField(max_length=255)
    image_path = models.ImageField(
        upload_to=word_image_upload_to,
        blank=True,
        null=True,
        max_length=255,  # Увеличиваем длину пути
        validators=[validate_image_extension]
    )
    tags = models.ManyToManyField(Tag, related_name='words', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['word']),
            models.Index(fields=['translation']),
        ]
        unique_together = ('dictionary', 'word')  # Предотвращает дублирование слов в одном словаре
        verbose_name = "Word"
        verbose_name_plural = "Words"

    def clean(self):
        if self.dictionary.word_count < 0:
            raise ValidationError({'dictionary': "Word count cannot be negative."})

    def save(self, *args, **kwargs):
        self.clean()
        super(Word, self).save(*args, **kwargs)
        if self.image_path:
            try:
                img = Image.open(self.image_path.path)
                if img.height > 300 or img.width > 300:
                    output_size = (300, 300)
                    img.thumbnail(output_size)
                    img.save(self.image_path.path)
            except Exception as e:
                # Логирование или обработка ошибки
                print(f"Error processing image: {e}")

    def __str__(self):
        return self.word


class UserWord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name='user_words')
    count = models.IntegerField(default=0)
    progress = models.FloatField(default=0.0)
    last_accessed = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('word',)
        indexes = [
            models.Index(fields=['word']),
        ]
        verbose_name = "User Word"
        verbose_name_plural = "User Words"

    def __str__(self):
        return f"UserWord({self.word.word})"

    @property
    def user_id(self):
        return self.word.dictionary.user_id
