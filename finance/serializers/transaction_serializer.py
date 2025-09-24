from rest_framework import serializers
from ..models import Transaction, Account


class TransactionSerializer(serializers.ModelSerializer):
    bank_destination = serializers.CharField(write_only=True, required=False, allow_blank=True)
    saved_bank_info = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Transaction
        fields = (
            'id', 'user', 'source_account', 'destination_account', 'destination_deposit', 
            'amount', 'kind', 'exchange_rate', 'state', 'applied', 'issued_at', 'scheduled_for', 'created_at',
            'admin_opinion', 'treasurer_opinion', 'finance_manager_opinion', 'user_comment', 'transaction_code',
            'bank_destination', 'saved_bank_info'
        )
        read_only_fields = ('user', 'applied', 'issued_at', 'created_at', 'admin_opinion', 'treasurer_opinion', 'finance_manager_opinion', 'transaction_code', 'saved_bank_info')

    def get_saved_bank_info(self, obj):
        user = obj.user if isinstance(obj, Transaction) else self.context.get('request').user
        if not user or not getattr(user, 'id', None):
            return {}
        return {
            'card_number': user.card_number or '',
            'sheba_number': user.sheba_number or ''
        }

    def validate(self, attrs):
        # Map bank_destination into withdrawal fields if provided
        dest = attrs.pop('bank_destination', None)
        if dest:
            if dest.startswith('card:'):
                attrs['withdrawal_card_number'] = dest.split(':', 1)[1]
                attrs['withdrawal_sheba_number'] = ''
            elif dest.startswith('sheba:'):
                attrs['withdrawal_sheba_number'] = dest.split(':', 1)[1]
                attrs['withdrawal_card_number'] = ''
        
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
