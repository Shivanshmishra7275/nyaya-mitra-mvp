#!/usr/bin/env python3
"""
start_backend.py
=================
Cross-platform startup helper for Nyaya Mitra backend.
Run: python start_backend.py

Automatically:
  1. Checks for vector_store_mock.json (runs ETL if missing)
  2. Starts uvicorn with sensible defaults
"""
import os
import sys
import subprocess
from pathlib import Path


def main():
    project_root = Path(__file__).parent

    print("=" * 50)
    print("  Nyaya Mitra — Backend Startup")
    print("=" * 50)

    # 1. Download Corpus if missing
    print("\n[INFO] Checking for official corpus PDFs...")
    subprocess.run([sys.executable, "download_corpus.py"], cwd=project_root)

    # 2. Check if vector store exists
    store = project_root / "vector_store_mock.json"
    if not store.exists():
        print("\n[WARN] vector_store_mock.json not found.")
        print("[INFO] Running ETL pipeline to build it...")
        result = subprocess.run(
            [sys.executable, "etl_pipeline.py"],
            cwd=project_root,
        )
        if result.returncode != 0:
            print("[ERROR] ETL pipeline failed. Place PDF files in Raw_Data/ and retry.")
            sys.exit(1)

    print("\n[OK] Starting server at http://localhost:8000")
    print("[OK] Swagger UI: http://localhost:8000/docs")
    print("[OK] Health check: http://localhost:8000/health")
    print("[OK] Press Ctrl+C to stop\n")

    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload",
    ], cwd=project_root)


if __name__ == "__main__":
    main()
