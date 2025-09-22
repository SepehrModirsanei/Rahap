from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import pytz

from finance.models import Deposit, DepositDailyBalance


class Command(BaseCommand):
    help = 'Snapshot all deposits balances for today (00:00 Iran time snapshot)'

    def handle(self, *args, **options):
        # Get current date in Iran timezone
        iran_tz = pytz.timezone('Asia/Tehran')
        now_iran = timezone.now().astimezone(iran_tz)
        today = now_iran.date()
        created = 0
        for deposit in Deposit.objects.all():
            obj, was_created = DepositDailyBalance.objects.get_or_create(
                deposit=deposit, snapshot_date=today,
                defaults={'balance': Decimal(deposit.balance)}
            )
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f'Created {created} deposit snapshot(s) for {today}'))
