#!/usr/bin/env python3
"""
Coverage Test Runner for Finance Application

This script runs tests with code coverage analysis and generates detailed reports.
"""

import os
import sys
import subprocess
import argparse
import webbrowser
from pathlib import Path

def run_command(command, capture_output=True):
    """Run a command and return the result"""
    try:
        result = subprocess.run(command, shell=True, capture_output=capture_output, text=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def install_coverage():
    """Install coverage package if not already installed"""
    print("🔧 Checking coverage installation...")
    returncode, stdout, stderr = run_command("python3 -c 'import coverage'")
    
    if returncode != 0:
        print("📦 Installing coverage package...")
        returncode, stdout, stderr = run_command("pip3 install coverage")
        if returncode != 0:
            print(f"❌ Failed to install coverage: {stderr}")
            return False
        print("✅ Coverage installed successfully!")
    else:
        print("✅ Coverage already installed!")
    return True

def run_coverage_tests(test_path, verbose=False, html=True, xml=False):
    """Run tests with coverage analysis"""
    print(f"🧪 Running coverage analysis for: {test_path}")
    print("=" * 60)
    
    # Clear any existing coverage data
    run_command("coverage erase")
    
    # Run tests with coverage
    cmd = f"coverage run --source=finance manage.py test {test_path}"
    if verbose:
        cmd += " -v 2"
    
    print(f"Running: {cmd}")
    returncode, stdout, stderr = run_command(cmd, capture_output=False)
    
    if returncode != 0:
        print("❌ Tests failed!")
        return False
    
    # Generate coverage report
    print("\n📊 Generating coverage report...")
    
    # Console report
    returncode, stdout, stderr = run_command("coverage report")
    if returncode == 0:
        print("📈 Coverage Report:")
        print(stdout)
    
    # HTML report
    if html:
        print("\n🌐 Generating HTML report...")
        returncode, stdout, stderr = run_command("coverage html")
        if returncode == 0:
            html_path = Path("htmlcov/index.html").absolute()
            print(f"✅ HTML report generated: {html_path}")
        else:
            print(f"❌ Failed to generate HTML report: {stderr}")
    
    # XML report
    if xml:
        print("\n📄 Generating XML report...")
        returncode, stdout, stderr = run_command("coverage xml")
        if returncode == 0:
            print("✅ XML report generated: coverage.xml")
        else:
            print(f"❌ Failed to generate XML report: {stderr}")
    
    return True

def open_html_report():
    """Open the HTML coverage report in browser"""
    html_path = Path("htmlcov/index.html")
    if html_path.exists():
        print(f"🌐 Opening coverage report: {html_path.absolute()}")
        webbrowser.open(f"file://{html_path.absolute()}")
    else:
        print("❌ HTML report not found. Run tests with --html flag first.")

def show_coverage_summary():
    """Show a quick coverage summary"""
    returncode, stdout, stderr = run_command("coverage report --show-missing")
    if returncode == 0:
        print("📊 Coverage Summary:")
        print(stdout)
    else:
        print(f"❌ Failed to get coverage summary: {stderr}")

def main():
    parser = argparse.ArgumentParser(description='Finance Coverage Test Runner')
    parser.add_argument('category', nargs='?', choices=[
        'all', 'profit', 'transactions', 'admin', 'models', 'quick'
    ], default='quick', help='Test category to run')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--no-html', action='store_true', help='Skip HTML report generation')
    parser.add_argument('--xml', action='store_true', help='Generate XML report')
    parser.add_argument('--open', action='store_true', help='Open HTML report in browser')
    parser.add_argument('--summary', action='store_true', help='Show coverage summary only')
    parser.add_argument('--list', action='store_true', help='List available test categories')
    
    args = parser.parse_args()
    
    if args.list:
        print("Available test categories:")
        print("  all         - Run all tests with coverage")
        print("  profit      - Run profit calculation tests")
        print("  transactions - Run transaction tests")
        print("  admin       - Run admin interface tests")
        print("  models      - Run model tests")
        print("  quick       - Run quick profit tests (default)")
        return
    
    # Change to the project directory
    os.chdir('/Users/sepehr/Desktop/Rahap')
    
    # Install coverage if needed
    if not install_coverage():
        sys.exit(1)
    
    # Show summary only
    if args.summary:
        show_coverage_summary()
        return
    
    # Open HTML report
    if args.open:
        open_html_report()
        return
    
    # Test categories
    test_categories = {
        'all': 'finance.tests',
        'profit': 'finance.tests.profit',
        'transactions': 'finance.tests.transactions',
        'admin': 'finance.tests.admin',
        'models': 'finance.tests.models',
        'quick': 'finance.tests.profit.test_profit_calculation finance.tests.profit.test_deposit_profit_to_base_account'
    }
    
    test_path = test_categories[args.category]
    
    print(f"🧪 Running {args.category} tests with coverage...")
    print(f"Test path: {test_path}")
    print()
    
    success = run_coverage_tests(
        test_path, 
        verbose=args.verbose,
        html=not args.no_html,
        xml=args.xml
    )
    
    if success:
        print("\n🎉 Coverage analysis completed successfully!")
        if not args.no_html:
            print("🌐 Open htmlcov/index.html in your browser to view detailed coverage report")
        sys.exit(0)
    else:
        print("\n💥 Coverage analysis failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()
