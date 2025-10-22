#!/usr/bin/env python3
"""
Student Portal Flask Application
Run this file to start the student portal server
"""

from app import app

if __name__ == '__main__':
    print("Starting Student Portal...")
   
    app.run(debug=True, host='0.0.0.0', port=5001)
