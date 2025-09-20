from django.db import models, transaction
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal


class Transaction(models.Model):
    KIND_ADD_TO_WALLET = 'add_to_wallet'
    KIND_REMOVE_FROM_WALLET = 'remove_from_wallet'
    KIND_TRANSFER_ACCOUNT_TO_WALLET = 'account_to_wallet'
    KIND_TRANSFER_WALLET_TO_ACCOUNT = 'wallet_to_account'
    KIND_TRANSFER_WALLET_TO_WALLET = 'wallet_to_wallet'
    KIND_TRANSFER_ACCOUNT_TO_ACCOUNT = 'account_to_account'
    KIND_WALLET_TO_DEPOSIT_INITIAL = 'wallet_to_deposit_initial'
    KIND_PROFIT_ACCOUNT = 'profit_account'
    KIND_PROFIT_DEPOSIT_TO_WALLET = 'profit_deposit_wallet'

    KIND_CHOICES = [
        (KIND_ADD_TO_WALLET, 'Add to Wallet'),
        (KIND_REMOVE_FROM_WALLET, 'Remove from Wallet'),
        (KIND_TRANSFER_ACCOUNT_TO_WALLET, 'Account to Wallet'),
        (KIND_TRANSFER_WALLET_TO_ACCOUNT, 'Wallet to Account'),
        (KIND_TRANSFER_WALLET_TO_WALLET, 'Wallet to Wallet'),
        (KIND_TRANSFER_ACCOUNT_TO_ACCOUNT, 'Account to Account'),
        (KIND_WALLET_TO_DEPOSIT_INITIAL, 'Wallet to Deposit (Initial)'),
        (KIND_PROFIT_ACCOUNT, 'Account Profit Accrual'),
        (KIND_PROFIT_DEPOSIT_TO_WALLET, 'Deposit Profit to Wallet'),
    ]

    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='transactions')
    source_wallet = models.ForeignKey('Wallet', null=True, blank=True, on_delete=models.SET_NULL, related_name='outgoing_wallet_transactions')
    destination_wallet = models.ForeignKey('Wallet', null=True, blank=True, on_delete=models.SET_NULL, related_name='incoming_wallet_transactions')
    source_account = models.ForeignKey('Account', null=True, blank=True, on_delete=models.SET_NULL, related_name='outgoing_account_transactions')
    destination_account = models.ForeignKey('Account', null=True, blank=True, on_delete=models.SET_NULL, related_name='incoming_account_transactions')
    destination_deposit = models.ForeignKey('Deposit', null=True, blank=True, on_delete=models.SET_NULL, related_name='incoming_deposit_transactions')
    amount = models.DecimalField(max_digits=18, decimal_places=2, validators=[MinValueValidator(0)])
    kind = models.CharField(max_length=40, choices=KIND_CHOICES)
    # Exchange rate to convert non-Rial accounts to wallet IRR and vice versa.
    # If moving account->wallet and account is not rial, wallet_amount = amount * exchange_rate
    # If moving wallet->account non-rial, account_amount = amount / exchange_rate
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
        if self.kind in [self.KIND_ADD_TO_WALLET, self.KIND_REMOVE_FROM_WALLET]:
            if not (self.destination_wallet or self.source_wallet):
                raise ValidationError('Add/Remove requires wallet.')
            return
        if self.kind == self.KIND_WALLET_TO_DEPOSIT_INITIAL:
            if not (self.source_wallet and self.destination_deposit):
                raise ValidationError('Wallet to Deposit requires source_wallet and destination_deposit')
            return
        if not any([self.source_wallet, self.source_account]) or not any([self.destination_wallet, self.destination_account]):
            raise ValidationError('Transaction must have a source and a destination.')
        
        # Validate exchange rate for currency conversions
        if self.exchange_rate is not None:
            if self.exchange_rate <= 0:
                raise ValidationError('Exchange rate must be positive.')
            if self.exchange_rate > Decimal('999999999999.999999'):
                raise ValidationError('Exchange rate is too large.')
            if self.exchange_rate < Decimal('0.000001'):
                raise ValidationError('Exchange rate is too small (minimum 0.000001).')
        
        # Validate sufficient balance for source accounts/wallets
        if self.source_wallet and self.amount:
            if Decimal(self.source_wallet.balance) < Decimal(self.amount):
                raise ValidationError(f'Insufficient wallet balance. Available: {self.source_wallet.balance}, Required: {self.amount}')
        
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
        if self.kind == self.KIND_ADD_TO_WALLET:
            if not self.destination_wallet:
                return
            # No need to modify balance directly - it's calculated from transactions
            self.applied = True
            self.save(update_fields=['applied'])
            return
        if self.kind == self.KIND_REMOVE_FROM_WALLET:
            if not self.source_wallet:
                return
            # No need to modify balance directly - it's calculated from transactions
            self.applied = True
            self.save(update_fields=['applied'])
            return

        if self.kind == self.KIND_WALLET_TO_DEPOSIT_INITIAL:
            # No need to modify balances directly - they're calculated from transactions
            self.applied = True
            self.save(update_fields=['applied'])
            return

        # Currency conversion for account <-> wallet when account is not rial
        def is_account_rial(account: 'Account') -> bool:
            from .account import Account
            return account.account_type == Account.ACCOUNT_TYPE_RIAL

        # No need to modify balances directly - they're calculated from transactions

        # No need to modify balances directly - they're calculated from transactions
        self.applied = True
        self.save(update_fields=['applied'])

    @transaction.atomic
    def revert(self):
        # Revert the effects of an already applied transaction
        if not self.applied:
            return
        amt = Decimal(self.amount)
        if self.kind == self.KIND_ADD_TO_WALLET and self.destination_wallet:
            # No need to modify balance directly - it's calculated from transactions
            self.applied = False
            self.save(update_fields=['applied'])
            return
        if self.kind == self.KIND_REMOVE_FROM_WALLET and self.source_wallet:
            # No need to modify balance directly - it's calculated from transactions
            self.applied = False
            self.save(update_fields=['applied'])
            return
        if self.kind == self.KIND_WALLET_TO_DEPOSIT_INITIAL and self.source_wallet:
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
