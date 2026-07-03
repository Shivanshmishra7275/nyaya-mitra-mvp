"""
conftest.py
============
Pytest configuration for the root-level test_api.py.
This ensures pytest can import from app.* properly from the project root.
"""
import sys
import os
from unittest.mock import MagicMock

# Make sure the project root is in the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Mock sentence_transformers to prevent Hugging Face model downloads during tests
mock_st = MagicMock()
mock_st.CrossEncoder = MagicMock()
mock_st.SentenceTransformer = MagicMock()
sys.modules['sentence_transformers'] = mock_st

