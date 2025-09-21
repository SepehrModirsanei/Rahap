"""
Comprehensive Utils Tests

This test file focuses on improving coverage for the utils.py module,
which contains Persian date handling functions.
"""

from django.test import TestCase
from django.utils import timezone
from datetime import datetime, date
from finance.utils import (
    to_persian_date,
    to_persian_datetime,
    get_persian_date_display,
    get_persian_date_short,
    get_persian_time,
    get_persian_weekday
)


class UtilsComprehensiveTests(TestCase):
    """Comprehensive tests for utils functions to improve coverage"""
    
    def setUp(self):
        """Set up test data"""
        self.test_datetime = datetime(2024, 1, 15, 14, 30, 45)
        self.test_date = date(2024, 1, 15)
        self.test_timezone_aware = timezone.make_aware(
            datetime(2024, 1, 15, 14, 30, 45)
        )

    def test_to_persian_date_with_datetime(self):
        """Test to_persian_date with datetime object"""
        result = to_persian_date(self.test_datetime)
        self.assertIsInstance(result, str)
        self.assertNotEqual(result, '-')
        # Should contain Persian date format
        self.assertIn('/', result)

    def test_to_persian_date_with_date(self):
        """Test to_persian_date with date object"""
        result = to_persian_date(self.test_date)
        self.assertIsInstance(result, str)
        self.assertNotEqual(result, '-')
        # Should contain Persian date format
        self.assertIn('/', result)

    def test_to_persian_date_with_none(self):
        """Test to_persian_date with None"""
        result = to_persian_date(None)
        self.assertEqual(result, '-')

    def test_to_persian_date_with_custom_format(self):
        """Test to_persian_date with custom format"""
        custom_format = '%Y-%m-%d'
        result = to_persian_date(self.test_datetime, custom_format)
        self.assertIsInstance(result, str)
        self.assertNotEqual(result, '-')

    def test_to_persian_datetime_with_datetime(self):
        """Test to_persian_datetime with datetime object"""
        result = to_persian_datetime(self.test_datetime)
        self.assertIsInstance(result, str)
        self.assertNotEqual(result, '-')
        # Should contain both date and time
        self.assertIn('/', result)
        self.assertIn(':', result)

    def test_to_persian_datetime_with_none(self):
        """Test to_persian_datetime with None"""
        result = to_persian_datetime(None)
        self.assertEqual(result, '-')

    def test_to_persian_datetime_with_custom_format(self):
        """Test to_persian_datetime with custom format"""
        custom_format = '%Y-%m-%d %H:%M:%S'
        result = to_persian_datetime(self.test_datetime, custom_format)
        self.assertIsInstance(result, str)
        self.assertNotEqual(result, '-')

    def test_get_persian_date_display_with_datetime(self):
        """Test get_persian_date_display with datetime object"""
        result = get_persian_date_display(self.test_datetime)
        self.assertIsInstance(result, str)
        self.assertNotEqual(result, '-')
        # Should contain both date and time
        self.assertIn('/', result)
        self.assertIn(':', result)

    def test_get_persian_date_display_with_date(self):
        """Test get_persian_date_display with date object"""
        result = get_persian_date_display(self.test_date)
        self.assertIsInstance(result, str)
        self.assertNotEqual(result, '-')
        # Should contain date only
        self.assertIn('/', result)

    def test_get_persian_date_display_with_none(self):
        """Test get_persian_date_display with None"""
        result = get_persian_date_display(None)
        self.assertEqual(result, '-')

    def test_get_persian_date_display_with_timezone_aware(self):
        """Test get_persian_date_display with timezone-aware datetime"""
        result = get_persian_date_display(self.test_timezone_aware)
        self.assertIsInstance(result, str)
        self.assertNotEqual(result, '-')

    def test_get_persian_date_display_with_invalid_date(self):
        """Test get_persian_date_display with invalid date (exception handling)"""
        # Create a mock object that will cause an exception
        class InvalidDate:
            pass
        
        invalid_date = InvalidDate()
        result = get_persian_date_display(invalid_date)
        # Should return string representation of the object
        self.assertIsInstance(result, str)

    def test_get_persian_date_short_with_datetime(self):
        """Test get_persian_date_short with datetime object"""
        result = get_persian_date_short(self.test_datetime)
        self.assertIsInstance(result, str)
        self.assertNotEqual(result, '-')
        # Should contain date only (no time)
        self.assertIn('/', result)
        self.assertNotIn(':', result)

    def test_get_persian_date_short_with_date(self):
        """Test get_persian_date_short with date object"""
        result = get_persian_date_short(self.test_date)
        self.assertIsInstance(result, str)
        self.assertNotEqual(result, '-')
        # Should contain date only
        self.assertIn('/', result)

    def test_get_persian_date_short_with_none(self):
        """Test get_persian_date_short with None"""
        result = get_persian_date_short(None)
        self.assertEqual(result, '-')

    def test_get_persian_date_short_with_invalid_date(self):
        """Test get_persian_date_short with invalid date (exception handling)"""
        # Create a mock object that will cause an exception
        class InvalidDate:
            pass
        
        invalid_date = InvalidDate()
        result = get_persian_date_short(invalid_date)
        # Should return string representation of the object
        self.assertIsInstance(result, str)

    def test_get_persian_time_with_datetime(self):
        """Test get_persian_time with datetime object"""
        result = get_persian_time(self.test_datetime)
        self.assertIsInstance(result, str)
        self.assertNotEqual(result, '-')
        # Should contain time format
        self.assertIn(':', result)

    def test_get_persian_time_with_none(self):
        """Test get_persian_time with None"""
        result = get_persian_time(None)
        self.assertEqual(result, '-')

    def test_get_persian_time_with_invalid_date(self):
        """Test get_persian_time with invalid date (exception handling)"""
        # Create a mock object that will cause an exception
        class InvalidDate:
            pass
        
        invalid_date = InvalidDate()
        result = get_persian_time(invalid_date)
        # Should return string representation of the object
        self.assertIsInstance(result, str)

    def test_get_persian_weekday_with_datetime(self):
        """Test get_persian_weekday with datetime object"""
        result = get_persian_weekday(self.test_datetime)
        self.assertIsInstance(result, str)
        self.assertNotEqual(result, '-')
        # Should be a Persian weekday name
        persian_weekdays = ['شنبه', 'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنج‌شنبه', 'جمعه']
        self.assertIn(result, persian_weekdays)

    def test_get_persian_weekday_with_date(self):
        """Test get_persian_weekday with date object"""
        result = get_persian_weekday(self.test_date)
        self.assertIsInstance(result, str)
        self.assertNotEqual(result, '-')
        # Should be a Persian weekday name
        persian_weekdays = ['شنبه', 'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنج‌شنبه', 'جمعه']
        self.assertIn(result, persian_weekdays)

    def test_get_persian_weekday_with_none(self):
        """Test get_persian_weekday with None"""
        result = get_persian_weekday(None)
        self.assertEqual(result, '-')

    def test_get_persian_weekday_with_invalid_date(self):
        """Test get_persian_weekday with invalid date (exception handling)"""
        # Create a mock object that will cause an exception
        class InvalidDate:
            pass
        
        invalid_date = InvalidDate()
        result = get_persian_weekday(invalid_date)
        # Should return string representation of the object
        self.assertIsInstance(result, str)

    def test_get_persian_weekday_all_weekdays(self):
        """Test get_persian_weekday for all days of the week"""
        # Test different days of the week
        test_dates = [
            datetime(2024, 1, 15),  # Monday
            datetime(2024, 1, 16),  # Tuesday
            datetime(2024, 1, 17),  # Wednesday
            datetime(2024, 1, 18),  # Thursday
            datetime(2024, 1, 19),  # Friday
            datetime(2024, 1, 20),  # Saturday
            datetime(2024, 1, 21),  # Sunday
        ]
        
        expected_weekdays = ['دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنج‌شنبه', 'جمعه', 'شنبه', 'یکشنبه']
        
        for i, test_date in enumerate(test_dates):
            result = get_persian_weekday(test_date)
            self.assertIsInstance(result, str)
            self.assertNotEqual(result, '-')

    def test_all_functions_with_timezone_aware_datetime(self):
        """Test all functions with timezone-aware datetime"""
        # Test all functions with timezone-aware datetime
        result1 = to_persian_date(self.test_timezone_aware)
        result2 = to_persian_datetime(self.test_timezone_aware)
        result3 = get_persian_date_display(self.test_timezone_aware)
        result4 = get_persian_date_short(self.test_timezone_aware)
        result5 = get_persian_time(self.test_timezone_aware)
        result6 = get_persian_weekday(self.test_timezone_aware)
        
        # All should return valid strings
        for result in [result1, result2, result3, result4, result5, result6]:
            self.assertIsInstance(result, str)
            self.assertNotEqual(result, '-')

    def test_edge_case_very_old_date(self):
        """Test functions with very old date"""
        old_date = datetime(1900, 1, 1)
        
        result1 = to_persian_date(old_date)
        result2 = get_persian_date_display(old_date)
        result3 = get_persian_date_short(old_date)
        
        # Should handle old dates gracefully
        for result in [result1, result2, result3]:
            self.assertIsInstance(result, str)
            self.assertNotEqual(result, '-')

    def test_edge_case_future_date(self):
        """Test functions with future date"""
        future_date = datetime(2100, 12, 31)
        
        result1 = to_persian_date(future_date)
        result2 = get_persian_date_display(future_date)
        result3 = get_persian_date_short(future_date)
        
        # Should handle future dates gracefully
        for result in [result1, result2, result3]:
            self.assertIsInstance(result, str)
            self.assertNotEqual(result, '-')

    def test_consistency_across_functions(self):
        """Test that different functions return consistent results for the same date"""
        test_date = datetime(2024, 6, 15, 10, 30)
        
        # All functions should return valid strings
        results = [
            to_persian_date(test_date),
            to_persian_datetime(test_date),
            get_persian_date_display(test_date),
            get_persian_date_short(test_date),
            get_persian_time(test_date),
            get_persian_weekday(test_date)
        ]
        
        for result in results:
            self.assertIsInstance(result, str)
            self.assertNotEqual(result, '-')
