from django.db import models, transaction
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from datetime import timedelta
from zoneinfo import ZoneInfo
from persiantools.jdatetime import JalaliDateTime
from ..utils import get_persian_date_display


class Transaction(models.Model):
    KIND_CREDIT_INCREASE = 'credit_increase'
    KIND_WITHDRAWAL_REQUEST = 'withdrawal_request'
    KIND_TRANSFER_ACCOUNT_TO_ACCOUNT = 'account_to_account'
    KIND_ACCOUNT_TO_DEPOSIT_INITIAL = 'account_to_deposit_initial'
    KIND_PROFIT_ACCOUNT = 'profit_account'
    KIND_PROFIT_DEPOSIT_TO_ACCOUNT = 'profit_deposit_account'

    KIND_CHOICES = [
        (KIND_CREDIT_INCREASE, _('افزایش اعتبار')),
        (KIND_WITHDRAWAL_REQUEST, _('درخواست برداشت')),
        (KIND_TRANSFER_ACCOUNT_TO_ACCOUNT, _('انتقال حساب به حساب')),
        (KIND_ACCOUNT_TO_DEPOSIT_INITIAL, _('حساب به سپرده اولیه')),
        (KIND_PROFIT_ACCOUNT, _('سود به حساب')),
        (KIND_PROFIT_DEPOSIT_TO_ACCOUNT, _('سود سپرده به حساب')),
    ]

    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='transactions', verbose_name=_('کاربر'))
    # Unique transaction code for easy identification
    transaction_code = models.CharField(max_length=64, unique=True, editable=False, null=True, blank=True, verbose_name=_('کد تراکنش'))
    source_account = models.ForeignKey('Account', null=True, blank=True, on_delete=models.SET_NULL, related_name='outgoing_account_transactions', verbose_name=_('حساب مبدا'))
    destination_account = models.ForeignKey('Account', null=True, blank=True, on_delete=models.SET_NULL, related_name='incoming_account_transactions', verbose_name=_('حساب مقصد'))
    destination_deposit = models.ForeignKey('Deposit', null=True, blank=True, on_delete=models.SET_NULL, related_name='incoming_deposit_transactions', verbose_name=_('سپرده مقصد'))
    amount = models.DecimalField(max_digits=18, decimal_places=2, validators=[MinValueValidator(0)], verbose_name=_('مبلغ'))
    kind = models.CharField(max_length=40, choices=KIND_CHOICES, verbose_name=_('نوع'))
    # Exchange rate to convert between different currency accounts
    # For cross-currency transfers: destination_amount = source_amount * exchange_rate
    exchange_rate = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True, verbose_name=_('نرخ تبدیل'))
    # Destination leg amount (computed and stored) for cross-currency transfers
    destination_amount = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True, verbose_name=_('مبلغ مقصد'))
    # Optional explicit prices in IRR for currency→currency transfers (admin entry)
    source_price_irr = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True, verbose_name=_('قیمت ارز مبدا بر حسب ریال'))
    dest_price_irr = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True, verbose_name=_('قیمت ارز مقصد بر حسب ریال'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    applied = models.BooleanField(default=False, verbose_name=_('اعمال شده'))
    issued_at = models.DateTimeField(default=timezone.now, verbose_name=_('تاریخ صدور'))
    scheduled_for = models.DateTimeField(null=True, blank=True, verbose_name=_('زمان‌بندی شده برای'))
    # Workflow state
    STATE_WAITING_TREASURY = 'waiting_treasury'
    STATE_WAITING_SANDOGH = 'waiting_sandogh'
    STATE_VERIFIED_KHAZANEDAR = 'verified_khazanedar'
    STATE_WAITING_TIME = 'waiting_time'
    STATE_DONE = 'done'
    STATE_REJECTED = 'rejected'
    STATE_WAITING_FINANCE_MANAGER = 'waiting_finance_manager'
    STATE_APPROVED_BY_FINANCE_MANAGER = 'approved_by_finance_manager'
    STATE_APPROVED_BY_SANDOGH = 'approved_by_sandogh'
    STATE_CHOICES = [
        (STATE_WAITING_TREASURY, _('در انتظار خزانه‌داری')),
        (STATE_WAITING_SANDOGH, _('در انتظار صندوق')),
        (STATE_VERIFIED_KHAZANEDAR, _('تایید شده توسط خزانه‌دار')),
        (STATE_WAITING_TIME, _('در انتظار زمان تنظیم شده')),
        (STATE_DONE, _('انجام شده')),
        (STATE_REJECTED, _('رد شده')),
        (STATE_WAITING_FINANCE_MANAGER, _('در انتظار تایید مدیر مالی')),
        (STATE_APPROVED_BY_FINANCE_MANAGER, _('تایید شده توسط مدیر مالی')),
        (STATE_APPROVED_BY_SANDOGH, _('تایید شده توسط صندوق')),
    ]
    state = models.CharField(max_length=40, choices=STATE_CHOICES, default=STATE_WAITING_TREASURY, verbose_name=_('وضعیت'))
    
    # Receipt for credit increase transactions
    receipt = models.ImageField(upload_to='receipts/', null=True, blank=True, verbose_name=_('رسید'), help_text=_('آپلود تصویر رسید (فرمت JPG) برای تراکنش‌های افزایش اعتبار'))
    
    # Withdrawal destination information
    withdrawal_card_number = models.CharField(max_length=16, blank=True, verbose_name=_('شماره کارت'), help_text=_('شماره کارت 16 رقمی برای برداشت'))
    withdrawal_sheba_number = models.CharField(max_length=24, blank=True, verbose_name=_('شماره شبا'), help_text=_('شماره شبا 24 رقمی برای برداشت'))
    # Admin opinions
    admin_opinion = models.TextField(blank=True, verbose_name=_('نظر ادمین'))
    treasurer_opinion = models.TextField(blank=True, verbose_name=_('نظر خزانه‌دار'))
    finance_manager_opinion = models.TextField(blank=True, verbose_name=_('نظر مدیر مالی'))
    user_comment = models.TextField(blank=True, verbose_name=_('نظر کاربر'))
    
    class Meta:
        verbose_name = _('تراکنش')
        verbose_name_plural = _('تراکنش‌ها')

    def clean(self):
        # Basic validation that at least one source and one destination is set appropriately
        if self.kind == self.KIND_CREDIT_INCREASE:
            if not self.destination_account:
                raise ValidationError('Credit increase requires destination_account.')
            # Credit increase must work with rial accounts only
            if self.destination_account.account_type != 'rial':
                raise ValidationError('Credit increase can only be applied to rial accounts.')
            return
        if self.kind == self.KIND_WITHDRAWAL_REQUEST:
            if not self.source_account:
                raise ValidationError('Withdrawal request requires source_account.')
            # Withdrawal request must work with rial accounts only
            if self.source_account.account_type != 'rial':
                raise ValidationError('Withdrawal request can only be applied to rial accounts.')
            # Validate withdrawal destination
            if not self.withdrawal_card_number and not self.withdrawal_sheba_number:
                raise ValidationError('Withdrawal request requires either card number or SHEBA number.')
            if self.withdrawal_card_number and self.withdrawal_sheba_number:
                raise ValidationError('Withdrawal request can have either card number or SHEBA number, not both.')
            # Validate card number format
            if self.withdrawal_card_number:
                if not self.withdrawal_card_number.isdigit() or len(self.withdrawal_card_number) != 16:
                    raise ValidationError('Card number must be 16 digits.')
            # Validate SHEBA number format
            if self.withdrawal_sheba_number:
                if not self.withdrawal_sheba_number.startswith('IR') or len(self.withdrawal_sheba_number) != 24:
                    raise ValidationError('SHEBA number must start with IR and be 24 characters long.')
            return
        if self.kind == self.KIND_ACCOUNT_TO_DEPOSIT_INITIAL:
            if not (self.source_account and self.destination_deposit):
                raise ValidationError('Account to Deposit requires source_account and destination_deposit')
            return
        
        # Validate account-to-account transactions
        if self.kind == self.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT:
            if not (self.source_account and self.destination_account):
                raise ValidationError('Account to Account transfer requires both source_account and destination_account')
            
            # Check and compute destination_amount for cross-currency transfers
            from .account import Account
            src_t = self.source_account.account_type
            dst_t = self.destination_account.account_type
            same_type = (src_t == dst_t)

            def is_rial(t):
                return t == Account.ACCOUNT_TYPE_RIAL

            def is_foreign_or_gold(t):
                return t in [Account.ACCOUNT_TYPE_USD, Account.ACCOUNT_TYPE_EUR, Account.ACCOUNT_TYPE_GBP, Account.ACCOUNT_TYPE_GOLD]

            if same_type:
                # No conversion needed; destination_amount equals source amount
                self.destination_amount = self.amount
            else:
                # Rial <-> FX/Gold uses single exchange_rate = IRR price per 1 unit of non-rial currency
                if (is_rial(src_t) and is_foreign_or_gold(dst_t)):
                    # Rial → foreign: dest = amount / rate
                    if not self.exchange_rate or self.exchange_rate <= 0:
                        raise ValidationError('Exchange rate (IRR per destination currency) is required and must be positive for Rial→Foreign/Gold.')
                    self.destination_amount = (Decimal(self.amount) / Decimal(self.exchange_rate)).quantize(Decimal('0.000001'))
                elif (is_foreign_or_gold(src_t) and is_rial(dst_t)):
                    # Foreign → Rial: dest = amount × rate
                    if not self.exchange_rate or self.exchange_rate <= 0:
                        raise ValidationError('Exchange rate (IRR per source currency) is required and must be positive for Foreign/Gold→Rial.')
                    self.destination_amount = (Decimal(self.amount) * Decimal(self.exchange_rate)).quantize(Decimal('0.000001'))
                else:
                    # Foreign/Gold → Foreign/Gold: need both prices in IRR
                    if not self.source_price_irr or not self.dest_price_irr:
                        raise ValidationError('Both source and destination currency IRR prices are required for cross-currency conversion.')
                    if self.source_price_irr <= 0 or self.dest_price_irr <= 0:
                        raise ValidationError('IRR prices must be positive values.')
                    # Convert via IRR: dest = amount * (src_price / dst_price)
                    self.destination_amount = (
                        Decimal(self.amount) * (Decimal(self.source_price_irr) / Decimal(self.dest_price_irr))
                    ).quantize(Decimal('0.000001'))
        
        # Profit transactions don't need a source account
        if self.kind not in [self.KIND_PROFIT_ACCOUNT, self.KIND_PROFIT_DEPOSIT_TO_ACCOUNT]:
            if not any([self.source_account]) or not any([self.destination_account, self.destination_deposit]):
                raise ValidationError('Transaction must have a source and a destination.')
        else:
            # Profit transactions only need a destination
            if not any([self.destination_account, self.destination_deposit]):
                raise ValidationError('Profit transaction must have a destination.')
        
        # Validate exchange rate numeric bounds when provided
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
            self.STATE_REJECTED: None,  # No further advancement
            self.STATE_WAITING_FINANCE_MANAGER: None,  # No further advancement (manual approval required)
            self.STATE_APPROVED_BY_FINANCE_MANAGER: self.STATE_WAITING_TREASURY,  # Finance manager approved, goes to treasury
            self.STATE_APPROVED_BY_SANDOGH: self.STATE_DONE,  # Sandogh approved, goes to done
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
        
        # Only workflow transactions (withdrawal, credit increase) need to be in STATE_DONE
        # Other transactions (account transfers, profit transfers) can apply immediately
        workflow_transactions = [self.KIND_WITHDRAWAL_REQUEST, self.KIND_CREDIT_INCREASE]
        if self.kind in workflow_transactions and self.state != self.STATE_DONE:
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
            # Account to deposit initial: money moves from account to deposit
            # The balance calculation will handle this automatically when applied=True
            self.applied = True
            self.save(update_fields=['applied'])
            return
        
        if self.kind == self.KIND_PROFIT_ACCOUNT:
            # Profit transactions add money to the destination account
            if not self.destination_account:
                return
            self.applied = True
            self.save(update_fields=['applied'])
            return
            
        if self.kind == self.KIND_PROFIT_DEPOSIT_TO_ACCOUNT:
            # Deposit profit transactions add money to the destination account
            if not self.destination_account:
                return
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

    def get_persian_created_at(self):
        """Return Persian date for created_at"""
        return get_persian_date_display(self.created_at)
    get_persian_created_at.short_description = 'تاریخ ایجاد'
    
    def get_persian_issued_at(self):
        """Return Persian date for issued_at"""
        return get_persian_date_display(self.issued_at)
    get_persian_issued_at.short_description = 'تاریخ صدور'
    
    def get_persian_scheduled_for(self):
        """Return Persian date for scheduled_for"""
        return get_persian_date_display(self.scheduled_for)
    get_persian_scheduled_for.short_description = 'تاریخ برنامه‌ریزی'

    def generate_transaction_code(self):
        """Generate a unique transaction code with requested format.

        Format: <Type>-<UserId>-<PersianDate>-<Seq>
        - Type: In | Out | Profit | Transfer | Transition
        - UserId: numeric user id
        - PersianDate: YYYYMMDD in Jalali (Asia/Tehran)
        - Seq: zero-padded 2-digit count for that user+kind on that Persian date
        """
        kind_prefix_map = {
            self.KIND_CREDIT_INCREASE: 'In',
            self.KIND_WITHDRAWAL_REQUEST: 'Out',
            self.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT: 'Transfer',
            self.KIND_ACCOUNT_TO_DEPOSIT_INITIAL: 'Transition',
            self.KIND_PROFIT_ACCOUNT: 'Profit',
            self.KIND_PROFIT_DEPOSIT_TO_ACCOUNT: 'Profit',
        }

        prefix = kind_prefix_map.get(self.kind, 'Txn')
        # Use 8-char UUID prefix assigned to each user
        try:
            user_part = (self.user.short_user_id if self.user else '00000000')
        except Exception:
            user_part = '00000000'

        tehran_tz = ZoneInfo('Asia/Tehran')
        issued_dt = self.issued_at or timezone.now()
        issued_local = issued_dt.astimezone(tehran_tz)
        jalali_date = JalaliDateTime(issued_local).strftime('%Y%m%d')

        # Calculate per-user-per-prefix sequence for that Persian date to avoid collisions
        # between different kinds that share the same prefix (e.g., both Profit kinds)
        base_code = f"{prefix}-{user_part}-{jalali_date}-"
        seq = (
            type(self).objects
            .filter(transaction_code__startswith=base_code)
            .count()
            + 1
        )
        return f"{base_code}{seq:02d}"

    def save(self, *args, **kwargs):
        """Override save to generate transaction code for new transactions and auto-apply done transactions"""
        if not self.transaction_code:
            self.transaction_code = self.generate_transaction_code()

        # Set initial state based on transaction kind (only if no state was explicitly set)
        if not self.pk:  # New transaction
            # Only set initial state if using the default state
            if self.state == self.STATE_WAITING_TREASURY:  # Default state
                if self.kind == self.KIND_WITHDRAWAL_REQUEST:
                    self.state = self.STATE_WAITING_FINANCE_MANAGER
                elif self.kind == self.KIND_CREDIT_INCREASE:
                    self.state = self.STATE_WAITING_TREASURY
                else:
                    # Auto-apply other transaction types (account transfers, profit transfers)
                    self.state = self.STATE_DONE

        # Ensure computed fields (e.g., destination_amount) are set before persisting
        try:
            self.clean()
        except Exception:
            # If clean raises because of transient form states, we skip here;
            # apply()/admin will re-run clean before any effects
            pass
        
        # Auto-apply transactions that are marked as done but not yet applied
        if self.state == self.STATE_DONE and not self.applied:
            super().save(*args, **kwargs)  # Save first to get the ID
            self.apply()  # Then apply the transaction
            return
        
        # Note: Auto-application of credit increase and withdrawal request transactions
        # has been removed to maintain compatibility with existing tests.
        # These transactions should only be applied when they reach STATE_DONE
        # through the normal workflow process.
        
        super().save(*args, **kwargs)

    def get_receipt_display(self):
        """Display receipt image in admin"""
        if self.receipt:
            from django.utils.html import format_html
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" style="max-width: 100px; max-height: 100px;" /></a>',
                self.receipt.url,
                self.receipt.url
            )
        return "-"
    get_receipt_display.short_description = 'Receipt'
    get_receipt_display.admin_order_field = 'receipt'

    def get_withdrawal_destination_display(self):
        """Display withdrawal destination (card or SHEBA) in admin"""
        if self.withdrawal_card_number:
            return f"Card: {self.withdrawal_card_number}"
        elif self.withdrawal_sheba_number:
            return f"SHEBA: {self.withdrawal_sheba_number}"
        return "-"
    get_withdrawal_destination_display.short_description = 'Withdrawal Destination'
    get_withdrawal_destination_display.admin_order_field = 'withdrawal_card_number'

    def __str__(self):
        amt = f"{self.amount:.2f}" if self.amount is not None else "0.00"
        return f"{self.kind}:{amt}"
