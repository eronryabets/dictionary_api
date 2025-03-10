from django.db import models, transaction
import uuid
import os
from django.core.exceptions import ValidationError
from PIL import Image
from django.db.models import F
from django.utils import timezone


def validate_image_extension(value):
    """
    Валидирует расширение загружаемого изображения.

    Допустимые расширения: .jpg, .jpeg, .png, .gif.

    :param value: Загружаемый файл изображения
    :raises ValidationError: Если расширение файла не поддерживается
    """
    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    if ext not in valid_extensions:
        raise ValidationError('Unsupported file extension.')


def dictionary_cover_upload_to(instance, filename):
    """
    Определяет путь для загрузки обложки словаря:
    media/users/user_id/dictionaries/dictionary_id/cover_filename.ext

    :param instance: Экземпляр модели Dictionary
    :param filename: Имя загружаемого файла
    :return: Путь для сохранения файла
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

    :param instance: Экземпляр модели Word
    :param filename: Имя загружаемого файла
    :return: Путь для сохранения файла
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
    """
    Модель словаря, содержащая основную информацию и связанные слова.

    Поля:
        - id (UUID): Уникальный идентификатор словаря.
        - user_id (UUID): Идентификатор пользователя, владельца словаря.
        - language (str): Язык словаря.
        - name (str): Уникальное название словаря.
        - cover_image (ImageField): Обложка словаря.
        - word_count (PositiveIntegerField): Счетчик слов в словаре.
        - created_at (DateTimeField): Дата и время создания.
        - updated_at (DateTimeField): Дата и время последнего обновления.

    Методы:
        - clean(): Проверяет, что word_count не отрицательный.
        - save(*args, **kwargs): Переопределённый метод сохранения с обработкой изображения.
        - __str__(): Возвращает строковое представление словаря.
    """
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
    """
    Модель тега для классификации слов.

    Поля:
        - id (UUID): Уникальный идентификатор тега.
        - name (str): Уникальное название тега.
        - created_at (DateTimeField): Дата и время создания.
        - updated_at (DateTimeField): Дата и время последнего обновления.
        - Сортировка выдачи тегов от самых новых - к самым старым.

    Методы:
        - __str__(): Возвращает название тега.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)  # Уникальное название тега
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']  # Теги будут сортироваться от самых новых к самым старым
        verbose_name = "Tag"
        verbose_name_plural = "Tags"

    def __str__(self):
        return self.name


