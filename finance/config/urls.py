"""
Main URL configuration for Rahap Finance System.

This file consolidates all URL patterns including:
- Default Django admin
- Custom admin sites (Treasury, Operations, ReadOnly, Analytics)
- Supervisor admin
- API endpoints
- Swagger documentation
"""

from django.contrib import admin
from django.contrib.admin import AdminSite
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from ..admin.supervisor import register_supervisor_admin
from ..admin.sites import (
    treasury_admin_site,
    operation_admin_site,
    readonly_admin_site_1,
    readonly_admin_site_2
)
from ..views import UserViewSet, AccountViewSet, DepositViewSet, TransactionViewSet, get_user_accounts_for_admin
from rest_framework.routers import DefaultRouter


# Supervisor Admin Site
class SupervisorAdminSite(AdminSite):
    site_header = 'مدیریت نظارت'
    site_title = 'مدیریت نظارت'
    index_title = 'نظارت فقط خواندن'


supervisor_site = SupervisorAdminSite(name='supervisor_admin')
register_supervisor_admin(supervisor_site)

# API Router
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'accounts', AccountViewSet, basename='account')
router.register(r'deposits', DepositViewSet, basename='deposit')
router.register(r'transactions', TransactionViewSet, basename='transaction')

# Swagger configuration
schema_view = get_schema_view(
    openapi.Info(
        title="Rahap Finance API",
        default_version='v1',
        description="API documentation for Rahap Finance System",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@rahap.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Custom Admin Sites (must come before default admin to avoid catch-all pattern)
    path('admin/treasury/', treasury_admin_site.urls),
    path('admin/operations/', operation_admin_site.urls),
    path('admin/financial-overview/', readonly_admin_site_1.urls),
    path('admin/analytics/', readonly_admin_site_2.urls),
    path('admin/supervisor/', supervisor_site.urls),
    
    # Default Django Admin (must come last due to catch-all pattern)
    path('admin/', admin.site.urls),
    
    # API Endpoints
    path('api/', include(router.urls)),
    path('api/admin/get-user-accounts/', get_user_accounts_for_admin, name='get_user_accounts_for_admin'),
    
    # API Documentation
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
