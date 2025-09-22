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
                'admin/css/persian-datepicker.min.css',
            )
        }
        js = (
            'admin/js/jquery-3.6.0.min.js',
            'admin/js/persian-date.min.js',
            'admin/js/persian-datepicker.min.js',
        )
    
    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'vDateField',
            'data-date-format': 'YYYY/MM/DD',
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
            var input = document.querySelector('input[name="{name}"]');
            if (input && typeof $ !== 'undefined') {{
                $(input).persianDatepicker({{
                    format: 'YYYY/MM/DD',
                    autoClose: true,
                    initialValue: false,
                    persianDigit: true,
                    altField: $(input),
                    altFormat: 'YYYY-MM-DD',
                    calendar: {{
                        persian: {{
                            locale: 'fa'
                        }}
                    }},
                    onSelect: function(unix) {{
                        var date = new persianDate(unix).toCalendar('gregorian');
                        $(this.altField).val(date.format('YYYY-MM-DD'));
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
                'admin/css/persian-datepicker.min.css',
            )
        }
        js = (
            'admin/js/jquery-3.6.0.min.js',
            'admin/js/persian-date.min.js',
            'admin/js/persian-datepicker.min.js',
        )
    
    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'vDateTimeInput',
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
            var input = document.querySelector('input[name="{name}"]');
            if (input && typeof $ !== 'undefined') {{
                $(input).persianDatepicker({{
                    format: 'YYYY/MM/DD HH:mm:ss',
                    autoClose: true,
                    initialValue: false,
                    persianDigit: true,
                    altField: $(input),
                    altFormat: 'YYYY-MM-DD HH:mm:ss',
                    calendar: {{
                        persian: {{
                            locale: 'fa'
                        }}
                    }},
                    timePicker: {{
                        enabled: true,
                        meridian: {{
                            enabled: false
                        }}
                    }},
                    onSelect: function(unix) {{
                        var date = new persianDate(unix).toCalendar('gregorian');
                        $(this.altField).val(date.format('YYYY-MM-DD HH:mm:ss'));
                    }}
                }});
            }}
        }});
        </script>
        """
        
        return mark_safe(widget_html + script)
