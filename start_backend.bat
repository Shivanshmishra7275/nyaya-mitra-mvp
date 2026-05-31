@echo off
echo =============================================
echo  Nyaya Mitra — Starting Backend API Server
echo =============================================

if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found.
    echo Run: python -m venv venv ^&^& venv\Scripts\activate ^&^& pip install -r requirements.txt
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
echo [OK] Virtual environment activated

if not exist "vector_store_mock.json" (
    echo [WARN] vector_store_mock.json not found. Running ETL pipeline...
    python etl_pipeline.py
)

echo [OK] Starting FastAPI server on http://localhost:8000
echo [OK] Swagger UI: http://localhost:8000/docs
echo [OK] Health check: http://localhost:8000/health
echo.
echo Press Ctrl+C to stop the server.
echo.

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
