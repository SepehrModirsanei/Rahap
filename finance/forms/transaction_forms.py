from django import forms

from ..models import Transaction, Account
from ..widgets.persian_date_picker import PersianDateTimePickerWidget


class TransactionAdminForm(forms.ModelForm):
    scheduled_for = forms.DateTimeField(
        required=False,
        widget=PersianDateTimePickerWidget(),
        # Accept only ISO Gregorian; the widget converts Jalali -> ISO before submit
        input_formats=['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M']
    )
    class Meta:
        model = Transaction
        fields = (
            'user', 'kind', 'amount', 'exchange_rate',
            'source_account', 'destination_account',
            'destination_deposit', 'state', 'scheduled_for',
            'receipt', 'withdrawal_card_number', 'withdrawal_sheba_number',
            'admin_opinion', 'treasurer_opinion', 'finance_manager_opinion'
        )
        widgets = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Default: make optional; model.clean will enforce correctly
        for name in ['source_account', 'destination_account', 'destination_deposit', 'exchange_rate']:
            if name in self.fields:
                self.fields[name].required = False
        if 'state' in self.fields:
            self.fields['state'].required = True

        # Filter accounts based on transaction type and user
        self._filter_account_choices()

    def _filter_account_choices(self):
        """Filter account choices based on transaction type and user"""
        # Get the current transaction kind and user
        kind = self.data.get('kind') if self.data else (self.instance.kind if self.instance.pk else None)
        user_id = self.data.get('user') if self.data else (self.instance.user_id if self.instance.pk else None)
        
        # If we have a user, filter accounts to that user
        if user_id:
            user_accounts = Account.objects.filter(user_id=user_id)
            
            # For credit increase and withdrawal request, only show rial accounts
            if kind in [Transaction.KIND_CREDIT_INCREASE, Transaction.KIND_WITHDRAWAL_REQUEST]:
                rial_accounts = user_accounts.filter(account_type=Account.ACCOUNT_TYPE_RIAL)
                
                if kind == Transaction.KIND_CREDIT_INCREASE:
                    # Credit increase uses destination_account
                    if 'destination_account' in self.fields:
                        self.fields['destination_account'].queryset = rial_accounts
                    if 'source_account' in self.fields:
                        self.fields['source_account'].queryset = Account.objects.none()
                elif kind == Transaction.KIND_WITHDRAWAL_REQUEST:
                    # Withdrawal request uses source_account
                    if 'source_account' in self.fields:
                        self.fields['source_account'].queryset = rial_accounts
                    if 'destination_account' in self.fields:
                        self.fields['destination_account'].queryset = Account.objects.none()
            else:
                # For other transaction types, show all user accounts
                if 'source_account' in self.fields:
                    self.fields['source_account'].queryset = user_accounts
                    self.fields['source_account'].label_from_instance = self._account_label_from_instance
                if 'destination_account' in self.fields:
                    self.fields['destination_account'].queryset = user_accounts
                    self.fields['destination_account'].label_from_instance = self._account_label_from_instance
        else:
            # No user selected, show all accounts (will be filtered by validation)
            if 'source_account' in self.fields:
                self.fields['source_account'].queryset = Account.objects.all()
                self.fields['source_account'].label_from_instance = self._account_label_from_instance
            if 'destination_account' in self.fields:
                self.fields['destination_account'].queryset = Account.objects.all()
                self.fields['destination_account'].label_from_instance = self._account_label_from_instance

    def _account_label_from_instance(self, obj):
        """Custom label for account fields"""
        if obj:
            return f"{obj.name} ({obj.get_account_type_display()})"
        return ""

    def clean(self):
        cleaned = super().clean()
        
        # Check if exchange rate is required for account-to-account transactions
        kind = cleaned.get('kind')
        source_account = cleaned.get('source_account')
        destination_account = cleaned.get('destination_account')
        exchange_rate = cleaned.get('exchange_rate')
        
        if (kind == Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT and 
            source_account and destination_account and 
            source_account.account_type != destination_account.account_type):
            if not exchange_rate:
                self.add_error('exchange_rate', 'Exchange rate is required for cross-currency account transfers.')
        
        # Delegate validation to model.clean for consistency
        # Bind cleaned data to instance before calling clean()
        for field, value in cleaned.items():
            setattr(self.instance, field, value)
        self.instance.clean()
        return cleaned


