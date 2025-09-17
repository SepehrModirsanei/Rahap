from django.core.management.base import BaseCommand
from django.utils import timezone

from finance.models import Transaction


class Command(BaseCommand):
    help = 'Process and apply all due (not yet applied) transactions scheduled up to now.'

    def handle(self, *args, **options):
        now = timezone.now()
        due = Transaction.objects.filter(applied=False).filter(
            scheduled_for__isnull=True
        ) | Transaction.objects.filter(applied=False, scheduled_for__lte=now)
        count = 0
        for txn in due.order_by('id'):
            before = txn.applied
            txn.apply()
            if not before and txn.applied:
                count += 1
        self.stdout.write(self.style.SUCCESS(f'Applied {count} scheduled or immediate transactions'))


