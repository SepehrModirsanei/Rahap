from django import forms
from ..models import Transaction, Account, Deposit
from ..widgets.persian_date_picker import PersianDatePickerWidget, PersianDateTimePickerWidget


class WithdrawalRequestForm(forms.ModelForm):
    """Form specifically for withdrawal request transactions"""
    class Meta:
        model = Transaction
        fields = ('user', 'source_account', 'amount', 'state', 'scheduled_for', 'withdrawal_card_number', 'withdrawal_sheba_number')
        widgets = {
            'scheduled_for': PersianDateTimePickerWidget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-set the kind to withdrawal_request
        self.instance.kind = Transaction.KIND_WITHDRAWAL_REQUEST
        
        # Make source_account required
        self.fields['source_account'].required = True
        self.fields['state'].required = True
        
        # Filter to only rial accounts for the selected user
        self._filter_account_choices()

    def _filter_account_choices(self):
        """Filter to only rial accounts for the selected user"""
        user_id = self.data.get('user') if self.data else (self.instance.user_id if self.instance.pk else None)
        
        if user_id:
            rial_accounts = Account.objects.filter(
                user_id=user_id, 
                account_type=Account.ACCOUNT_TYPE_RIAL
            )
            self.fields['source_account'].queryset = rial_accounts
        else:
            self.fields['source_account'].queryset = Account.objects.none()

    def clean(self):
        cleaned = super().clean()
        # Delegate validation to model.clean
        for field, value in cleaned.items():
            setattr(self.instance, field, value)
        self.instance.clean()
        return cleaned


class CreditIncreaseForm(forms.ModelForm):
    """Form specifically for credit increase transactions"""
    class Meta:
        model = Transaction
        fields = ('user', 'destination_account', 'amount', 'state', 'scheduled_for', 'receipt')
        widgets = {
            'scheduled_for': PersianDateTimePickerWidget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-set the kind to credit_increase
        self.instance.kind = Transaction.KIND_CREDIT_INCREASE
        
        # Make destination_account required
        self.fields['destination_account'].required = True
        self.fields['state'].required = True
        
        # Filter to only rial accounts for the selected user
        self._filter_account_choices()

    def _filter_account_choices(self):
        """Filter to only rial accounts for the selected user"""
        user_id = self.data.get('user') if self.data else (self.instance.user_id if self.instance.pk else None)
        
        if user_id:
            rial_accounts = Account.objects.filter(
                user_id=user_id, 
                account_type=Account.ACCOUNT_TYPE_RIAL
            )
            self.fields['destination_account'].queryset = rial_accounts
        else:
            # Initially show no accounts - will be populated by JavaScript
            self.fields['destination_account'].queryset = Account.objects.none()

    def clean(self):
        cleaned = super().clean()
        # Delegate validation to model.clean
        for field, value in cleaned.items():
            setattr(self.instance, field, value)
        self.instance.clean()
        return cleaned


class AccountTransferForm(forms.ModelForm):
    """Form specifically for account-to-account transfer transactions"""
    class Meta:
        model = Transaction
        fields = ('user', 'source_account', 'destination_account', 'amount', 'exchange_rate', 'state', 'scheduled_for')
        widgets = {
            'scheduled_for': PersianDateTimePickerWidget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-set the kind to account_to_account
        self.instance.kind = Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT
        
        # Make both accounts required
        self.fields['source_account'].required = True
        self.fields['destination_account'].required = True
        self.fields['state'].required = True
        
        # Filter accounts for the selected user
        self._filter_account_choices()

    def _filter_account_choices(self):
        """Filter accounts for the selected user"""
        user_id = self.data.get('user') if self.data else (self.instance.user_id if self.instance.pk else None)
        
        if user_id:
            user_accounts = Account.objects.filter(user_id=user_id)
            self.fields['source_account'].queryset = user_accounts
            self.fields['destination_account'].queryset = user_accounts
        else:
            self.fields['source_account'].queryset = Account.objects.none()
            self.fields['destination_account'].queryset = Account.objects.none()

    def clean(self):
        cleaned = super().clean()
        
        # Check if exchange rate is required for cross-currency transfers
        source_account = cleaned.get('source_account')
        destination_account = cleaned.get('destination_account')
        exchange_rate = cleaned.get('exchange_rate')
        
        if (source_account and destination_account and 
            source_account.account_type != destination_account.account_type):
            if not exchange_rate:
                self.add_error('exchange_rate', 'Exchange rate is required for cross-currency account transfers.')
        
        # Delegate validation to model.clean
        for field, value in cleaned.items():
            setattr(self.instance, field, value)
        self.instance.clean()
        return cleaned


class ProfitTransactionForm(forms.ModelForm):
    """Form specifically for profit-related transactions"""
    class Meta:
        model = Transaction
        fields = ('user', 'destination_account', 'amount', 'state', 'scheduled_for')
        widgets = {
            'scheduled_for': PersianDateTimePickerWidget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-set the kind to profit_account (can be changed if needed)
        self.instance.kind = Transaction.KIND_PROFIT_ACCOUNT
        
        # Make destination_account required
        self.fields['destination_account'].required = True
        self.fields['state'].required = True
        
        # Filter accounts for the selected user
        self._filter_account_choices()

    def _filter_account_choices(self):
        """Filter accounts for the selected user"""
        user_id = self.data.get('user') if self.data else (self.instance.user_id if self.instance.pk else None)
        
        if user_id:
            user_accounts = Account.objects.filter(user_id=user_id)
            self.fields['destination_account'].queryset = user_accounts
        else:
            self.fields['destination_account'].queryset = Account.objects.none()

    def clean(self):
        cleaned = super().clean()
        # Delegate validation to model.clean
        for field, value in cleaned.items():
            setattr(self.instance, field, value)
        self.instance.clean()
        return cleaned


class DepositTransactionForm(forms.ModelForm):
    """Form specifically for account-to-deposit transactions"""
    class Meta:
        model = Transaction
        fields = ('user', 'source_account', 'destination_deposit', 'amount', 'state', 'scheduled_for')
        widgets = {
            'scheduled_for': PersianDateTimePickerWidget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-set the kind to account_to_deposit_initial
        self.instance.kind = Transaction.KIND_ACCOUNT_TO_DEPOSIT_INITIAL
        
        # Make both source_account and destination_deposit required
        self.fields['source_account'].required = True
        self.fields['destination_deposit'].required = True
        self.fields['state'].required = True
        
        # Filter accounts and deposits for the selected user
        self._filter_choices()

    def _filter_choices(self):
        """Filter accounts and deposits for the selected user"""
        user_id = self.data.get('user') if self.data else (self.instance.user_id if self.instance.pk else None)
        
        if user_id:
            user_accounts = Account.objects.filter(user_id=user_id)
            user_deposits = Deposit.objects.filter(user_id=user_id)
            self.fields['source_account'].queryset = user_accounts
            self.fields['destination_deposit'].queryset = user_deposits
        else:
            self.fields['source_account'].queryset = Account.objects.none()
            self.fields['destination_deposit'].queryset = Deposit.objects.none()

    def clean(self):
        cleaned = super().clean()
        # Delegate validation to model.clean
        for field, value in cleaned.items():
            setattr(self.instance, field, value)
        self.instance.clean()
        return cleaned
