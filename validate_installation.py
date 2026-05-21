#!/usr/bin/env python3
"""
validate_installation.py
========================
Quick validation script to check if Nyaya Mitra is properly configured.

Run after installing dependencies:
    python validate_installation.py
"""

import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent

def check_environment():
    """Validate .env file exists and contains required keys."""
    env_file = BASE_DIR / ".env"
    if not env_file.exists():
        logger.error("❌ .env file not found. Copy from .env.example and fill in GEMINI_API_KEY.")
        return False
    
    with open(env_file) as f:
        content = f.read()
        if "GEMINI_API_KEY" not in content or "your_gemini_api_key_here" in content:
            logger.error("❌ GEMINI_API_KEY not set in .env file.")
            return False
    
    logger.info("✓ .env file found and configured.")
    return True

def check_directories():
    """Validate required directories exist."""
    required_dirs = [
        BASE_DIR / "models",
        BASE_DIR / "routers",
        BASE_DIR / "services",
        BASE_DIR / "db",
        BASE_DIR / "templates",
    ]
    
    for d in required_dirs:
        if not d.is_dir():
            logger.error(f"❌ Missing directory: {d.name}/")
            return False
    
    logger.info("✓ All required directories present.")
    return True

def check_files():
    """Validate required files exist."""
    required_files = [
        BASE_DIR / "main.py",
        BASE_DIR / "config.py",
        BASE_DIR / "etl_pipeline.py",
        BASE_DIR / "requirements.txt",
        BASE_DIR / "Dockerfile",
        BASE_DIR / "docker-compose.yml",
    ]
    
    for f in required_files:
        if not f.is_file():
            logger.error(f"❌ Missing file: {f.name}")
            return False
    
    logger.info("✓ All required files present.")
    return True

def check_imports():
    """Test critical imports."""
    try:
        import fastapi
        import chromadb
        import google.generativeai
        import langchain
        logger.info("✓ All critical dependencies importable.")
        return True
    except ImportError as e:
        logger.error(f"❌ Import failed: {e}")
        logger.error("Run: pip install -r requirements.txt")
        return False

def main():
    """Run all checks."""
    logger.info("=" * 60)
    logger.info("Nyaya Mitra Installation Validation")
    logger.info("=" * 60)
    
    checks = [
        ("Environment", check_environment),
        ("Directories", check_directories),
        ("Files", check_files),
        ("Imports", check_imports),
    ]
    
    results = []
    for name, check_fn in checks:
        try:
            result = check_fn()
            results.append(result)
        except Exception as e:
            logger.error(f"❌ {name} check failed: {e}")
            results.append(False)
    
    logger.info("=" * 60)
    if all(results):
        logger.info("✅ All checks passed! Ready to start development.")
        logger.info("")
        logger.info("Next steps:")
        logger.info("  1. Run ETL: python etl_pipeline.py")
        logger.info("  2. Start backend: uvicorn main:app --reload")
        logger.info("  3. In another terminal: cd nyaya-mitra-app && npx expo start")
        return 0
    else:
        logger.error("❌ Some checks failed. Fix issues above and try again.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
