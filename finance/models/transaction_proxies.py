from django.db import models
from django.utils.translation import gettext_lazy as _
from .transaction import Transaction


class WithdrawalRequest(Transaction):
    """Proxy model for withdrawal request transactions"""
    class Meta:
        proxy = True
        verbose_name = _('Withdrawal request')
        verbose_name_plural = _('Withdrawal requests')


class CreditIncrease(Transaction):
    """Proxy model for credit increase transactions"""
    class Meta:
        proxy = True
        verbose_name = _('Credit increase')
        verbose_name_plural = _('Credit increases')


class AccountTransfer(Transaction):
    """Proxy model for account-to-account transfer transactions"""
    class Meta:
        proxy = True
        verbose_name = _('Account transfer')
        verbose_name_plural = _('Account transfers')


class ProfitTransaction(Transaction):
    """Proxy model for profit-related transactions"""
    class Meta:
        proxy = True
        verbose_name = _('Profit transaction')
        verbose_name_plural = _('Profit transactions')


class DepositTransaction(Transaction):
    """Proxy model for account-to-deposit transactions"""
    class Meta:
        proxy = True
        verbose_name = _('Deposit transaction')
        verbose_name_plural = _('Deposit transactions')
