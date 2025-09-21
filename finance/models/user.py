from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from .account import Account
from decimal import Decimal
import uuid
from ..utils import get_persian_date_display


class User(AbstractUser):
    # Unique ID for each user
    user_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, verbose_name=_('User ID'))
    
    # Personal Information
    national_id = models.CharField(max_length=10, blank=True, verbose_name=_('کد ملی'), help_text=_('10-digit national ID'))
    birth_date = models.DateField(null=True, blank=True, verbose_name=_('تاریخ تولد'))
    email = models.EmailField(blank=True, verbose_name=_('ایمیل'))
    phone_number = models.CharField(max_length=11, blank=True, verbose_name=_('شماره همراه'), help_text=_('11-digit phone number'))
    
    # Bank Information
    card_number = models.CharField(max_length=16, blank=True, verbose_name=_('شماره کارت'), help_text=_('16-digit card number'))
    sheba_number = models.CharField(max_length=24, blank=True, verbose_name=_('شماره شبا'), help_text=_('24-digit IBAN number'))
    
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
    
    def get_persian_birth_date(self):
        """Return Persian date for birth_date"""
        return get_persian_date_display(self.birth_date)
    get_persian_birth_date.short_description = 'تاریخ تولد'
    
    def clean(self):
        """Validate user data"""
        super().clean()
        
        # Validate national ID (should be 10 digits)
        if self.national_id and not self.national_id.isdigit():
            raise ValidationError({'national_id': 'کد ملی باید فقط شامل اعداد باشد'})
        if self.national_id and len(self.national_id) != 10:
            raise ValidationError({'national_id': 'کد ملی باید 10 رقم باشد'})
        
        # Validate phone number (should be 11 digits starting with 09)
        if self.phone_number and not self.phone_number.isdigit():
            raise ValidationError({'phone_number': 'شماره همراه باید فقط شامل اعداد باشد'})
        if self.phone_number and len(self.phone_number) != 11:
            raise ValidationError({'phone_number': 'شماره همراه باید 11 رقم باشد'})
        if self.phone_number and not self.phone_number.startswith('09'):
            raise ValidationError({'phone_number': 'شماره همراه باید با 09 شروع شود'})
        
        # Validate card number (should be 16 digits)
        if self.card_number and not self.card_number.isdigit():
            raise ValidationError({'card_number': 'شماره کارت باید فقط شامل اعداد باشد'})
        if self.card_number and len(self.card_number) != 16:
            raise ValidationError({'card_number': 'شماره کارت باید 16 رقم باشد'})
        
        # Validate SHEBA number (should be 24 characters, starting with IR)
        if self.sheba_number and not self.sheba_number.startswith('IR'):
            raise ValidationError({'sheba_number': 'شماره شبا باید با IR شروع شود'})
        if self.sheba_number and len(self.sheba_number) != 24:
            raise ValidationError({'sheba_number': 'شماره شبا باید 24 کاراکتر باشد'})
    
    def save(self, *args, **kwargs):
        self.clean()
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
