from django.core.management.base import BaseCommand

from finance.models import Account, Deposit


class Command(BaseCommand):
    help = 'Accrue monthly profit for accounts (compounded) and deposits (to wallet).'

    def handle(self, *args, **options):
        count_acc = 0
        count_dep = 0
        for account in Account.objects.all():
            before = account.balance
            account.accrue_monthly_profit()
            if account.balance != before:
                count_acc += 1
        for deposit in Deposit.objects.all():
            before = deposit.last_profit_accrual_at
            deposit.accrue_monthly_profit()
            if deposit.last_profit_accrual_at != before:
                count_dep += 1
        self.stdout.write(self.style.SUCCESS(f"Accrued profit: accounts={count_acc}, deposits={count_dep}"))


