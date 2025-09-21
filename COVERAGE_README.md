# Code Coverage Tools for Finance Application

This project now includes comprehensive code coverage tools to help you understand how well your tests are covering your code.

## Quick Start

### 1. Install Coverage Dependencies
```bash
pip install -r requirements-test.txt
```

### 2. Run Tests with Coverage

#### Option A: Use the dedicated coverage script (Recommended)
```bash
# Run quick tests with coverage
python run_coverage.py quick

# Run all tests with coverage
python run_coverage.py all

# Run specific test categories
python run_coverage.py profit
python run_coverage.py transactions
python run_coverage.py admin
python run_coverage.py models
```

#### Option B: Use the updated test runner
```bash
# Run tests with coverage
python run_tests.py quick --coverage
python run_tests.py all --coverage
```

### 3. View Coverage Reports

After running tests with coverage, you'll get:

1. **Console Report**: Shows coverage percentage and missing lines
2. **HTML Report**: Detailed interactive report at `htmlcov/index.html`
3. **XML Report**: Machine-readable report at `coverage.xml` (if using `--xml` flag)

## Available Commands

### Coverage Script (`run_coverage.py`)
```bash
# Basic usage
python run_coverage.py [category] [options]

# Options:
-v, --verbose     Verbose output
--no-html        Skip HTML report generation
--xml            Generate XML report
--open           Open HTML report in browser
--summary        Show coverage summary only
--list           List available test categories
```

### Test Runner (`run_tests.py`)
```bash
# Basic usage
python run_tests.py [category] [options]

# Options:
-v, --verbose    Verbose output
--coverage       Run with code coverage analysis
--list           List available test categories
```

## Test Categories

- `quick` - Run quick profit tests (default)
- `profit` - Run profit calculation tests
- `transactions` - Run transaction tests
- `admin` - Run admin interface tests
- `models` - Run model tests
- `all` - Run all tests

## Coverage Configuration

The coverage is configured in `.coveragerc`:

- **Source**: Only covers the `finance` app
- **Omits**: Excludes migrations, tests, admin files, static files, etc.
- **Reports**: Generates HTML and console reports
- **Exclusions**: Excludes common patterns like `__repr__`, debug code, etc.

## Understanding Coverage Reports

### Console Report
Shows a summary like:
```
Name                           Stmts   Miss  Cover   Missing
------------------------------------------------------------
finance/models/account.py        45      2    96%     23, 45
finance/models/transaction.py   120      8    93%     45-52
------------------------------------------------------------
TOTAL                           500     25    95%
```

### HTML Report
- **Green**: Covered lines
- **Red**: Uncovered lines
- **Yellow**: Partially covered lines
- **Gray**: Excluded lines

## Best Practices

1. **Aim for 80%+ coverage** on critical business logic
2. **Focus on models and views** - these contain your core business logic
3. **Don't worry about 100%** - some code (like admin files) doesn't need full coverage
4. **Use the HTML report** to identify specific uncovered lines
5. **Run coverage regularly** to catch regressions

## Troubleshooting

### Coverage not installed
```bash
pip install coverage
```

### HTML report not opening
```bash
# Open manually
open htmlcov/index.html
# or
python run_coverage.py --open
```

### Coverage data not found
```bash
# Clear and re-run
coverage erase
python run_coverage.py quick
```

## Integration with CI/CD

For continuous integration, use:
```bash
python run_coverage.py all --xml
```

This generates `coverage.xml` that can be consumed by CI tools like Jenkins, GitHub Actions, etc.
