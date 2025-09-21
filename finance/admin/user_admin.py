from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from ..models import User
from .user_inlines import AccountInline, DepositInline, TransactionInline


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ('short_user_id_display', 'username', 'full_name_display', 'national_id', 'phone_number', 'email', 'card_number_display', 'is_staff', 'is_superuser', 'is_active', 'get_persian_date_joined')
    list_display_links = ('short_user_id_display',)  # Make short user_id clickable
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined', 'last_login')
    search_fields = ('user_id', 'username', 'email', 'first_name', 'last_name', 'national_id', 'phone_number', 'card_number', 'sheba_number')
    readonly_fields = ('user_id', 'date_joined', 'last_login', 'get_persian_date_joined', 'get_persian_last_login', 'get_persian_birth_date')
    ordering = ('-date_joined',)  # Show newest users first
    
    # Add inlines to show user's financial data
    inlines = [AccountInline, DepositInline, TransactionInline]
    
    # Reorganize fieldsets to show user_id prominently
    fieldsets = (
        (None, {'fields': ('user_id', 'username', 'password')}),
        ('اطلاعات شخصی', {
            'fields': ('first_name', 'last_name', 'email', 'national_id', 'birth_date', 'phone_number'),
            'description': 'اطلاعات شخصی کاربر شامل نام، ایمیل، کد ملی، تاریخ تولد و شماره همراه'
        }),
        ('اطلاعات بانکی', {
            'fields': ('card_number', 'sheba_number'),
            'description': 'اطلاعات بانکی کاربر شامل شماره کارت و شماره شبا'
        }),
        ('وضعیت حساب', {
            'fields': ('is_active', 'is_staff', 'is_superuser'),
            'description': 'وضعیت فعال بودن حساب و دسترسی‌های کاربر'
        }),
        ('تاریخ‌های مهم', {
            'fields': ('get_persian_date_joined', 'get_persian_last_login', 'get_persian_birth_date'),
            'description': 'تاریخ عضویت، آخرین ورود و تاریخ تولد کاربر'
        }),
    )
    
    # Add form - user_id is auto-generated, so don't show it
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
            'description': 'اطلاعات ورود کاربر شامل نام کاربری و رمز عبور'
        }),
        ('اطلاعات شخصی', {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name', 'email', 'national_id', 'birth_date', 'phone_number'),
            'description': 'اطلاعات شخصی کاربر شامل نام، ایمیل، کد ملی، تاریخ تولد و شماره همراه'
        }),
        ('اطلاعات بانکی', {
            'classes': ('wide',),
            'fields': ('card_number', 'sheba_number'),
            'description': 'اطلاعات بانکی کاربر شامل شماره کارت و شماره شبا'
        }),
        ('وضعیت حساب', {
            'fields': ('is_active', 'is_staff', 'is_superuser'),
            'description': 'وضعیت فعال بودن حساب و دسترسی‌های کاربر'
        }),
    )
    
    def short_user_id_display(self, obj):
        """Display the first 8 characters of the user_id"""
        return obj.short_user_id
    short_user_id_display.short_description = 'User ID'
    short_user_id_display.admin_order_field = 'user_id'
    
    def full_name_display(self, obj):
        """Display full name"""
        return f"{obj.first_name} {obj.last_name}".strip() or "نام کامل"
    full_name_display.short_description = 'نام کامل'
    full_name_display.admin_order_field = 'first_name'
    
    def card_number_display(self, obj):
        """Display masked card number"""
        if obj.card_number:
            return f"****-****-****-{obj.card_number[-4:]}"
        return "ندارد"
    card_number_display.short_description = 'شماره کارت'
    card_number_display.admin_order_field = 'card_number'
    
    def get_queryset(self, request):
        """Optimize queryset for admin display"""
        return super().get_queryset(request).select_related()
