from django import forms

from .models import Transaction


class TransactionAdminForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = (
            'user', 'kind', 'amount', 'exchange_rate',
            'source_wallet', 'destination_wallet',
            'source_account', 'destination_account',
            'destination_deposit', 'state'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Default: make optional; model.clean will enforce correctly
        for name in ['source_wallet', 'destination_wallet', 'source_account', 'destination_account', 'destination_deposit', 'exchange_rate']:
            if name in self.fields:
                self.fields[name].required = False
        if 'state' in self.fields:
            self.fields['state'].required = True

    def clean(self):
        cleaned = super().clean()
        # Delegate validation to model.clean for consistency
        # Bind cleaned data to instance before calling clean()
        for field, value in cleaned.items():
            setattr(self.instance, field, value)
        self.instance.clean()
        return cleaned


