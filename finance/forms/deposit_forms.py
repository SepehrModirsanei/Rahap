from django import forms
from ..models import Deposit


class DepositAdminForm(forms.ModelForm):
    """Custom form for deposit admin - simplified without funding source"""
    
    class Meta:
        model = Deposit
        fields = '__all__'
