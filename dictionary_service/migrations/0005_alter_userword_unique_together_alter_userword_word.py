# Generated by Django 5.1.1 on 2024-12-04 12:23

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dictionary_service', '0004_dictionary_word_count_alter_dictionary_cover_image_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='userword',
            unique_together=set(),
        ),
        migrations.AlterField(
            model_name='userword',
            name='word',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='userword', to='dictionary_service.word'),
        ),
    ]