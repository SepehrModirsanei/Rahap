"""
URL configuration for rahap_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib import admin as django_admin
from django.contrib.admin import AdminSite
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from finance import admin_supervisor as supervisor_admin


class SupervisorAdminSite(AdminSite):
    site_header = 'Supervisor Admin'
    site_title = 'Supervisor Admin'
    index_title = 'Read-only supervision'


supervisor_site = SupervisorAdminSite(name='supervisor_admin')
supervisor_admin.register(supervisor_site)

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
    path('admin/', admin.site.urls),
    path('supervisor-admin/', supervisor_site.urls),
    path('api/', include('finance.urls')),
    
    # Swagger URLs
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
