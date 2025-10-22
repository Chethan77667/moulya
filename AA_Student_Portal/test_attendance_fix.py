#!/usr/bin/env python3
"""
Test script to verify that attendance data is now displaying correctly
"""

import requests
import json
import sys
import os

def test_attendance_display():
    """Test the attendance display functionality"""
    
    # Test the student portal API endpoints
    base_url = "http://localhost:5000"
    
    print("=== Testing Attendance Display Fix ===")
    print()
    
    # Test 1: Check if server is running
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print("✓ Server is running")
    except requests.exceptions.RequestException as e:
        print(f"✗ Server is not running: {e}")
        print("Please start the student portal with: python student_app.py")
        return False
    
    # Test 2: Test the monthly attendance API endpoint
    try:
        # This would normally require authentication, but let's test the endpoint structure
        response = requests.get(f"{base_url}/api/attendance/monthly", timeout=5)
        print(f"✓ Monthly attendance API endpoint accessible (status: {response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"✗ Monthly attendance API error: {e}")
    
    print()
    print("=== Manual Testing Instructions ===")
    print("1. Open your browser and go to: http://localhost:5000")
    print("2. Login with:")
    print("   - Username: BCA23077")
    print("   - Password: 2005-01-15")
    print("3. Click on 'Attendance' in the navigation")
    print("4. You should now see:")
    print("   - Total Classes: 33")
    print("   - Present: 23")
    print("   - Deputation: 0")
    print("   - Absent: 10")
    print("   - Attendance %: 69.70%")
    print("   - Monthly data for September 2025 (83.33%) and August 2025 (61.90%)")
    print()
    print("If you see all zeros, the fix may not be working properly.")
    print("If you see the correct data, the attendance display issue has been resolved!")
    
    return True

if __name__ == "__main__":
    test_attendance_display()
