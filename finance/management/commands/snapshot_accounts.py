from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal

from finance.models import Account, AccountDailyBalance


class Command(BaseCommand):
    help = 'Snapshot all accounts balances for today (00:00 snapshot)'

    def handle(self, *args, **options):
        today = timezone.now().date()
        created = 0
        for acc in Account.objects.all():
            obj, was_created = AccountDailyBalance.objects.get_or_create(
                account=acc, snapshot_date=today,
                defaults={'balance': Decimal(acc.balance)}
            )
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f'Created {created} account snapshot(s) for {today}'))


