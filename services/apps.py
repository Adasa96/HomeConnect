from django.apps import AppConfig


class ServicesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'services'
    verbose_name = "Homeowner Service Management"

    def ready(self):
        # Load services-related signals later if needed
        try:
            import services.signals
        except ImportError:
            pass
