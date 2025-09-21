from django.db import models
from django.utils.translation import gettext_lazy as _
from .transaction import Transaction


class WithdrawalRequest(Transaction):
    """Proxy model for withdrawal request transactions"""
    class Meta:
        proxy = True
        verbose_name = _('درخواست برداشت')
        verbose_name_plural = _('درخواست‌های برداشت')


class CreditIncrease(Transaction):
    """Proxy model for credit increase transactions"""
    class Meta:
        proxy = True
        verbose_name = _('افزایش اعتبار')
        verbose_name_plural = _('افزایش‌های اعتبار')


class AccountTransfer(Transaction):
    """Proxy model for account-to-account transfer transactions"""
    class Meta:
        proxy = True
        verbose_name = _('انتقال حساب')
        verbose_name_plural = _('انتقال‌های حساب')


class ProfitTransaction(Transaction):
    """Proxy model for profit-related transactions"""
    class Meta:
        proxy = True
        verbose_name = _('تراکنش سود')
        verbose_name_plural = _('تراکنش‌های سود')


class DepositTransaction(Transaction):
    """Proxy model for account-to-deposit transactions"""
    class Meta:
        proxy = True
        verbose_name = _('تراکنش سپرده')
        verbose_name_plural = _('تراکنش‌های سپرده')
