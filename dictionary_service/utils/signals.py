
from django.db.models.signals import pre_save, post_delete, post_save
from django.dispatch import receiver
from dictionary_service.models import Dictionary, Word
import os
from django.db.models import F
import logging

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Dictionary)
def delete_old_dictionary_cover(sender, instance, **kwargs):
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
    if instance.cover_image and os.path.isfile(instance.cover_image.path):
        os.remove(instance.cover_image.path)


@receiver(pre_save, sender=Word)
def delete_old_word_image(sender, instance, **kwargs):
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
    if instance.image_path and os.path.isfile(instance.image_path.path):
        os.remove(instance.image_path.path)


# Новые сигналы для обновления word_count
@receiver(post_save, sender=Word)
def increment_word_count(sender, instance, created, **kwargs):
    if created:
        Dictionary.objects.filter(id=instance.dictionary.id).update(word_count=F('word_count') + 1)
        logger.info(f"Word added to Dictionary {instance.dictionary.id}. Incremented word_count.")


@receiver(post_delete, sender=Word)
def decrement_word_count(sender, instance, **kwargs):
    Dictionary.objects.filter(id=instance.dictionary.id).update(word_count=F('word_count') - 1)
    logger.info(f"Word removed from Dictionary {instance.dictionary.id}. Decremented word_count.")
