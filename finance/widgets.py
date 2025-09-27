"""
Custom widgets for Persian date handling
"""
from django import forms
from persiantools.jdatetime import JalaliDateTime, JalaliDate
from persiantools import digits


class PersianDateWidget(forms.DateInput):
    """Widget for Persian date input"""
    template_name = 'admin/widgets/persian_date.html'
    
    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'persian-date-input',
            'placeholder': 'YYYY/MM/DD'
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)
    
    def format_value(self, value):
        """Convert datetime to Persian date string"""
        if value:
            if isinstance(value, str):
                return value
            try:
                jalali = JalaliDateTime(value)
                return jalali.strftime('%Y/%m/%d')
            except:
                return str(value)
        return ''


class PersianDateTimeWidget(forms.DateTimeInput):
    """Widget for Persian datetime input"""
    template_name = 'admin/widgets/persian_datetime.html'
    
    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'persian-datetime-input',
            'placeholder': 'YYYY/MM/DD HH:MM'
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)
    
    def format_value(self, value):
        """Convert datetime to Persian datetime string"""
        if value:
            if isinstance(value, str):
                return value
            try:
                jalali = JalaliDateTime(value)
                return jalali.strftime('%Y/%m/%d %H:%M')
            except:
                return str(value)
        return ''


class PersianDateField(forms.DateField):
    """Custom field for Persian date input"""
    widget = PersianDateWidget
    
    def to_python(self, value):
        """Convert Persian date string to Python date"""
        if not value:
            return None
        
        try:
            # Convert Persian digits to English
            value = digits.en_to_fa(value)
            
            # Parse Persian date (YYYY/MM/DD)
            year, month, day = map(int, value.split('/'))
            
            # Convert to Gregorian
            jalali_date = JalaliDate(year, month, day)
            gregorian_date = jalali_date.to_gregorian()
            
            return gregorian_date
        except (ValueError, TypeError):
            raise forms.ValidationError('Enter a valid Persian date (YYYY/MM/DD)')


class PersianDateTimeField(forms.DateTimeField):
    """Custom field for Persian datetime input"""
    widget = PersianDateTimeWidget
    
    def to_python(self, value):
        """Convert Persian datetime string to Python datetime"""
        if not value:
            return None
        
        try:
            # Convert Persian digits to English
            value = digits.en_to_fa(value)
            
            # Parse Persian datetime (YYYY/MM/DD HH:MM)
            date_part, time_part = value.split(' ')
            year, month, day = map(int, date_part.split('/'))
            hour, minute = map(int, time_part.split(':'))
            
            # Convert to Gregorian
            jalali_datetime = JalaliDateTime(year, month, day, hour, minute)
            gregorian_datetime = jalali_datetime.to_gregorian()
            
            return gregorian_datetime
        except (ValueError, TypeError):
            raise forms.ValidationError('Enter a valid Persian datetime (YYYY/MM/DD HH:MM)')
