from rest_framework import serializers
from ..models import Deposit


class DepositSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deposit
        fields = (
            'id', 'user', 'initial_balance', 'monthly_profit_rate',
            'last_profit_accrual_at', 'created_at', 'updated_at'
        )
        read_only_fields = ('user', 'last_profit_accrual_at', 'created_at', 'updated_at')
