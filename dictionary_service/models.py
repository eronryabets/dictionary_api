from django.db import models
import uuid


class Dictionary(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField()  # Идентификатор пользователя из другого сервиса
    language = models.CharField(max_length=100)
    name = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['language']),
        ]

    def __str__(self):
        return f"Dictionary({self.language}, User: {self.user_id})"


class Tag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Word(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dictionary = models.ForeignKey(Dictionary, on_delete=models.CASCADE, related_name='words')
    word = models.CharField(max_length=255)
    translation = models.CharField(max_length=255)
    image_path = models.CharField(max_length=500, blank=True, null=True)  # Или ImageField
    tags = models.ManyToManyField(Tag, related_name='words', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['word']),
            models.Index(fields=['translation']),
        ]
        unique_together = ('dictionary', 'word')  # Предотвращает дублирование слов в одном словаре

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

    def __str__(self):
        return f"UserWord({self.word.word})"

    @property
    def user_id(self):
        return self.word.dictionary.user_id
