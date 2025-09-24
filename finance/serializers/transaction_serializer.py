from rest_framework import serializers
from ..models import Transaction, Account
from ..services.quote_service import QuoteService


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
            # Auto-quote for API usage if cross-currency and rates not provided
            if source_account.account_type != destination_account.account_type:
                amount = attrs.get('amount')
                if amount is None:
                    raise serializers.ValidationError('amount is required for cross-currency transfers')
                quote = QuoteService.compute_destination_amount(
                    float(amount),
                    source_account.account_type,
                    destination_account.account_type,
                )
                # If rial<->fx, we set exchange_rate; if fx<->fx we set source/dest IRR prices
                if quote.get('destination_amount') is None:
                    # If still none, require explicit exchange info
                    if destination_account.account_type == Account.ACCOUNT_TYPE_RIAL or source_account.account_type == Account.ACCOUNT_TYPE_RIAL:
                        if not exchange_rate:
                            raise serializers.ValidationError('exchange_rate required for rial cross-currency when quote unavailable')
                    else:
                        if not (attrs.get('source_price_irr') and attrs.get('dest_price_irr')):
                            raise serializers.ValidationError('source_price_irr and dest_price_irr required for FX to FX when quote unavailable')
                else:
                    if destination_account.account_type == Account.ACCOUNT_TYPE_RIAL or source_account.account_type == Account.ACCOUNT_TYPE_RIAL:
                        if quote.get('exchange_rate'):
                            attrs['exchange_rate'] = quote['exchange_rate']
                    else:
                        if quote.get('source_price_irr'):
                            attrs['source_price_irr'] = quote['source_price_irr']
                        if quote.get('dest_price_irr'):
                            attrs['dest_price_irr'] = quote['dest_price_irr']
        elif kind == Transaction.KIND_ACCOUNT_TO_DEPOSIT_INITIAL:
            if not (source_account and destination_deposit):
                raise serializers.ValidationError('source_account and destination_deposit are required for account_to_deposit_initial')
        return attrs
