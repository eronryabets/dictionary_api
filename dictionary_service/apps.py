from django.apps import AppConfig


class DictionaryServiceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dictionary_service'

    def ready(self):
        import dictionary_service.utils.signals  # Подключение сигналов
