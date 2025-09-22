import threading
import time
from datetime import timedelta
from django.db.models import Q
from django.utils import timezone

_scheduler_started = False


def _accrue_due_profits_once():
    """Run a single scan to accrue profits for due accounts and deposits."""
    from .models import Account, Deposit  # Lazy import to avoid AppConfig import cycles

    now = timezone.now()
    due_threshold = now - timedelta(days=30)

    # Accounts due: last_profit_accrual_at <= threshold OR null and created_at <= threshold
    accounts_due = Account.objects.filter(
        monthly_profit_rate__gt=0
    ).filter(
        Q(last_profit_accrual_at__lte=due_threshold) |
        (Q(last_profit_accrual_at__isnull=True) & Q(created_at__lte=due_threshold))
    )

    for acc in accounts_due[:200]:  # safety cap per tick
        try:
            acc.accrue_monthly_profit()
        except Exception:
            # Don't let one failure stop the loop
            pass

    # Deposits due
    deposits_due = Deposit.objects.filter(
        monthly_profit_rate__gt=0
    ).filter(
        Q(last_profit_accrual_at__lte=due_threshold) |
        (Q(last_profit_accrual_at__isnull=True) & Q(created_at__lte=due_threshold))
    )

    for dep in deposits_due[:200]:
        try:
            dep.accrue_monthly_profit()
        except Exception:
            pass


def _scheduler_loop():
    # Run periodic scan every 60 seconds
    while True:
        try:
            _accrue_due_profits_once()
        except Exception:
            # swallow errors and keep running
            pass
        time.sleep(60)


def start_profit_scheduler():
    global _scheduler_started
    if _scheduler_started:
        return
    _scheduler_started = True
    t = threading.Thread(target=_scheduler_loop, name="profit-scheduler", daemon=True)
    t.start()


