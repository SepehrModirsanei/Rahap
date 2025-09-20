from rest_framework import serializers
from ..models import Account


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = (
            'id', 'user', 'name', 'account_type', 'balance',
            'monthly_profit_rate', 'last_profit_accrual_at', 'created_at', 'updated_at'
        )
        read_only_fields = ('user', 'balance', 'last_profit_accrual_at', 'created_at', 'updated_at')
