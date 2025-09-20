from django.db import models, transaction
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal


class Transaction(models.Model):
    KIND_CREDIT_INCREASE = 'credit_increase'
    KIND_WITHDRAWAL_REQUEST = 'withdrawal_request'
    KIND_TRANSFER_ACCOUNT_TO_ACCOUNT = 'account_to_account'
    KIND_ACCOUNT_TO_DEPOSIT_INITIAL = 'account_to_deposit_initial'
    KIND_PROFIT_ACCOUNT = 'profit_account'
    KIND_PROFIT_DEPOSIT_TO_ACCOUNT = 'profit_deposit_account'

    KIND_CHOICES = [
        (KIND_CREDIT_INCREASE, 'Credit Increase'),
        (KIND_WITHDRAWAL_REQUEST, 'Withdrawal Request'),
        (KIND_TRANSFER_ACCOUNT_TO_ACCOUNT, 'Account to Account'),
        (KIND_ACCOUNT_TO_DEPOSIT_INITIAL, 'Account to Deposit (Initial)'),
        (KIND_PROFIT_ACCOUNT, 'Account Profit Accrual'),
        (KIND_PROFIT_DEPOSIT_TO_ACCOUNT, 'Deposit Profit to Account'),
    ]

    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='transactions')
    source_account = models.ForeignKey('Account', null=True, blank=True, on_delete=models.SET_NULL, related_name='outgoing_account_transactions')
    destination_account = models.ForeignKey('Account', null=True, blank=True, on_delete=models.SET_NULL, related_name='incoming_account_transactions')
    destination_deposit = models.ForeignKey('Deposit', null=True, blank=True, on_delete=models.SET_NULL, related_name='incoming_deposit_transactions')
    amount = models.DecimalField(max_digits=18, decimal_places=2, validators=[MinValueValidator(0)])
    kind = models.CharField(max_length=40, choices=KIND_CHOICES)
    # Exchange rate to convert between different currency accounts
    # For cross-currency transfers: destination_amount = source_amount * exchange_rate
    exchange_rate = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    applied = models.BooleanField(default=False)
    issued_at = models.DateTimeField(default=timezone.now)
    scheduled_for = models.DateTimeField(null=True, blank=True)
    # Workflow state
    STATE_WAITING_TREASURY = 'waiting_treasury'
    STATE_WAITING_SANDOGH = 'waiting_sandogh'
    STATE_VERIFIED_KHAZANEDAR = 'verified_khazanedar'
    STATE_DONE = 'done'
    STATE_CHOICES = [
        (STATE_WAITING_TREASURY, 'Waiting for Treasury'),
        (STATE_WAITING_SANDOGH, 'Waiting for Sandogh'),
        (STATE_VERIFIED_KHAZANEDAR, 'Verified by Khazane dar'),
        (STATE_DONE, 'Done'),
    ]
    state = models.CharField(max_length=40, choices=STATE_CHOICES, default=STATE_WAITING_TREASURY)

    def clean(self):
        # Basic validation that at least one source and one destination is set appropriately
        if self.kind == self.KIND_CREDIT_INCREASE:
            if not self.destination_account:
                raise ValidationError('Credit increase requires destination_account.')
            return
        if self.kind == self.KIND_WITHDRAWAL_REQUEST:
            if not self.source_account:
                raise ValidationError('Withdrawal request requires source_account.')
            return
        if self.kind == self.KIND_ACCOUNT_TO_DEPOSIT_INITIAL:
            if not (self.source_account and self.destination_deposit):
                raise ValidationError('Account to Deposit requires source_account and destination_deposit')
            return
        if not any([self.source_account]) or not any([self.destination_account, self.destination_deposit]):
            raise ValidationError('Transaction must have a source and a destination.')
        
        # Validate exchange rate for currency conversions
        if self.exchange_rate is not None:
            if self.exchange_rate <= 0:
                raise ValidationError('Exchange rate must be positive.')
            if self.exchange_rate > Decimal('999999999999.999999'):
                raise ValidationError('Exchange rate is too large.')
            if self.exchange_rate < Decimal('0.000001'):
                raise ValidationError('Exchange rate is too small (minimum 0.000001).')
        
        # Validate sufficient balance for source accounts
        if self.source_account and self.amount:
            if Decimal(self.source_account.balance) < Decimal(self.amount):
                raise ValidationError(f'Insufficient account balance. Available: {self.source_account.balance}, Required: {self.amount}')

    def advance_state(self):
        """Advance transaction to the next state in the workflow"""
        state_transitions = {
            self.STATE_WAITING_TREASURY: self.STATE_WAITING_SANDOGH,
            self.STATE_WAITING_SANDOGH: self.STATE_VERIFIED_KHAZANEDAR,
            self.STATE_VERIFIED_KHAZANEDAR: self.STATE_DONE,
            self.STATE_DONE: None,  # No further advancement
        }
        
        next_state = state_transitions.get(self.state)
        if next_state:
            self.state = next_state
            self.save(update_fields=['state'])
            return True
        return False

    @transaction.atomic
    def apply(self):
        # Apply transactional movement with optional conversions
        if self.applied:
            return
        # If scheduled in the future, skip application now
        if self.scheduled_for and self.scheduled_for > timezone.now():
            return
        # Only apply when workflow is marked as done
        if self.state != self.STATE_DONE:
            return
        
        # Validate before applying
        self.clean()
        if self.kind == self.KIND_CREDIT_INCREASE:
            if not self.destination_account:
                return
            # Credit increase adds money to account (no source needed)
            self.applied = True
            self.save(update_fields=['applied'])
            return
        if self.kind == self.KIND_WITHDRAWAL_REQUEST:
            if not self.source_account:
                return
            # Withdrawal request removes money from account (no destination needed)
            self.applied = True
            self.save(update_fields=['applied'])
            return

        if self.kind == self.KIND_ACCOUNT_TO_DEPOSIT_INITIAL:
            # No need to modify balances directly - they're calculated from transactions
            self.applied = True
            self.save(update_fields=['applied'])
            return

        # Currency conversion for account <-> wallet when account is not rial
        def is_account_rial(account: 'Account') -> bool:
            from .account import Account
            return account.account_type == Account.ACCOUNT_TYPE_RIAL

        # Handle account-to-account transactions with exchange rates
        if self.kind == self.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT:
            if self.source_account and self.destination_account:
                # For account-to-account transfers, we need to handle exchange rates
                # The transaction amount is in the source account's currency
                # We need to convert it to the destination account's currency
                
                # If both accounts are the same type (both rial, both foreign, etc.), no conversion needed
                if self.source_account.account_type == self.destination_account.account_type:
                    # Same currency type - direct transfer
                    pass  # No conversion needed
                else:
                    # Different currency types - need exchange rate
                    if not self.exchange_rate or self.exchange_rate <= 0:
                        raise ValidationError('Exchange rate is required for cross-currency account transfers.')
                    
                    # The exchange rate should convert from source currency to destination currency
                    # For example: 1 USD = 500,000 IRR (exchange_rate = 500000)
                    # If transferring 1 USD from USD account to IRR account:
                    # - Source account loses 1 USD
                    # - Destination account gains 500,000 IRR
                    pass  # Exchange rate validation passed

        # No need to modify balances directly - they're calculated from transactions
        self.applied = True
        self.save(update_fields=['applied'])

    @transaction.atomic
    def revert(self):
        # Revert the effects of an already applied transaction
        if not self.applied:
            return
        amt = Decimal(self.amount)
        if self.kind == self.KIND_CREDIT_INCREASE and self.destination_account:
            # No need to modify balance directly - it's calculated from transactions
            self.applied = False
            self.save(update_fields=['applied'])
            return
        if self.kind == self.KIND_WITHDRAWAL_REQUEST and self.source_account:
            # No need to modify balance directly - it's calculated from transactions
            self.applied = False
            self.save(update_fields=['applied'])
            return
        if self.kind == self.KIND_ACCOUNT_TO_DEPOSIT_INITIAL and self.source_account:
            # No need to modify balances directly - they're calculated from transactions
            self.applied = False
            self.save(update_fields=['applied'])
            return

        def is_account_rial(account: 'Account') -> bool:
            from .account import Account
            return account.account_type == Account.ACCOUNT_TYPE_RIAL

        # No need to modify balances directly - they're calculated from transactions
        self.applied = False
        self.save(update_fields=['applied'])

    def __str__(self):
        return f"Txn({self.kind}) {self.amount} by {self.user.username}"
