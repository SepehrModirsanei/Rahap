from django.core.management.base import BaseCommand
from django.db import transaction as db_txn
from django.utils import timezone
from zoneinfo import ZoneInfo
from persiantools.jdatetime import JalaliDateTime


class Command(BaseCommand):
    help = "Regenerate transaction_code for all transactions to the new format"

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Only show what would change')

    @db_txn.atomic
    def handle(self, *args, **options):
        from finance.models import Transaction

        tehran_tz = ZoneInfo('Asia/Tehran')

        def prefix_for_kind(kind: str) -> str:
            return {
                Transaction.KIND_CREDIT_INCREASE: 'In',
                Transaction.KIND_WITHDRAWAL_REQUEST: 'Out',
                Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT: 'Transfer',
                Transaction.KIND_ACCOUNT_TO_DEPOSIT_INITIAL: 'Transition',
                Transaction.KIND_PROFIT_ACCOUNT: 'Profit',
                Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT: 'Profit',
            }.get(kind, 'Txn')

        updated = 0
        skipped = 0
        for t in Transaction.objects.all().order_by('id').select_related('user'):
            old = t.transaction_code or ''
            # If already in new style (contains three dashes and not starting with TXN-), skip
            if old and '-' in old and not old.startswith('TXN-'):
                skipped += 1
                continue

            prefix = prefix_for_kind(t.kind)
            try:
                user_part = t.user.short_user_id if t.user else '00000000'
            except Exception:
                user_part = '00000000'

            issued_dt = t.issued_at or timezone.now()
            issued_local = issued_dt.astimezone(tehran_tz)
            jalali_date = JalaliDateTime(issued_local).strftime('%Y%m%d')

            base_code = f"{prefix}-{user_part}-{jalali_date}-"
            # Determine next sequence based on existing rows with same base_code
            seq = (
                Transaction.objects.filter(transaction_code__startswith=base_code).count()
                + 1
            )
            new_code = f"{base_code}{seq:02d}"

            if options['dry_run']:
                self.stdout.write(f"Would update id={t.id} {old} -> {new_code}")
            else:
                t.transaction_code = new_code
                t.save(update_fields=['transaction_code'])
                updated += 1

        if options['dry_run']:
            self.stdout.write(self.style.WARNING(f"Dry run complete. Skipped existing new-format: {skipped}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Updated {updated} transaction codes. Skipped in new format: {skipped}"))


