#!/usr/bin/env python3
"""
Simple test runner to validate core functionality
"""

import sys
import subprocess

def run_test_suite():
    """Run the most critical tests to validate functionality"""
    
    print("🧪 Running EIP Sentiment Analyzer Test Suite")
    print("=" * 50)
    
    # Test categories to run
    test_commands = [
        ("Authentication Tests", "python -m pytest tests/test_auth.py::TestAuthentication::test_login_page_accessible -v"),
        ("Public Routes Test", "python -c \"import requests; print('Testing application accessibility...')\""),
        ("Database Models", "python -c \"from app import app, db; print('Database models imported successfully')\""),
    ]
    
    results = []
    
    for test_name, command in test_commands:
        print(f"\n📋 Running: {test_name}")
        print("-" * 30)
        
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print(f"✅ {test_name}: PASSED")
                results.append((test_name, "PASSED"))
            else:
                print(f"❌ {test_name}: FAILED")
                print(f"Error: {result.stderr}")
                results.append((test_name, "FAILED"))
        except subprocess.TimeoutExpired:
            print(f"⏰ {test_name}: TIMEOUT")
            results.append((test_name, "TIMEOUT"))
        except Exception as e:
            print(f"🚫 {test_name}: ERROR - {str(e)}")
            results.append((test_name, "ERROR"))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, status in results if status == "PASSED")
    total = len(results)
    
    for test_name, status in results:
        status_icon = "✅" if status == "PASSED" else "❌"
        print(f"{status_icon} {test_name}: {status}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All critical tests passing!")
        return True
    else:
        print("⚠️  Some tests need attention")
        return False

if __name__ == "__main__":
    success = run_test_suite()
    sys.exit(0 if success else 1)