from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import UserViewSet, WalletViewSet, AccountViewSet, DepositViewSet, TransactionViewSet


router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'wallets', WalletViewSet, basename='wallet')
router.register(r'accounts', AccountViewSet, basename='account')
router.register(r'deposits', DepositViewSet, basename='deposit')
router.register(r'transactions', TransactionViewSet, basename='transaction')


urlpatterns = [
    path('', include(router.urls)),
]


