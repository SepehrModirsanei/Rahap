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

### 📁 `/workflow/` - Workflow Tests
- **`test_transaction_state_workflow.py`** - Transaction state workflow and admin workflow tests

### 📁 `/admin/` - Admin Interface Tests
- (To be added) Admin panel functionality tests

### 📁 `/models/` - Model Tests
- **`test_account_balance_comprehensive.py`** - Comprehensive account balance calculation tests
- **`test_account_model.py`** - Basic account model functionality tests
- **`test_deposit_model.py`** - Basic deposit model functionality tests
- **`test_deposit_profit_comprehensive.py`** - Comprehensive deposit profit calculation tests
- **`test_transaction_comprehensive.py`** - Comprehensive transaction functionality tests
- **`test_user_model.py`** - User model functionality tests
- **`test_exchange_rate_logic.py`** - Exchange rate logic for cross-currency transactions
- **`test_transaction_code_generation.py`** - Transaction code generation and uniqueness tests
- **`test_daily_balance_snapshots.py`** - Daily balance snapshot system tests
- **`test_breakage_coefficient.py`** - Breakage coefficient logic tests (incomplete implementation)

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
