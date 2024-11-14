from django.contrib import admin
from .models import Dictionary, Tag, Word


@admin.register(Dictionary)
class DictionaryAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'language', 'name', 'created_at', 'updated_at')
    list_filter = ('language', 'created_at')
    search_fields = ('id', 'user_id', 'language', 'name')
    ordering = ('-created_at',)
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at', 'updated_at')
    search_fields = ('name',)
    ordering = ('name',)
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    list_display = ('id', 'dictionary', 'word', 'translation', 'image_path', 'created_at', 'updated_at')
    list_filter = ('dictionary__language', 'tags', 'created_at')
    search_fields = ('word', 'translation', 'dictionary__name')
    ordering = ('word',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    filter_horizontal = ('tags',)  # Улучшение интерфейса для ManyToManyField

    def get_queryset(self, request):
        # Оптимизация запросов с использованием select_related и prefetch_related
        qs = super().get_queryset(request)
        return qs.select_related('dictionary').prefetch_related('tags')
