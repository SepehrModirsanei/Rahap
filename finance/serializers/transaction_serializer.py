from rest_framework import serializers
from ..models import Transaction, Account


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = (
            'id', 'user', 'source_account', 'destination_account', 'destination_deposit', 
            'amount', 'kind', 'exchange_rate', 'state', 'applied', 'issued_at', 'scheduled_for', 'created_at'
        )
        read_only_fields = ('user', 'applied', 'issued_at', 'created_at')

    def validate(self, attrs):
        kind = attrs.get('kind')
        source_account = attrs.get('source_account')
        destination_account = attrs.get('destination_account')
        destination_deposit = attrs.get('destination_deposit')
        exchange_rate = attrs.get('exchange_rate')

        if kind == Transaction.KIND_CREDIT_INCREASE:
            if not destination_account:
                raise serializers.ValidationError('destination_account is required for credit_increase')
        elif kind == Transaction.KIND_WITHDRAWAL_REQUEST:
            if not source_account:
                raise serializers.ValidationError('source_account is required for withdrawal_request')
        elif kind == Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT:
            if not (source_account and destination_account):
                raise serializers.ValidationError('source_account and destination_account are required for account_to_account')
            if source_account.account_type != destination_account.account_type and not exchange_rate:
                raise serializers.ValidationError('exchange_rate required for cross-currency transfers')
        elif kind == Transaction.KIND_ACCOUNT_TO_DEPOSIT_INITIAL:
            if not (source_account and destination_deposit):
                raise serializers.ValidationError('source_account and destination_deposit are required for account_to_deposit_initial')
        return attrs
