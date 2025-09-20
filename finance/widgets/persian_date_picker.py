"""
Persian Date Picker Widget for Django Admin
"""
from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _


class PersianDatePickerWidget(forms.DateInput):
    """Persian date picker widget for Django admin"""
    
    class Media:
        css = {
            'all': (
                'https://cdn.jsdelivr.net/npm/persian-datepicker@1.2.0/dist/css/persian-datepicker.min.css',
            )
        }
        js = (
            'https://cdn.jsdelivr.net/npm/persian-datepicker@1.2.0/dist/js/persian-datepicker.min.js',
        )
    
    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'persian-datepicker',
            'data-date-format': 'YYYY/MM/DD',
            'data-view-mode': 'day',
            'data-min-view-mode': 'day',
            'data-auto-close': 'true',
            'data-position': 'bottom',
            'data-language': 'fa',
            'data-view-mode': 'day',
            'data-min-view-mode': 'day',
            'data-auto-close': 'true',
            'data-position': 'bottom',
            'data-language': 'fa',
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)
    
    def render(self, name, value, attrs=None, renderer=None):
        widget_html = super().render(name, value, attrs, renderer)
        
        # Add JavaScript to initialize Persian date picker
        script = f"""
        <script>
        document.addEventListener('DOMContentLoaded', function() {{
            var dateInput = document.querySelector('input[name="{name}"]');
            if (dateInput) {{
                $(dateInput).persianDatepicker({{
                    format: 'YYYY/MM/DD',
                    viewMode: 'day',
                    minViewMode: 'day',
                    autoClose: true,
                    position: 'bottom',
                    language: 'fa',
                    calendar: {{
                        persian: {{
                            locale: 'fa',
                            showHint: true,
                            leapYearMode: 'algorithmic'
                        }}
                    }}
                }});
            }}
        }});
        </script>
        """
        
        return mark_safe(widget_html + script)


class PersianDateTimePickerWidget(forms.DateTimeInput):
    """Persian date and time picker widget for Django admin"""
    
    class Media:
        css = {
            'all': (
                'https://cdn.jsdelivr.net/npm/persian-datepicker@1.2.0/dist/css/persian-datepicker.min.css',
            )
        }
        js = (
            'https://cdn.jsdelivr.net/npm/persian-datepicker@1.2.0/dist/js/persian-datepicker.min.js',
        )
    
    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'persian-datetimepicker',
            'data-date-format': 'YYYY/MM/DD HH:mm',
            'data-view-mode': 'day',
            'data-min-view-mode': 'day',
            'data-auto-close': 'true',
            'data-position': 'bottom',
            'data-language': 'fa',
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)
    
    def render(self, name, value, attrs=None, renderer=None):
        widget_html = super().render(name, value, attrs, renderer)
        
        # Add JavaScript to initialize Persian date and time picker
        script = f"""
        <script>
        document.addEventListener('DOMContentLoaded', function() {{
            var dateInput = document.querySelector('input[name="{name}"]');
            if (dateInput) {{
                $(dateInput).persianDatepicker({{
                    format: 'YYYY/MM/DD HH:mm',
                    viewMode: 'day',
                    minViewMode: 'day',
                    autoClose: true,
                    position: 'bottom',
                    language: 'fa',
                    timePicker: {{
                        enabled: true,
                        meridiem: {{
                            enabled: true
                        }}
                    }},
                    calendar: {{
                        persian: {{
                            locale: 'fa',
                            showHint: true,
                            leapYearMode: 'algorithmic'
                        }}
                    }}
                }});
            }}
        }});
        </script>
        """
        
        return mark_safe(widget_html + script)
