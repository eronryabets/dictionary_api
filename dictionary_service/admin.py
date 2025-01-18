
from django.contrib import admin
from .models import Dictionary, Tag, Word, UserWord
from django.utils.html import format_html


@admin.register(Dictionary)
class DictionaryAdmin(admin.ModelAdmin):
    list_display = (
    'id', 'user_id', 'language', 'name', 'word_count', 'cover_image_display', 'created_at', 'updated_at')
    list_filter = ('language', 'created_at')
    search_fields = ('id', 'user_id', 'language', 'name')
    ordering = ('-created_at',)
    readonly_fields = (
    'id', 'created_at', 'updated_at', 'cover_image_display', 'word_count')  # word_count только для чтения
    fields = (
    'user_id', 'language', 'name', 'cover_image', 'cover_image_display', 'word_count', 'created_at', 'updated_at')

    def cover_image_display(self, obj):
        if obj.cover_image:
            return format_html('<img src="{}" width="100" height="100" />', obj.cover_image.url)
        return "-"

    cover_image_display.short_description = 'Cover Image Preview'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at', 'updated_at')
    search_fields = ('name',)
    ordering = ('name',)
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    list_display = (
    'id', 'dictionary', 'word', 'translation', 'image_path_display', 'display_tags', 'get_count', 'get_progress',
    'created_at', 'updated_at')
    list_filter = ('dictionary__language', 'tags', 'created_at')
    search_fields = ('word', 'translation', 'dictionary__name')
    ordering = ('word',)
    readonly_fields = ('id', 'created_at', 'updated_at', 'image_path_display', 'get_count', 'get_progress')
    filter_horizontal = ('tags',)
    fields = (
    'dictionary', 'word', 'translation', 'image_path', 'image_path_display', 'tags', 'get_count', 'get_progress',
    'created_at', 'updated_at')

    def display_tags(self, obj):
        return ", ".join([tag.name for tag in obj.tags.all()])

    display_tags.short_description = 'Tags'

    def image_path_display(self, obj):
        if obj.image_path:
            return format_html('<img src="{}" width="100" height="100" />', obj.image_path.url)
        return "-"

    image_path_display.short_description = 'Image Preview'

    # Добавляем методы для отображения count и progress
    def get_count(self, obj):
        try:
            return obj.userword.count
        except UserWord.DoesNotExist:
            return 'N/A'

    get_count.short_description = 'Count'

    def get_progress(self, obj):
        try:
            return obj.userword.progress
        except UserWord.DoesNotExist:
            return 'N/A'

    get_progress.short_description = 'Progress'


@admin.register(UserWord)
class UserWordAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'word',
        'count',
        'progress',
        'highlight_disabled',
        'last_accessed',
        'created_at',
        'updated_at'
    )
    search_fields = ('word__word',)
