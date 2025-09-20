"""
Utility functions for Persian date handling
"""
from datetime import datetime
from django.utils import timezone
from persiantools.jdatetime import JalaliDate, JalaliDateTime
from django.utils.safestring import mark_safe


def to_persian_date(date_obj, format_str='%Y/%m/%d'):
    """
    Convert a datetime object to Persian date string
    
    Args:
        date_obj: datetime object
        format_str: Persian date format string
        
    Returns:
        str: Persian date string
    """
    if not date_obj:
        return '-'
    
    if isinstance(date_obj, datetime):
        # Convert to JalaliDateTime
        jalali_date = JalaliDateTime(date_obj)
        return jalali_date.strftime(format_str)
    else:
        # Assume it's a date object
        jalali_date = JalaliDate(date_obj)
        return jalali_date.strftime(format_str)


def to_persian_datetime(datetime_obj, format_str='%Y/%m/%d %H:%M'):
    """
    Convert a datetime object to Persian datetime string
    
    Args:
        datetime_obj: datetime object
        format_str: Persian datetime format string
        
    Returns:
        str: Persian datetime string
    """
    if not datetime_obj:
        return '-'
    
    jalali_datetime = JalaliDateTime(datetime_obj)
    return jalali_datetime.strftime(format_str)


def get_persian_date_display(date_obj):
    """
    Get a formatted Persian date for display in admin panels
    
    Args:
        date_obj: datetime or date object
        
    Returns:
        str: Formatted Persian date
    """
    if not date_obj:
        return '-'
    
    try:
        if isinstance(date_obj, datetime):
            jalali = JalaliDateTime(date_obj)
            return jalali.strftime('%Y/%m/%d %H:%M')
        else:
            jalali = JalaliDate(date_obj)
            return jalali.strftime('%Y/%m/%d')
    except:
        return str(date_obj)


def get_persian_date_short(date_obj):
    """
    Get a short Persian date for display
    
    Args:
        date_obj: datetime or date object
        
    Returns:
        str: Short Persian date (YYYY/MM/DD)
    """
    if not date_obj:
        return '-'
    
    try:
        if isinstance(date_obj, datetime):
            jalali = JalaliDateTime(date_obj)
            return jalali.strftime('%Y/%m/%d')
        else:
            jalali = JalaliDate(date_obj)
            return jalali.strftime('%Y/%m/%d')
    except:
        return str(date_obj)


def get_persian_time(date_obj):
    """
    Get Persian time for display
    
    Args:
        date_obj: datetime object
        
    Returns:
        str: Persian time (HH:MM)
    """
    if not date_obj:
        return '-'
    
    try:
        jalali = JalaliDateTime(date_obj)
        return jalali.strftime('%H:%M')
    except:
        return str(date_obj)


def get_persian_weekday(date_obj):
    """
    Get Persian weekday name
    
    Args:
        date_obj: datetime or date object
        
    Returns:
        str: Persian weekday name
    """
    if not date_obj:
        return '-'
    
    try:
        if isinstance(date_obj, datetime):
            jalali = JalaliDateTime(date_obj)
        else:
            jalali = JalaliDate(date_obj)
        
        weekdays = {
            0: 'شنبه',
            1: 'یکشنبه', 
            2: 'دوشنبه',
            3: 'سه‌شنبه',
            4: 'چهارشنبه',
            5: 'پنج‌شنبه',
            6: 'جمعه'
        }
        
        return weekdays[jalali.weekday()]
    except:
        return str(date_obj)