class Word(models.Model):
    """
    Модель слова, входящего в словарь.

    Поля:
        - id (UUID): Уникальный идентификатор слова.
        - dictionary (ForeignKey): Ссылка на связанный Dictionary.
        - word (str): Само слово.
        - translation (str): Перевод слова.
        - image_path (ImageField): Изображение, связанное со словом.
        - tags (ManyToManyField): Связанные теги.
        - created_at (DateTimeField): Дата и время создания.
        - updated_at (DateTimeField): Дата и время последнего обновления.

    Методы:
        - clean(): Проверяет, что word_count словаря не отрицательный.
        - save(*args, **kwargs): Переопределённый метод сохранения с обработкой изображения.
        - __str__(): Возвращает само слово.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dictionary = models.ForeignKey(Dictionary, on_delete=models.CASCADE, related_name='words')
    word = models.CharField(max_length=500)
    translation = models.CharField(max_length=500)
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
        """
         Переопределённый метод save модели Word для выполнения предварительной валидации,
         последующей обработки изображения и обновления счетчика слов в связанном словаре.

         Основные шаги метода:
         1. Определяется, создаётся ли объект впервые (is_new) с помощью self._state.adding.
         2. Вызывается метод clean() для валидации данных модели перед сохранением.
         3. Вызывается родительский метод save() для сохранения объекта в базе данных.
         4. Если атрибут image_path задан:
            - Открывается изображение по пути self.image_path.path с использованием PIL.Image.
            - Если высота или ширина изображения превышают 300 пикселей, изображение масштабируется
              с сохранением пропорций до размеров, не превышающих 300x300 пикселей (используется метод thumbnail()).
            - Обновлённое изображение сохраняется обратно по тому же пути.
            - В случае возникновения исключения при обработке изображения, ошибка логируется в консоль.
         5. Если объект создаётся впервые (is_new):
            - Выполняется обновление поля word_count в связанном объекте Dictionary,
              увеличивая его на 1, и обновляется поле updated_at текущим временем.

         :param args: Дополнительные позиционные аргументы.
         :param kwargs: Дополнительные именованные аргументы.
         """
        is_new = self._state.adding  # True, если объект создаётся впервые
        self.clean()
        super(Word, self).save(*args, **kwargs)
        # Обработка изображения, если оно задано:
        if self.image_path:
            try:
                img = Image.open(self.image_path.path)
                if img.height > 300 or img.width > 300:
                    output_size = (300, 300)
                    img.thumbnail(output_size)
                    img.save(self.image_path.path)
            except Exception as e:
                print(f"Error processing image: {e}")
        # Если объект новый, обновляем word_count в связанном словаре
        if is_new:
            self.dictionary.__class__.objects.filter(pk=self.dictionary.id).update(
                word_count=F('word_count') + 1,
                updated_at=timezone.now()
            )

    def delete(self, *args, **kwargs):
        """
        Удаляет слово и обновляет связанные статистические данные:
          - Уменьшает total_progress на значение прогресса слова.
          - Уменьшает max_progress на 10 (так как каждое слово вносит +10 в max_progress).
          - Уменьшает соответствующий счётчик группы (например, group_0_2) на 1.
          - Пересчитывает overall_progress.
          - Уменьшает word_count в связанном Dictionary на 1.
        Все обновления выполняются в атомарной транзакции.
        """
        from django.db import transaction
        with transaction.atomic():
            # Получаем значение прогресса удаляемого слова (из связанной модели UserWord)
            try:
                progress_value = self.userword.progress
            except Exception:
                progress_value = 0.0

            # Обновляем DictionaryProgress: уменьшаем total_progress и max_progress через F() выражения
            DictionaryProgress.objects.filter(dictionary=self.dictionary).update(
                total_progress=F('total_progress') - progress_value,
                max_progress=F('max_progress') - 10
            )

            # Получаем объект DictionaryProgress (обновлённый в БД)
            dp = self.dictionary.progress
            # Обновляем счётчик группы для удаляемого слова
            dp._adjust_group_counter(progress_value, -1)
            # Пересчитываем overall_progress на основе обновлённых total_progress и max_progress
            if dp.max_progress > 0:
                new_overall = round((dp.total_progress / dp.max_progress) * 100, 3)
            else:
                new_overall = 0
                dp.total_progress = 0
            dp.overall_progress = new_overall
            dp.save()

            # Обновляем word_count в связанном Dictionary
            Dictionary.objects.filter(pk=self.dictionary.id).update(
                word_count=F('word_count') - 1,
                updated_at=timezone.now()
            )

            # Вызываем стандартное удаление слова
            super().delete(*args, **kwargs)

    def __str__(self):
        return self.word


class UserWord(models.Model):
    """
    Модель, связывающая пользователя и слово для отслеживания прогресса.

    Поля:
        - id (UUID): Уникальный идентификатор записи.
        - word (OneToOneField): Ссылка на связанный Word.
        - count (IntegerField): Количество раз, когда пользователь взаимодействовал со словом.
        - progress (FloatField): Прогресс пользователя в изучении слова.
        - highlight_disabled (BooleanField): По умолчанию подсветка слова Включена.
        - last_accessed (DateTimeField): Дата и время последнего доступа.
        - created_at (DateTimeField): Дата и время создания.
        - updated_at (DateTimeField): Дата и время последнего обновления.

    Методы:
        - __str__(): Возвращает строковое представление UserWord.
        - user_id (property): Возвращает идентификатор пользователя из связанного Dictionary.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    word = models.OneToOneField(Word, on_delete=models.CASCADE, related_name='userword')
    count = models.IntegerField(default=0)
    progress = models.FloatField(default=0.0)
    highlight_disabled = models.BooleanField(default=False)
    last_accessed = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
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


