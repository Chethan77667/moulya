#!/usr/bin/env python3
"""
Test script to verify login printing functionality
"""

import requests
import json
from datetime import datetime

def test_login_printing():
    """Test the login printing functionality"""
    print("=== Testing Login Printing Functionality ===")
    
    # Test data
    test_roll_number = "BCA25001"
    test_date_of_birth = "2000-01-01"  # You may need to adjust this
    
    print(f"Testing with roll number: {test_roll_number}")
    print(f"Date of birth: {test_date_of_birth}")
    
    # Base URL
    base_url = "http://localhost:5000"
    
    try:
        # Test login
        print("\n1. Testing login...")
        login_data = {
            'roll_number': test_roll_number,
            'date_of_birth': test_date_of_birth
        }
        
        session = requests.Session()
        
        # Get login page first
        response = session.get(f"{base_url}/login")
        if response.status_code == 200:
            print("✓ Login page accessible")
        else:
            print(f"✗ Login page not accessible: {response.status_code}")
            return False
        
        # Attempt login
        response = session.post(f"{base_url}/login", data=login_data)
        if response.status_code == 200:
            print("✓ Login request sent")
            # Check if redirected to dashboard
            if 'dashboard' in response.url or response.status_code == 302:
                print("✓ Login successful - redirected to dashboard")
            else:
                print("? Login response received but not redirected")
        else:
            print(f"✗ Login failed: {response.status_code}")
            return False
        
        # Test attendance page access
        print("\n2. Testing attendance page access...")
        response = session.get(f"{base_url}/attendance")
        if response.status_code == 200:
            print("✓ Attendance page accessible")
        else:
            print(f"✗ Attendance page not accessible: {response.status_code}")
            return False
        
        print("\n=== Test Complete ===")
        print("Check the server console output for printed user data")
        return True
        
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to server. Make sure the server is running on localhost:5000")
        return False
    except Exception as e:
        print(f"✗ Error during test: {e}")
        return False

if __name__ == "__main__":
    success = test_login_printing()
    if success:
        print("\n🎉 Test completed successfully!")
        print("Check the server console for printed user data.")
    else:
        print("\n❌ Test failed. Check the output above for details.")
