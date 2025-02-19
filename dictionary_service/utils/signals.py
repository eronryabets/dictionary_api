from django.db import transaction
from django.db.models.signals import pre_save, post_delete, post_save, pre_delete
from django.dispatch import receiver
from dictionary_service.models import Dictionary, Word, DictionaryProgress
import os
from django.db.models import F
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Dictionary)
def delete_old_dictionary_cover(sender, instance, **kwargs):
    """
    Удаляет старую обложку книги перед сохранением новой обложки.

    Если объект Dictionary обновляется и новая cover_image отличается от старой,
    старая cover_image удаляется из файловой системы.
    """
    if not instance.pk:
        return False  # Новое объект, нечего удалять

    try:
        old_cover = Dictionary.objects.get(pk=instance.pk).cover_image
    except Dictionary.DoesNotExist:
        return False

    new_cover = instance.cover_image
    if old_cover and old_cover != new_cover:
        if os.path.isfile(old_cover.path):
            os.remove(old_cover.path)


@receiver(post_delete, sender=Dictionary)
def delete_dictionary_cover_on_delete(sender, instance, **kwargs):
    """
    Удаляет обложку книги при удалении объекта Dictionary.

    Если у удаляемого Dictionary есть cover_image, файл обложки удаляется из файловой системы.
    """
    if instance.cover_image and os.path.isfile(instance.cover_image.path):
        os.remove(instance.cover_image.path)


@receiver(pre_save, sender=Word)
def delete_old_word_image(sender, instance, **kwargs):
    """
    Удаляет старое изображение слова перед сохранением нового.

    Если объект Word обновляется и новое image_path отличается от старого,
    старое изображение удаляется из файловой системы.
    """
    if not instance.pk:
        return False  # Новое объект, нечего удалять

    try:
        old_image = Word.objects.get(pk=instance.pk).image_path
    except Word.DoesNotExist:
        return False

    new_image = instance.image_path
    if old_image and old_image != new_image:
        if os.path.isfile(old_image.path):
            os.remove(old_image.path)


@receiver(post_delete, sender=Word)
def delete_word_image_on_delete(sender, instance, **kwargs):
    """
    Удаляет изображение слова при удалении объекта Word.

    Если у удаляемого Word есть image_path, файл изображения удаляется из файловой системы.
    """
    if instance.image_path and os.path.isfile(instance.image_path.path):
        os.remove(instance.image_path.path)


# Новые сигналы для обновления word_count
@receiver(post_save, sender=Word)
def increment_word_count(sender, instance, created, **kwargs):
    """
    Увеличивает счетчик слов в Dictionary при добавлении нового Word.

    Если Word создается впервые, счетчик word_count в связанном Dictionary увеличивается на 1,
    а поле updated_at обновляется текущим временем.
    """
    if created:
        with transaction.atomic():
            Dictionary.objects.filter(id=instance.dictionary.id).update(
                word_count=F('word_count') + 1,
                updated_at=timezone.now()
            )
        logger.info(
            f"Word added to Dictionary {instance.dictionary.id}. Incremented word_count and updated updated_at.")


@receiver(post_delete, sender=Word)
def decrement_word_count(sender, instance, **kwargs):
    """
    Уменьшает счетчик слов в Dictionary при удалении Word.

    При удалении Word счетчик word_count в связанном Dictionary уменьшается на 1,
    поле updated_at обновляется текущим временем. Если word_count становится меньше 0,
    он сбрасывается в 0, и генерируется предупреждение.
    """
    with transaction.atomic():
        Dictionary.objects.filter(id=instance.dictionary.id).update(
            word_count=F('word_count') - 1,
            updated_at=timezone.now()
        )
        dictionary = Dictionary.objects.get(id=instance.dictionary.id)
        if dictionary.word_count < 0:
            dictionary.word_count = 0
            dictionary.save()
            logger.warning(f"word_count for Dictionary {dictionary.id} became negative. Reset to 0.")
        else:
            logger.info(
                f"Word removed from Dictionary {instance.dictionary.id}. Decremented word_count and updated updated_at.")


@receiver(post_save, sender=Dictionary)
def create_dictionary_progress(sender, instance, created, **kwargs):
    if created:
        # При создании нового словаря создаём запись прогресса.
        DictionaryProgress.objects.create(dictionary=instance)


@receiver(pre_delete, sender=Word)
def store_word_progress_before_deletion(sender, instance, **kwargs):
    """
    Сохраняет значение прогресса слова перед его удалением.
    Это нужно, так как связанная запись UserWord удаляется каскадом.
    """
    try:
        instance._progress_for_deletion = instance.userword.progress
    except Exception:
        instance._progress_for_deletion = 0.0


@receiver(post_delete, sender=Word)
def update_dictionary_progress_on_word_deletion(sender, instance, **kwargs):
    """
    Обновляет статистику словаря при удалении слова.
    Вычитает значение прогресса удаляемого слова из DictionaryProgress.
    """
    progress = getattr(instance, '_progress_for_deletion', 0.0)
    dictionary = instance.dictionary
    if hasattr(dictionary, 'progress'):
        dictionary.progress.remove_word(progress)
