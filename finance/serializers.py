from rest_framework import serializers

from .models import User, Wallet, Account, Deposit, Transaction


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ('id', 'user', 'balance', 'currency', 'created_at', 'updated_at')
        read_only_fields = ('user', 'balance', 'created_at', 'updated_at')


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = (
            'id', 'user', 'wallet', 'name', 'account_type', 'balance',
            'monthly_profit_rate', 'last_profit_accrual_at', 'created_at', 'updated_at'
        )
        read_only_fields = ('user', 'balance', 'last_profit_accrual_at', 'created_at', 'updated_at')


class DepositSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deposit
        fields = (
            'id', 'user', 'wallet', 'amount', 'monthly_profit_rate',
            'last_profit_accrual_at', 'created_at', 'updated_at'
        )
        read_only_fields = ('user', 'last_profit_accrual_at', 'created_at', 'updated_at')


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = (
            'id', 'user', 'source_wallet', 'destination_wallet', 'source_account',
            'destination_account', 'destination_deposit', 'amount', 'kind', 'exchange_rate', 'applied', 'created_at'
        )
        read_only_fields = ('user', 'applied', 'created_at')

    def validate(self, attrs):
        kind = attrs.get('kind')
        source_wallet = attrs.get('source_wallet')
        destination_wallet = attrs.get('destination_wallet')
        source_account = attrs.get('source_account')
        destination_account = attrs.get('destination_account')
        destination_deposit = attrs.get('destination_deposit')
        exchange_rate = attrs.get('exchange_rate')

        if kind == Transaction.KIND_ADD_TO_WALLET:
            if not destination_wallet:
                raise serializers.ValidationError('destination_wallet is required for add_to_wallet')
        elif kind == Transaction.KIND_REMOVE_FROM_WALLET:
            if not source_wallet:
                raise serializers.ValidationError('source_wallet is required for remove_from_wallet')
        elif kind == Transaction.KIND_WALLET_TO_DEPOSIT_INITIAL:
            if not (source_wallet and destination_deposit):
                raise serializers.ValidationError('source_wallet and destination_deposit are required for wallet_to_deposit_initial')
        elif kind == Transaction.KIND_TRANSFER_ACCOUNT_TO_WALLET:
            if not (source_account and destination_wallet):
                raise serializers.ValidationError('source_account and destination_wallet required')
            if source_account.account_type != Account.ACCOUNT_TYPE_RIAL and not exchange_rate:
                raise serializers.ValidationError('exchange_rate required for non-rial account to wallet')
        elif kind == Transaction.KIND_TRANSFER_WALLET_TO_ACCOUNT:
            if not (source_wallet and destination_account):
                raise serializers.ValidationError('source_wallet and destination_account required')
            if destination_account.account_type != Account.ACCOUNT_TYPE_RIAL and not exchange_rate:
                raise serializers.ValidationError('exchange_rate required for wallet to non-rial account')
        return attrs


