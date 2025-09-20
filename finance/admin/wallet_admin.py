from django.contrib import admin
from ..models import Wallet, Transaction


class ReadOnlyTransactionInline(admin.TabularInline):
    model = Transaction
    extra = 0
    can_delete = False
    readonly_fields = ('user', 'kind', 'amount', 'exchange_rate', 'source_wallet', 'destination_wallet', 'source_account', 'destination_account', 'destination_deposit', 'applied', 'created_at')
    fields = readonly_fields

    def has_add_permission(self, request, obj=None):
        return False


class WalletTxnOutInline(ReadOnlyTransactionInline):
    fk_name = 'source_wallet'


class WalletTxnInInline(ReadOnlyTransactionInline):
    fk_name = 'destination_wallet'


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'initial_balance', 'currency', 'created_at')
    search_fields = ('user__username',)
    inlines = [WalletTxnOutInline, WalletTxnInInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'initial_balance', 'currency'),
            'description': 'Initial balance is the starting amount for this wallet'
        }),
    )
