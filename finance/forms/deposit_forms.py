from django import forms
from ..models import Deposit, Account


class DepositAdminForm(forms.ModelForm):
    """Custom form for deposit admin with rial account filtering"""
    
    class Meta:
        model = Deposit
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter funding_account to only show rial accounts
        if 'funding_account' in self.fields:
            # Get the user from the instance or from the form data
            user = None
            if self.instance and self.instance.pk:
                user = self.instance.user
            elif 'user' in self.data:
                try:
                    from ..models import User
                    user = User.objects.get(pk=self.data['user'])
                except (User.DoesNotExist, ValueError):
                    pass
            
            if user:
                # Filter to only rial accounts for this user
                rial_accounts = Account.objects.filter(
                    user=user,
                    account_type=Account.ACCOUNT_TYPE_RIAL
                )
                self.fields['funding_account'].queryset = rial_accounts
            else:
                # No user selected, show no accounts
                self.fields['funding_account'].queryset = Account.objects.none()
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Additional validation for rial account requirement
        funding_source = cleaned_data.get('funding_source')
        funding_account = cleaned_data.get('funding_account')
        
        if funding_source == Deposit.FUNDING_SOURCE_TRANSACTION and funding_account:
            if funding_account.account_type != Account.ACCOUNT_TYPE_RIAL:
                self.add_error('funding_account', 'Funding account must be a rial account.')
        
        return cleaned_data
