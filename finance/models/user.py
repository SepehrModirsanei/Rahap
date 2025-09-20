from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from .account import Account
from decimal import Decimal
import uuid
from ..utils import get_persian_date_display


class User(AbstractUser):
    # Unique ID for each user
    user_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, verbose_name=_('User ID'))
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
    
    def __str__(self):
        return f"User {str(self.user_id)[:8]}"
    
    @property
    def short_user_id(self):
        """Return the first 8 characters of the user_id"""
        return str(self.user_id)[:8]
    
    def get_persian_date_joined(self):
        """Return Persian date for date_joined"""
        return get_persian_date_display(self.date_joined)
    get_persian_date_joined.short_description = 'تاریخ عضویت'
    
    def get_persian_last_login(self):
        """Return Persian date for last_login"""
        return get_persian_date_display(self.last_login)
    get_persian_last_login.short_description = 'آخرین ورود'
    
    def save(self, *args, **kwargs):
        is_new = not self.pk
        super().save(*args, **kwargs)
        
        # Create default rial account for new users
        if is_new:
            Account.objects.create(
                user=self,
                name='حساب پایه',
                account_type=Account.ACCOUNT_TYPE_RIAL,
                initial_balance=Decimal('0.00'),
                monthly_profit_rate=Decimal('0.00')
            )
