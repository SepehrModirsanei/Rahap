from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from ..utils import get_persian_date_display


class Deposit(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='deposits', verbose_name=_('User'))
    initial_balance = models.DecimalField(max_digits=18, decimal_places=2, validators=[MinValueValidator(0)], verbose_name=_('Initial balance'))
    monthly_profit_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0)], verbose_name=_('Monthly profit rate'))
    # Funding options
    FUNDING_SOURCE_TRANSACTION = 'transaction'
    FUNDING_SOURCE_NONE = 'none'
    FUNDING_SOURCE_CHOICES = [
        (FUNDING_SOURCE_TRANSACTION, _('Fund from Transaction')),
        (FUNDING_SOURCE_NONE, _('No Initial Funding')),
    ]
    funding_source = models.CharField(max_length=20, choices=FUNDING_SOURCE_CHOICES, default=FUNDING_SOURCE_NONE, verbose_name=_('Funding source'))
    # Account to fund from when funding_source is 'transaction'
    funding_account = models.ForeignKey('Account', on_delete=models.SET_NULL, null=True, blank=True, related_name='funded_deposits', verbose_name=_('Funding account'))
    # Profit goes to wallet (not compounded)
    last_profit_accrual_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Last profit accrual'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated at'))
    
    class Meta:
        verbose_name = _('Deposit')
        verbose_name_plural = _('Deposits')

    @property
    def amount(self):
        """Alias for initial_balance for backward compatibility"""
        return self.initial_balance

    @property
    def balance(self):
        """Calculate current balance based on initial balance and all transactions"""
        from .transaction import Transaction
        # Get all transactions that affect this deposit
        incoming = Transaction.objects.filter(
            destination_deposit=self,
            applied=True
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
        
        # Deposits can only receive money, not send it
        return self.initial_balance + incoming

    def save(self, *args, **kwargs):
        is_new = not self.pk
        
        if is_new:
            # Handle initial funding from transaction
            if self.funding_source == self.FUNDING_SOURCE_TRANSACTION and self.initial_balance > 0:
                # Set initial balance to funding amount
                self.initial_balance = self.initial_balance
        
        super().save(*args, **kwargs)

    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Validate funding based on funding source
        if self.funding_source == self.FUNDING_SOURCE_TRANSACTION:
            if not self.funding_account:
                raise ValidationError('Funding account is required when funding source is "Fund from Transaction".')
            if self.funding_account.user != self.user:
                raise ValidationError('Funding account must belong to the same user.')
            if self.funding_account.account_type != 'rial':
                raise ValidationError('Funding account must be a rial account.')
            if self.initial_balance and self.initial_balance > 0:
                if self.funding_account.balance < self.initial_balance:
                    raise ValidationError(f'Insufficient balance in funding account. Available: {self.funding_account.balance}, Required: {self.initial_balance}')

    def accrue_monthly_profit(self):
        now = timezone.now()
        if self.monthly_profit_rate and (not self.last_profit_accrual_at or (now - self.last_profit_accrual_at).days >= 28):
            # Calculate profit based on current deposit amount (not just initial balance)
            profit = (self.initial_balance * self.monthly_profit_rate) / 100
            if profit <= 0:
                return
                
            # Find user's base account (حساب پایه) to credit profit
            base_account = self.user.accounts.filter(account_type='rial', name='حساب پایه').first()
            if not base_account:
                # This should not happen as User model creates a default base account
                return
            
            # Create and apply profit transaction
            from .transaction import Transaction
            profit_transaction = Transaction.objects.create(
                user=self.user,
                source_account=None,
                destination_account=base_account,
                amount=profit,
                kind=Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT,
                state=Transaction.STATE_DONE
            )
            profit_transaction.apply()
            
            # Update only the timestamp (profit goes to user's base account, not back to deposit)
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
            # For deposits, the profit calculation starts when the deposit is created
            # and is based on the initial_balance (which gets updated with profits)
            profit_start_date = self.created_at
            
            # The average balance for deposits is the initial_balance
            # (which includes accumulated profits)
            return f"شروع: {get_persian_date_display(profit_start_date)} - میانگین: ${self.initial_balance:,.2f}"
        else:
            return "شروع نشده"
    get_profit_calculation_info.short_description = 'اطلاعات سود'

    def __str__(self):
        return f"Deposit({self.user.username}) initial_balance={self.initial_balance}"
