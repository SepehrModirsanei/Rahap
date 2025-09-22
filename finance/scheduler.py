import threading
import time
from datetime import timedelta, date
from django.db.models import Q
from django.utils import timezone
from decimal import Decimal

_scheduler_started = False


def _create_daily_snapshots():
    """Create daily snapshots for all accounts and deposits."""
    from .models import Account, AccountDailyBalance, Deposit, DepositDailyBalance
    
    today = timezone.now().date()
    created_accounts = 0
    created_deposits = 0
    
    # Snapshot accounts
    for account in Account.objects.all():
        obj, was_created = AccountDailyBalance.objects.get_or_create(
            account=account, snapshot_date=today,
            defaults={'balance': Decimal(account.balance)}
        )
        if was_created:
            created_accounts += 1
    
    # Snapshot deposits
    for deposit in Deposit.objects.all():
        obj, was_created = DepositDailyBalance.objects.get_or_create(
            deposit=deposit, snapshot_date=today,
            defaults={'balance': Decimal(deposit.balance)}
        )
        if was_created:
            created_deposits += 1
    
    return created_accounts, created_deposits


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

    # Auto-apply scheduled transactions whose time has arrived
    from .models import Transaction
    now = timezone.now()
    due_txns = Transaction.objects.filter(
        state=Transaction.STATE_WAITING_TIME,
        applied=False,
        scheduled_for__isnull=False,
        scheduled_for__lte=now,
    )[:200]
    for txn in due_txns:
        try:
            txn.state = Transaction.STATE_DONE
            txn.save(update_fields=['state'])
            txn.apply()
        except Exception:
            pass


def _scheduler_loop():
    # Run periodic scan every 60 seconds
    last_snapshot_date = None
    
    while True:
        try:
            # Create daily snapshots at midnight
            today = timezone.now().date()
            if last_snapshot_date != today:
                _create_daily_snapshots()
                last_snapshot_date = today
            
            # Accrue profits for due accounts and deposits
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


