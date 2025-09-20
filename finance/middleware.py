from django.utils.translation import activate
from django.utils.deprecation import MiddlewareMixin


class AdminPersianMiddleware(MiddlewareMixin):
    """Force admin interface to use Persian locale"""
    
    def process_request(self, request):
        if request.path.startswith('/admin/'):
            activate('fa')
        return None
