from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .admin_sites import (
    treasury_admin_site,
    operation_admin_site, 
    readonly_admin_site_1,
    readonly_admin_site_2
)

from .views import UserViewSet, AccountViewSet, DepositViewSet, TransactionViewSet, get_user_accounts_for_admin


router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'accounts', AccountViewSet, basename='account')
router.register(r'deposits', DepositViewSet, basename='deposit')
router.register(r'transactions', TransactionViewSet, basename='transaction')


urlpatterns = [
    path('', include(router.urls)),
    # Admin Panel URLs
    path('admin/treasury/', treasury_admin_site.urls),
    path('admin/operations/', operation_admin_site.urls),
    path('admin/financial-overview/', readonly_admin_site_1.urls),
    path('admin/analytics/', readonly_admin_site_2.urls),
    # Admin helper endpoints
    path('admin/get-user-accounts/', get_user_accounts_for_admin, name='get_user_accounts_for_admin'),
]


