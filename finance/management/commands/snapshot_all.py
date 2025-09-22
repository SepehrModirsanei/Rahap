from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal

from finance.models import Account, AccountDailyBalance, Deposit, DepositDailyBalance


class Command(BaseCommand):
    help = 'Snapshot all accounts and deposits balances for today (00:00 snapshot)'

    def handle(self, *args, **options):
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
                
        self.stdout.write(self.style.SUCCESS(
            f'Created {created_accounts} account snapshot(s) and {created_deposits} deposit snapshot(s) for {today}'
        ))
