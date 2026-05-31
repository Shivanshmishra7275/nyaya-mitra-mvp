"""
conftest.py
============
Pytest configuration for the root-level test_api.py.
This ensures pytest can import from app.* properly from the project root.
"""
import sys
import os

# Make sure the project root is in the Python path
sys.path.insert(0, os.path.dirname(__file__))
