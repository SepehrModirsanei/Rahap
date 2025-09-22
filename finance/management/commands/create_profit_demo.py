from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal

from finance.models import User, Account, Deposit


class Command(BaseCommand):
    help = "Create a demo user with an account and a deposit whose next profit accrual will be due in ~2 minutes."

    def add_arguments(self, parser):
        parser.add_argument('--username', default='profit_demo_user', help='Username for the demo user')
        parser.add_argument('--email', default='profit_demo@example.com', help='Email for the demo user')
        parser.add_argument('--account-balance', default='100000.00', help='Initial balance for the account (IRR)')
        parser.add_argument('--deposit-balance', default='50000.00', help='Initial balance for the deposit (IRR)')
        parser.add_argument('--rate', default='2.50', help='Monthly profit rate (percent) for both account and deposit')
        parser.add_argument('--days-ago', type=int, default=27, help='How many days ago to set last_profit_accrual_at (default 27)')

    def handle(self, *args, **options):
        username: str = options['username']
        email: str = options['email']
        account_balance = Decimal(options['account_balance'])
        deposit_balance = Decimal(options['deposit_balance'])
        monthly_rate = Decimal(options['rate'])

        user, _ = User.objects.get_or_create(username=username, defaults={'email': email})
        if not user.has_usable_password():
            user.set_password('pass')
            user.save(update_fields=['password'])

        # Create a Rial account (required for profits and withdrawals)
        account, _ = Account.objects.get_or_create(
            user=user,
            name='Demo Rial Account',
            defaults={
                'account_type': Account.ACCOUNT_TYPE_RIAL,
                'initial_balance': account_balance,
                'monthly_profit_rate': monthly_rate,
            }
        )
        # Ensure fields are set if it already existed
        account.account_type = Account.ACCOUNT_TYPE_RIAL
        account.monthly_profit_rate = monthly_rate
        account.initial_balance = account_balance
        # Set last_profit_accrual_at relative to now
        days_ago = int(options['days_ago'])
        back_dt = timezone.now() - timezone.timedelta(days=days_ago)
        account.last_profit_accrual_at = back_dt
        account.save()
        # Also backdate created_at for display purposes
        from django.db.models import F
        type(account).objects.filter(pk=account.pk).update(created_at=back_dt)

        # Create a deposit for the same user
        deposit, _ = Deposit.objects.get_or_create(
            user=user,
            defaults={
                'initial_balance': deposit_balance,
                'monthly_profit_rate': monthly_rate,
            }
        )
        deposit.initial_balance = deposit_balance
        deposit.monthly_profit_rate = monthly_rate
        deposit.last_profit_accrual_at = back_dt
        deposit.save()
        type(deposit).objects.filter(pk=deposit.pk).update(created_at=back_dt)

        self.stdout.write(self.style.SUCCESS('Demo data prepared successfully.'))
        self.stdout.write(f"User: {user.username} (id={user.id})")
        self.stdout.write(f"Account: {account.name} | balance={account.initial_balance} | rate={account.monthly_profit_rate}% | last_profit_accrual_at={account.last_profit_accrual_at}")
        self.stdout.write(f"Deposit: balance={deposit.initial_balance} | rate={deposit.monthly_profit_rate}% | last_profit_accrual_at={deposit.last_profit_accrual_at}")
        self.stdout.write("")
        self.stdout.write("What next:")
        self.stdout.write("1) Wait ~2 minutes.")
        self.stdout.write("2) Run: python manage.py accrue_monthly_profit")
        self.stdout.write("   This will create profit transactions for due accounts/deposits.")
        self.stdout.write("3) Check admin Transaction pages to see created profit transactions.")


