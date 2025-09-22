from django.apps import AppConfig


class FinanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'finance'

    def ready(self):
        from . import signals  # noqa
        from .signals import transaction_signals  # noqa
        # Start background profit scheduler
        try:
            from .scheduler import start_profit_scheduler
            start_profit_scheduler()
        except Exception:
            # Avoid breaking startup if scheduler fails
            pass
