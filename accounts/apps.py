from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    verbose_name = "User Accounts & Authentication"

    def ready(self):
        # This is where you load signals if you add any
        try:
            import accounts.signals
        except ImportError:
            pass

