from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from ..models import User
from .user_inlines import AccountInline, DepositInline, TransactionInline


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ('short_user_id_display', 'username', 'email', 'is_staff', 'is_superuser', 'is_active', 'get_persian_date_joined')
    list_display_links = ('short_user_id_display',)  # Make short user_id clickable
    search_fields = ('user_id', 'username', 'email')
    readonly_fields = ('user_id', 'date_joined', 'last_login')
    ordering = ('-date_joined',)  # Show newest users first
    
    # Add inlines to show user's financial data
    inlines = [AccountInline, DepositInline, TransactionInline]
    
    # Reorganize fieldsets to show user_id prominently
    fieldsets = (
        (None, {'fields': ('user_id', 'username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    # Add form - user_id is auto-generated, so don't show it
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser'),
        }),
    )
    
    def short_user_id_display(self, obj):
        """Display the first 8 characters of the user_id"""
        return obj.short_user_id
    short_user_id_display.short_description = 'User ID'
    short_user_id_display.admin_order_field = 'user_id'
    
    def get_queryset(self, request):
        """Optimize queryset for admin display"""
        return super().get_queryset(request).select_related()
