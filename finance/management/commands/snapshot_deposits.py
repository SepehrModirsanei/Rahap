from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal

from finance.models import Deposit, DepositDailyBalance


class Command(BaseCommand):
    help = 'Snapshot all deposits balances for today (00:00 snapshot)'

    def handle(self, *args, **options):
        today = timezone.now().date()
        created = 0
        for deposit in Deposit.objects.all():
            obj, was_created = DepositDailyBalance.objects.get_or_create(
                deposit=deposit, snapshot_date=today,
                defaults={'balance': Decimal(deposit.balance)}
            )
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f'Created {created} deposit snapshot(s) for {today}'))
