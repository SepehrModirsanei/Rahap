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
from django.urls import path, include
from finance import admin_supervisor as supervisor_admin


class SupervisorAdminSite(AdminSite):
    site_header = 'Supervisor Admin'
    site_title = 'Supervisor Admin'
    index_title = 'Read-only supervision'


supervisor_site = SupervisorAdminSite(name='supervisor_admin')
supervisor_admin.register(supervisor_site)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('supervisor-admin/', supervisor_site.urls),
    path('api/', include('finance.urls')),
]
