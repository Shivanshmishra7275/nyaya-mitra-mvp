# 11 — Environment and DevOps
## Nyaya Mitra — Local Setup, Environment Variables, and AWS Deployment

**Version:** 1.0.0  
**Date:** March 2026

---

## 1. Local Development Setup (Windows — Current Environment)

### Prerequisites
```
Python 3.11+        (check: python --version)
Node.js 18+         (check: node --version)
npm 9+              (check: npm --version)
Git                 (check: git --version)
Expo Go app         (install on Android/iOS device for testing)
```

### Step 1: Clone and Setup Python Environment
```powershell
# Navigate to project root
cd "D:\Project Nyaya Mitra"

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install all Python dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables
```powershell
# Copy the example file
Copy-Item .env.example .env

# Edit .env and add your Gemini API key
# GEMINI_API_KEY=your_key_here
```

**.env file contents:**
```env
# ─── AI ────────────────────────────────────────────────
GEMINI_API_KEY=your_gemini_api_key_here

# ─── ChromaDB ──────────────────────────────────────────
CHROMA_DB_PATH=./chroma_db
CHROMA_COLLECTION_NAME=nyaya_mitra_legal

# ─── Embedding Model ───────────────────────────────────
EMBEDDING_MODEL=all-MiniLM-L6-v2

# ─── RAG Config ────────────────────────────────────────
RAG_TOP_K=15
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# ─── FastAPI ───────────────────────────────────────────
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
FASTAPI_ENV=development

# ─── SQLite (MVP) ──────────────────────────────────────
SQLITE_DB_PATH=./nyaya_mitra.db

# ─── Logging ───────────────────────────────────────────
LOG_LEVEL=INFO
```

### Step 3: Run ETL Pipeline (One-time, after placing PDFs)
```powershell
# Place PDFs in Raw_Data/
# bns.pdf, bnss.pdf, bsa.pdf, const.pdf

# Run ETL — populates chroma_db/ directory
python etl_pipeline.py

# Verify output
# Expected: "Successfully loaded X chunks into ChromaDB"
```

### Step 4: Start FastAPI Backend
```powershell
# From project root (with venv activated)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Test health endpoint
curl http://localhost:8000/health
```

### Step 5: Start React Native Frontend
```powershell
# In a new terminal
cd nyaya-mitra-app
npm install
npx expo start

# Scan QR code with Expo Go app (physical device)
# Press 'a' for Android emulator
# Press 'i' for iOS simulator (Mac only)
```

---

## 2. Environment Configuration Matrix

| Variable | Development | Staging | Production |
|---|---|---|---|
| `FASTAPI_ENV` | `development` | `staging` | `production` |
| `CHROMA_DB_PATH` | `./chroma_db` | `/data/chroma_db` | `/mnt/efs/chroma_db` |
| `SQLITE_DB_PATH` | `./nyaya_mitra.db` | (migrated to RDS) | (migrated to RDS) |
| `ALLOW_ORIGINS` | `["*"]` | `["https://staging.nyayamitra.in"]` | `["https://nyayamitra.in"]` |
| `LOG_LEVEL` | `DEBUG` | `INFO` | `WARNING` |
| `FASTAPI_PORT` | `8000` | `8000` | `8000` |

---

## 3. AWS Production Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     AWS (ap-south-1)                     │
│                                                         │
│  Route 53 DNS                                           │
│  api.nyayamitra.in → ALB                               │
│                                                         │
│  Application Load Balancer (ALB)                        │
│  ↓                                                      │
│  EC2 Auto Scaling Group                                 │
│  ├── t3.medium (FastAPI + Gunicorn, 4 workers)         │
│  └── User Data: pull Docker image from ECR             │
│                                                         │
│  Amazon EFS (Elastic File System)                       │
│  └── /mnt/efs/chroma_db  (shared ChromaDB store)       │
│                                                         │
│  Amazon RDS PostgreSQL (db.t3.micro → Phase 2)         │
│  └── nyaya_mitra_prod database                         │
│                                                         │
│  Amazon S3                                              │
│  └── s3://nyaya-mitra-pdfs/ (Raw PDFs, ETL source)     │
│                                                         │
│  AWS Secrets Manager                                    │
│  └── /nyaya-mitra/prod/GEMINI_API_KEY                  │
│                                                         │
│  CloudWatch Logs + Metrics                              │
│  └── /aws/nyaya-mitra/api-logs                         │
└─────────────────────────────────────────────────────────┘
```

---

## 4. Docker Configuration (Phase 2)

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download embedding model (cache in image layer)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy application code
COPY . .

# Run with Gunicorn (production) or Uvicorn (dev)
CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
```

```yaml
# docker-compose.yml (local + staging)
version: '3.9'
services:
  api:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./chroma_db:/app/chroma_db
      - ./Raw_Data:/app/Raw_Data
    env_file:
      - .env
    restart: unless-stopped
```

---

## 5. CI/CD Pipeline (GitHub Actions — Phase 2)

```yaml
# .github/workflows/deploy.yml
name: Deploy Nyaya Mitra Backend

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.11'}
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v --tb=short

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Build and push to ECR
        run: |
          aws ecr get-login-password | docker login ...
          docker build -t nyaya-mitra-api .
          docker push $ECR_URI/nyaya-mitra-api:$GITHUB_SHA

      - name: Deploy to EC2 via SSM
        run: |
          aws ssm send-command \
            --instance-ids $EC2_INSTANCE_ID \
            --document-name "AWS-RunShellScript" \
            --parameters commands='["docker pull $ECR_URI/nyaya-mitra-api:latest && docker-compose up -d"]'
```

---

## 6. Monitoring & Alerting (Phase 2)

```
CloudWatch Alarms:
  - API latency P95 > 4000ms → SNS alert
  - Error rate > 5% (5xx responses) → PagerDuty
  - ChromaDB memory > 80% → scale up alert

Application Metrics (custom):
  - query_latency_ms (histogram)
  - gemini_tokens_used (counter)
  - rag_retrieval_latency_ms (histogram)
  - cache_hit_rate (gauge)
```
