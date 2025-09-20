from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from datetime import date, timedelta
from ..utils import get_persian_date_display


class Account(models.Model):
    ACCOUNT_TYPE_RIAL = 'rial'
    ACCOUNT_TYPE_GOLD = 'gold'
    ACCOUNT_TYPE_FOREIGN = 'foreign currency'
    ACCOUNT_TYPE_CHOICES = [
        (ACCOUNT_TYPE_RIAL, _('Rial account')),
        (ACCOUNT_TYPE_GOLD, _('Gold account')),
        (ACCOUNT_TYPE_FOREIGN, _('Foreign Currency account')),
    ]

    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='accounts', verbose_name=_('User'))
    name = models.CharField(max_length=100, verbose_name=_('Account name'))
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES, verbose_name=_('Account type'))
    initial_balance = models.DecimalField(max_digits=18, decimal_places=6, default=0, verbose_name=_('Initial balance'))
    monthly_profit_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0)], verbose_name=_('Monthly profit rate'))
    # Funding options
    FUNDING_SOURCE_TRANSACTION = 'transaction'
    FUNDING_SOURCE_NONE = 'none'
    FUNDING_SOURCE_CHOICES = [
        (FUNDING_SOURCE_TRANSACTION, _('Fund from Transaction')),
        (FUNDING_SOURCE_NONE, _('No Initial Funding')),
    ]
    funding_source = models.CharField(max_length=20, choices=FUNDING_SOURCE_CHOICES, default=FUNDING_SOURCE_NONE, verbose_name=_('Funding source'))
    initial_funding_amount = models.DecimalField(max_digits=18, decimal_places=6, default=0, validators=[MinValueValidator(0)], verbose_name=_('Initial funding amount'))
    # e.g., 2.5 => 2.5% monthly
    last_profit_accrual_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Last profit accrual'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated at'))
    
    class Meta:
        verbose_name = _('Account')
        verbose_name_plural = _('Accounts')

    @property
    def balance(self):
        """Calculate current balance based on initial balance and all transactions"""
        from .transaction import Transaction
        
        # Get all transactions that affect this account
        incoming_txns = Transaction.objects.filter(
            destination_account=self,
            applied=True
        )
        
        outgoing_txns = Transaction.objects.filter(
            source_account=self,
            applied=True
        )
        
        # Calculate incoming amount (considering exchange rates)
        incoming_total = Decimal('0')
        for txn in incoming_txns:
            if txn.kind == Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT:
                # For account-to-account transfers, we need to consider exchange rates
                if (txn.source_account and txn.destination_account and 
                    txn.source_account.account_type != txn.destination_account.account_type and
                    txn.exchange_rate):
                    # Cross-currency transfer: convert amount using exchange rate
                    # The transaction amount is in source currency, we need destination currency
                    converted_amount = Decimal(txn.amount) * Decimal(txn.exchange_rate)
                    incoming_total += converted_amount
                else:
                    # Same currency or no exchange rate needed
                    incoming_total += Decimal(txn.amount)
            elif txn.kind == Transaction.KIND_CREDIT_INCREASE:
                # Credit increase adds money directly to this account
                incoming_total += Decimal(txn.amount)
            elif txn.kind == Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT:
                # Profit from deposit goes to this account
                incoming_total += Decimal(txn.amount)
            else:
                # Other transaction types
                incoming_total += Decimal(txn.amount)
        
        # Calculate outgoing amount (always in this account's currency)
        outgoing_total = Decimal('0')
        for txn in outgoing_txns:
            if txn.kind == Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT:
                # For account-to-account transfers, we need to consider exchange rates
                if (txn.source_account and txn.destination_account and 
                    txn.source_account.account_type != txn.destination_account.account_type and
                    txn.exchange_rate):
                    # Cross-currency transfer: convert amount using exchange rate
                    # The transaction amount is in source currency, we need destination currency
                    converted_amount = Decimal(txn.amount) * Decimal(txn.exchange_rate)
                    outgoing_total += converted_amount
                else:
                    # Same currency or no exchange rate needed
                    outgoing_total += Decimal(txn.amount)
            elif txn.kind == Transaction.KIND_WITHDRAWAL_REQUEST:
                # Withdrawal request removes money from this account
                outgoing_total += Decimal(txn.amount)
            elif txn.kind == Transaction.KIND_ACCOUNT_TO_DEPOSIT_INITIAL:
                # Account to deposit initial removes money from this account
                outgoing_total += Decimal(txn.amount)
            else:
                # Other transaction types
                outgoing_total += Decimal(txn.amount)
        
        return self.initial_balance + incoming_total - outgoing_total

    def save(self, *args, **kwargs):
        is_new = not self.pk
        
        if is_new:
            # Handle initial funding from transaction
            if self.funding_source == self.FUNDING_SOURCE_TRANSACTION and self.initial_funding_amount > 0:
                # Set initial balance to funding amount
                self.initial_balance = self.initial_funding_amount
        
        super().save(*args, **kwargs)

    def accrue_monthly_profit(self):
        now = timezone.now()
        if not self.monthly_profit_rate:
            return
        # Compute profit based on daily snapshots over last 30 days ending yesterday
        period_end = date.today()
        period_start = period_end - timedelta(days=30)
        snapshots = list(self.daily_balances.filter(snapshot_date__gt=period_start).order_by('snapshot_date'))
        # Get carry snapshot on or before start
        carry = self.daily_balances.filter(snapshot_date__lte=period_start).order_by('-snapshot_date').first()
        segments = []
        # Build segments between dates with constant balance
        prev_date = period_start
        prev_balance = Decimal(carry.balance) if carry else Decimal(self.initial_balance)
        for snap in snapshots:
            d = snap.snapshot_date
            if d > prev_date:
                segments.append((prev_date, d, Decimal(snap.balance) if False else prev_balance))
            prev_date = d
            prev_balance = Decimal(snap.balance)
        # Last segment until period_end
        if prev_date < period_end:
            segments.append((prev_date, period_end, prev_balance))
        # Sum daily balances
        total_days = Decimal(0)
        weighted_sum = Decimal(0)
        for start, end, bal in segments:
            days = Decimal((end - start).days)
            if days > 0:
                total_days += days
                weighted_sum += (bal * days)
        if total_days == 0:
            return
        # Monthly profit = rate% * (sum of daily balances / 30)
        average_balance = weighted_sum / Decimal(30)
        profit = (average_balance * Decimal(self.monthly_profit_rate)) / Decimal(100)
        if profit <= 0:
            return
        
        # Create profit transaction instead of directly modifying balance
        from .transaction import Transaction
        profit_transaction = Transaction.objects.create(
            user=self.user,
            source_account=None,
            destination_account=self,
            amount=profit,
            kind=Transaction.KIND_PROFIT_ACCOUNT,
            state=Transaction.STATE_DONE
        )
        profit_transaction.apply()
        
        # Update the last profit accrual timestamp
        self.last_profit_accrual_at = now
        self.save(update_fields=['last_profit_accrual_at', 'updated_at'])

    def get_persian_created_at(self):
        """Return Persian date for created_at"""
        return get_persian_date_display(self.created_at)
    get_persian_created_at.short_description = 'تاریخ ایجاد'
    
    def get_persian_updated_at(self):
        """Return Persian date for updated_at"""
        return get_persian_date_display(self.updated_at)
    get_persian_updated_at.short_description = 'تاریخ بروزرسانی'
    
    def get_persian_last_profit_accrual(self):
        """Return Persian date for last_profit_accrual_at"""
        return get_persian_date_display(self.last_profit_accrual_at)
    get_persian_last_profit_accrual.short_description = 'آخرین سود'
    
    def get_profit_calculation_info(self):
        """Return profit calculation start date and average balance"""
        if self.last_profit_accrual_at:
            # Calculate average balance for the 30-day period
            from django.utils import timezone
            from datetime import timedelta
            from .account_daily_balance import AccountDailyBalance
            
            # Get the start of the profit calculation period (30 days before last accrual)
            profit_start_date = self.last_profit_accrual_at - timedelta(days=30)
            
            # Calculate average balance over the 30-day period
            daily_balances = AccountDailyBalance.objects.filter(
                account=self,
                snapshot_date__gte=profit_start_date.date(),
                snapshot_date__lte=self.last_profit_accrual_at.date()
            ).order_by('snapshot_date')
            
            if daily_balances.exists():
                total_balance = sum(balance.balance for balance in daily_balances)
                avg_balance = total_balance / daily_balances.count()
                return f"شروع: {get_persian_date_display(profit_start_date)} - میانگین: ${avg_balance:,.2f}"
            else:
                return f"شروع: {get_persian_date_display(profit_start_date)} - میانگین: ${self.initial_balance:,.2f}"
        else:
            return "شروع نشده"
    get_profit_calculation_info.short_description = 'اطلاعات سود'

    def __str__(self):
        return f"Account({self.user.username}:{self.name}:{self.account_type})"
