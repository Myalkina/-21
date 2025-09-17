from django.apps import AppConfig


class NewsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'news'

    def ready(self):
        # Импортируем и запускаем планировщик только при запуске приложения
        import os
        if os.environ.get('RUN_MAIN'):
            from .tasks import start_scheduler
            start_scheduler()