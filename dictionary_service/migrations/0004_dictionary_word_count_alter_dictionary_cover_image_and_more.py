# Generated by Django 5.1.1 on 2024-11-17 15:08

import dictionary_service.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dictionary_service', '0003_alter_dictionary_cover_image_alter_dictionary_name_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='dictionary',
            name='word_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='dictionary',
            name='cover_image',
            field=models.ImageField(blank=True, max_length=255, null=True, upload_to=dictionary_service.models.dictionary_cover_upload_to, validators=[dictionary_service.models.validate_image_extension]),
        ),
        migrations.AlterField(
            model_name='word',
            name='image_path',
            field=models.ImageField(blank=True, max_length=255, null=True, upload_to=dictionary_service.models.word_image_upload_to, validators=[dictionary_service.models.validate_image_extension]),
        ),
    ]
