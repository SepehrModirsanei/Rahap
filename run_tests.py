#!/usr/bin/env python3
"""
Test Runner Script for Finance Application

This script provides an easy way to run different categories of tests.
"""

import os
import sys
import subprocess
import argparse

def run_command(command):
    """Run a command and return the result"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def run_tests(test_path, verbose=False, coverage=False):
    """Run tests for a specific path"""
    if coverage:
        # Use coverage to run tests
        cmd = f"coverage run --source=finance manage.py test {test_path}"
        if verbose:
            cmd += " -v 2"
        
        print(f"Running with coverage: {cmd}")
        print("=" * 60)
        
        returncode, stdout, stderr = run_command(cmd)
        
        if returncode == 0:
            print("✅ Tests passed!")
            # Generate coverage report
            print("\n📊 Generating coverage report...")
            coverage_returncode, coverage_stdout, coverage_stderr = run_command("coverage report")
            if coverage_returncode == 0:
                print("📈 Coverage Report:")
                print(coverage_stdout)
            
            # Generate HTML report
            html_returncode, html_stdout, html_stderr = run_command("coverage html")
            if html_returncode == 0:
                print("🌐 HTML coverage report generated: htmlcov/index.html")
        else:
            print("❌ Tests failed!")
            if stderr:
                print(f"Error: {stderr}")
    else:
        # Regular test run
        cmd = f"python3 manage.py test {test_path}"
        if verbose:
            cmd += " -v 2"
        
        print(f"Running: {cmd}")
        print("=" * 60)
        
        returncode, stdout, stderr = run_command(cmd)
        
        if returncode == 0:
            print("✅ Tests passed!")
        else:
            print("❌ Tests failed!")
            if stderr:
                print(f"Error: {stderr}")
    
    if stdout:
        print(stdout)
    
    return returncode == 0

def main():
    parser = argparse.ArgumentParser(description='Finance Test Runner')
    parser.add_argument('category', nargs='?', choices=[
        'all', 'profit', 'transactions', 'admin', 'models', 'quick'
    ], default='quick', help='Test category to run')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--coverage', action='store_true', help='Run with code coverage analysis')
    parser.add_argument('--list', action='store_true', help='List available test categories')
    
    args = parser.parse_args()
    
    if args.list:
        print("Available test categories:")
        print("  all         - Run all tests")
        print("  profit      - Run profit calculation tests")
        print("  transactions - Run transaction tests")
        print("  admin       - Run admin interface tests")
        print("  models      - Run model tests")
        print("  quick       - Run quick profit tests (default)")
        return
    
    # Change to the project directory
    os.chdir('/Users/sepehr/Desktop/Rahap')
    
    test_categories = {
        'all': 'finance.tests',
        'profit': 'finance.tests.profit',
        'transactions': 'finance.tests.transactions',
        'admin': 'finance.tests.admin',
        'models': 'finance.tests.models',
        'quick': 'finance.tests.profit.test_profit_calculation finance.tests.profit.test_deposit_profit_to_base_account'
    }
    
    test_path = test_categories[args.category]
    
    print(f"🧪 Running {args.category} tests...")
    print(f"Test path: {test_path}")
    print()
    
    success = run_tests(test_path, args.verbose, args.coverage)
    
    if success:
        print("\n🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()