class DictionaryProgress(models.Model):
    """
    Модель для хранения статистики прогресса словаря.
    Статистика обновляется инкрементально, без перебора всех слов.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dictionary = models.OneToOneField(
        'dictionary_service.Dictionary',
        on_delete=models.CASCADE,
        related_name='progress'
    )
    # Суммарный прогресс всех слов (на шкале от 0 до 10)
    total_progress = models.FloatField(default=0.0, help_text="Суммарный прогресс всех слов (0–10)")
    # Общий прогресс словаря в процентах (вычисляется как (total_progress / word_count) * 10)
    overall_progress = models.FloatField(default=0.0, help_text="Общий прогресс словаря в %")
    # Новый столбец: максимальный возможный прогресс, равен количеству слов * 10
    max_progress = models.FloatField(default=0.0, help_text="Максимальный возможный прогресс (word_count * 10)")
    # Группы слов по диапазонам прогресса
    group_0_2 = models.PositiveIntegerField(default=0, help_text="Слова с прогрессом 0–2")
    group_3_4 = models.PositiveIntegerField(default=0, help_text="Слова с прогрессом 3–4")
    group_5_6 = models.PositiveIntegerField(default=0, help_text="Слова с прогрессом 5–6")
    group_7_8 = models.PositiveIntegerField(default=0, help_text="Слова с прогрессом 7–8")
    group_9_10 = models.PositiveIntegerField(default=0, help_text="Слова с прогрессом 9–10")

    def __str__(self):
        return f"Прогресс словаря '{self.dictionary.name}': {self.overall_progress}%"

    def _get_group(self, progress):
        """
        Определяет группу для заданного прогресса.
        Возвращает строку с идентификатором группы.
        """
        if 0 <= progress <= 2:
            return '0_2'
        elif 3 <= progress <= 4:
            return '3_4'
        elif 5 <= progress <= 6:
            return '5_6'
        elif 7 <= progress <= 8:
            return '7_8'
        elif 9 <= progress <= 10:
            return '9_10'
        else:
            return None

    def _compute_overall_progress(self):
        """
        Вычисляет общий прогресс словаря в процентах на основе total_progress и max_progress.
        Если max_progress <= 0, возвращает 0.
        Результат округляется до трех знаков после запятой.
        """
        if self.max_progress <= 0:
            return 0
        return round((self.total_progress / self.max_progress) * 100, 3)

    def _adjust_group_counter(self, progress, delta):
        """
        Универсально изменяет счётчик группы.
        :param progress: Значение прогресса слова.
        :param delta: Изменение (например, +1 или -1).
        """
        group = self._get_group(progress)
        if group == '0_2':
            self.group_0_2 = max(0, self.group_0_2 + delta)
        elif group == '3_4':
            self.group_3_4 = max(0, self.group_3_4 + delta)
        elif group == '5_6':
            self.group_5_6 = max(0, self.group_5_6 + delta)
        elif group == '7_8':
            self.group_7_8 = max(0, self.group_7_8 + delta)
        elif group == '9_10':
            self.group_9_10 = max(0, self.group_9_10 + delta)

    def add_word(self, progress):
        """
        Обновляет статистику при добавлении нового слова.
        :param progress: Прогресс нового слова (от 0 до 10)
        """
        # При добавлении нового слова число слов должно быть увеличено на 1,
        # так как сигнал increment_word_count обновит dictionary.word_count позже.
        new_total_words = self.dictionary.word_count + 1

        # Обновляем суммарный прогресс
        self.total_progress += progress

        # Обновляем счетчик группы для нового слова
        self._adjust_group_counter(progress, 1)

        # Обновляем максимальный возможный прогресс (+10 для нового слова)
        self.max_progress += 10

        # Пересчитываем общий прогресс, используя max_progress
        self.overall_progress = self._compute_overall_progress()
        self.save()

    def remove_word(self, progress):
        """
        Обновляет статистику словаря при удалении слова.
        Вычитает значение прогресса удаляемого слова из total_progress,
        уменьшает счетчик соответствующей группы, уменьшает max_progress на 10 и пересчитывает общий прогресс.
        При этом учитывается, что на момент вызова значение dictionary.word_count ещё не обновлено,
        поэтому фактическое число оставшихся слов определяется через max_progress.
        """
        self.total_progress -= progress
        # Уменьшаем счетчик группы для удаляемого слова:
        self._adjust_group_counter(progress, -1)
        # Уменьшаем максимальный возможный прогресс на 10:
        self.max_progress -= 10
        # Если max_progress стал 0 или меньше, сбрасываем total_progress и overall_progress:
        if self.max_progress <= 0:
            self.overall_progress = 0
            self.total_progress = 0
        else:
            self.overall_progress = self._compute_overall_progress()
        self.save()

    def update_word(self, old_progress, new_progress):
        """
        Обновляет статистику при изменении прогресса слова.
        Всегда пересчитывает общий прогресс и обновляет счетчики групп.

        :param old_progress: Предыдущее значение прогресса слова.
        :param new_progress: Новое значение прогресса слова.
        """
        # Корректируем суммарный прогресс:
        self.total_progress = self.total_progress - old_progress + new_progress
        # Обновляем счетчики групп: уменьшаем для старого значения, затем увеличиваем для нового:
        self._adjust_group_counter(old_progress, -1)
        self._adjust_group_counter(new_progress, 1)
        # Пересчитываем общий прогресс:
        self.overall_progress = self._compute_overall_progress()
        self.save()
