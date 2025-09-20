# Finance Tests Documentation

This directory contains all test files for the finance application, organized by functionality.

## Test Organization

### 📁 `/profit/` - Profit Calculation Tests
- **`test_profit_calculation.py`** - Basic profit calculation tests for accounts and deposits
- **`test_profit_transaction_creation.py`** - Tests for profit transaction creation and application
- **`test_deposit_profit_to_base_account.py`** - Tests that deposit profits go to user's base account
- **`test_complete_profit_system.py`** - Comprehensive profit system integration tests

### 📁 `/transactions/` - Transaction Tests
- **`test_transaction_current.py`** - Current transaction functionality tests

### 📁 `/admin/` - Admin Interface Tests
- (To be added) Admin panel functionality tests

### 📁 `/models/` - Model Tests
- (To be added) Model validation and behavior tests

## Running Tests

### Run All Tests
```bash
python3 manage.py test finance.tests
```

### Run Specific Test Categories
```bash
# Profit calculation tests
python3 manage.py test finance.tests.profit

# Transaction tests
python3 manage.py test finance.tests.transactions

# Admin tests
python3 manage.py test finance.tests.admin

# Model tests
python3 manage.py test finance.tests.models
```

### Run Individual Test Files
```bash
# Profit calculation tests
python3 manage.py test finance.tests.profit.test_profit_calculation
python3 manage.py test finance.tests.profit.test_profit_transaction_creation
python3 manage.py test finance.tests.profit.test_deposit_profit_to_base_account
python3 manage.py test finance.tests.profit.test_complete_profit_system

# Transaction tests
python3 manage.py test finance.tests.transactions.test_transaction_current
```

### Run Specific Test Methods
```bash
# Example: Run specific test method
python3 manage.py test finance.tests.profit.test_profit_calculation.ProfitCalculationTest.test_account_profit_calculation_with_daily_snapshots
```

## Test Categories

### 🎯 Profit Calculation Tests
These tests verify that:
- Account profits are calculated correctly using daily snapshots
- Deposit profits are sent to the user's base account (حساب پایه)
- Profit transactions are created and applied correctly
- Management command works properly
- Multiple deposits send profits to the same base account

### 🔄 Transaction Tests
These tests verify that:
- Transactions are created correctly
- Transaction states are managed properly
- Transaction application works correctly

### 🎛️ Admin Interface Tests
These tests verify that:
- Admin panels work correctly
- Forms are properly configured
- JavaScript functionality works
- Persian translations are displayed

### 📊 Model Tests
These tests verify that:
- Model validation works correctly
- Model methods function properly
- Model relationships are correct

## Adding New Tests

When adding new tests:

1. **Choose the appropriate directory** based on functionality
2. **Follow naming convention**: `test_<functionality>.py`
3. **Use descriptive class names**: `Test<Functionality>Test`
4. **Add docstrings** to explain what each test does
5. **Update this README** with the new test information

## Test Data Setup

Most tests use the `setUp()` method to create test data:
- Test users
- Test accounts with different types and profit rates
- Test deposits with different profit rates
- Daily snapshots for account profit calculation

## Best Practices

1. **Isolate tests** - Each test should be independent
2. **Use descriptive names** - Test names should explain what they test
3. **Clean up data** - Tests should not leave data in the database
4. **Test edge cases** - Include tests for error conditions
5. **Document complex tests** - Add comments for complex test logic
