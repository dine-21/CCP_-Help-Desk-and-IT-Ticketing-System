"""
IT HelpDesk System — Root Execution Runner
Allows running the web application directly from the repository root directory.
Usage:
    python run.py
"""
import sys
import os

# Set working directory and import path to SourceCode
SOURCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'SourceCode')
if SOURCE_DIR not in sys.path:
    sys.path.insert(0, SOURCE_DIR)

os.chdir(SOURCE_DIR)

from app import app

if __name__ == '__main__':
    print("=" * 60)
    print(" IT HelpDesk System (Group 03 — SE CCP Project #11)")
    print(" Running locally at: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(host='127.0.0.1', port=5000, debug=True)
