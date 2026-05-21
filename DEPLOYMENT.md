# Nyaya Mitra — Deployment Guide

## Production Deployment Checklist

This guide covers production-ready deployment of Nyaya Mitra.

### Pre-Deployment Validation

1. **Configuration**
   - [ ] Set `FASTAPI_ENV=production` in environment
   - [ ] Set valid `CORS_ORIGINS` (restrict to your domain)
   - [ ] Ensure `GEMINI_API_KEY` is securely stored (not in .env)
   - [ ] Set `GEMINI_MODEL` to stable version (not dev/preview)

2. **Database**
   - [ ] Run `python etl_pipeline.py` once to populate ChromaDB
   - [ ] Verify SQLite database path is on persistent storage
   - [ ] Enable WAL mode for SQLite (handled automatically)
   - [ ] Test backup/restore of ChromaDB and SQLite files

3. **Security**
   - [ ] Rotate Gemini API key regularly
   - [ ] Use HTTPS (TLS) in production
   - [ ] Implement rate limiting at reverse proxy (nginx/traefik)
   - [ ] Set `X-Content-Type-Options: nosniff` headers
   - [ ] Enable CORS only for trusted origins

4. **Performance**
   - [ ] Configure `UVICORN_WORKERS` based on CPU count (2-4 per core)
   - [ ] Set memory limits in Docker/Kubernetes
   - [ ] Enable CDN for static assets
   - [ ] Monitor API response times and queuing

### Docker Deployment

#### Build

```bash
docker build -t nyaya-mitra:latest .
```

#### Run with Environment

```bash
docker run \
  -e GEMINI_API_KEY="your-key-here" \
  -e FASTAPI_ENV=production \
  -e CORS_ORIGINS="https://your-domain.com" \
  -e UVICORN_WORKERS=4 \
  -p 8000:8000 \
  -v nyaya-chroma:/app/chroma_db \
  -v nyaya-sqlite:/app/db \
  nyaya-mitra:latest
```

#### Docker Compose (Production)

Update `docker-compose.yml`:

```yaml
services:
  backend:
    image: nyaya-mitra:latest
    environment:
      GEMINI_API_KEY: ${GEMINI_API_KEY}
      FASTAPI_ENV: production
      CORS_ORIGINS: https://yourdomain.com
      UVICORN_WORKERS: 4
      LOG_LEVEL: WARNING
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
```

### Kubernetes Deployment

Example `deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nyaya-mitra-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nyaya-mitra
  template:
    metadata:
      labels:
        app: nyaya-mitra
    spec:
      containers:
      - name: backend
        image: nyaya-mitra:latest
        env:
        - name: GEMINI_API_KEY
          valueFrom:
            secretKeyRef:
              name: nyaya-secrets
              key: gemini-key
        - name: FASTAPI_ENV
          value: "production"
        - name: UVICORN_WORKERS
          value: "4"
        ports:
        - containerPort: 8000
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 40
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        volumeMounts:
        - name: chroma-volume
          mountPath: /app/chroma_db
        - name: sqlite-volume
          mountPath: /app/db
      volumes:
      - name: chroma-volume
        persistentVolumeClaim:
          claimName: chroma-pvc
      - name: sqlite-volume
        persistentVolumeClaim:
          claimName: sqlite-pvc
```

### Reverse Proxy (Nginx)

```nginx
upstream nyaya_mitra {
    server backend:8000;
}

server {
    listen 443 ssl http2;
    server_name api.nyayamitra.in;

    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;

    # Security headers
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req zone=api_limit burst=20 nodelay;

    location /api/ {
        proxy_pass http://nyaya_mitra;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /health {
        proxy_pass http://nyaya_mitra;
        access_log off;
    }
}
```

### Monitoring & Logging

1. **Logs**
   - Collect Docker/k8s logs centrally (ELK, Splunk, etc.)
   - Filter by `[ERROR]`, `[WARNING]` levels
   - Alert on repeated failures

2. **Metrics**
   - Response time (P50, P95, P99)
   - API error rates (4xx, 5xx)
   - Gemini API quota usage
   - Database query latency
   - ChromaDB retrieval latency

3. **Alerts**
   - Health endpoint returns !="healthy"
   - API error rate > 5%
   - Response time P99 > 5s
   - Database connection pool exhausted

### Data Backup

1. **Daily Backup**
   ```bash
   # Backup ChromaDB
   tar -czf chroma_db_$(date +%Y%m%d).tar.gz ./chroma_db/
   
   # Backup SQLite
   cp nyaya_mitra.db nyaya_mitra_db_$(date +%Y%m%d).db
   ```

2. **Restore**
   ```bash
   # Stop API
   docker-compose down
   
   # Restore from backup
   tar -xzf chroma_db_20240101.tar.gz
   cp nyaya_mitra_db_20240101.db nyaya_mitra.db
   
   # Start API
   docker-compose up -d
   ```

### Scaling Considerations

1. **Vertical**
   - Increase `UVICORN_WORKERS` (CPU-bound due to JSON parsing)
   - Increase memory limits
   - Use faster hardware for Gemini API calls

2. **Horizontal**
   - Run multiple backend instances behind load balancer
   - Share ChromaDB and SQLite via network storage (NFS, EBS, etc.)
   - Use Kubernetes HPA for auto-scaling

3. **Bottlenecks**
   - Gemini API quotas (implement client-side caching)
   - ChromaDB query latency (HNSW index optimization)
   - SQLite write contention (consider PostgreSQL migration in Phase 2)

### Known Limitations

- **Embedding API**: Gemini free tier has quota limits (~1500 RPM). Add rate limiting.
- **ChromaDB**: Local filesystem backend not suitable for multi-machine deployments. Migrate to Supabase Vector or Pinecone for production scale.
- **SQLite**: File-based locking can cause issues under high concurrency. Migrate to PostgreSQL in Phase 2.
- **Frontend**: Currently a stub. Implement React Native/Expo frontend separately.

### Incident Response

#### API Returns 503 (Service Unavailable)

1. Check ChromaDB status: `curl localhost:8000/health`
2. If `vector_store="not_loaded"`: Re-run ETL pipeline
3. Check Gemini API status and quota
4. Review server logs for detailed errors

#### API Returns 502 (Bad Gateway)

1. Check Gemini API connectivity
2. Verify API key is valid and has quota
3. Check network connectivity to Gemini endpoints
4. Increase timeout values if needed

#### Database Locked Errors

1. Check SQLite file permissions
2. Enable WAL mode (automatic)
3. Review concurrent connection count
4. Plan migration to PostgreSQL

### Post-Deployment Validation

```bash
# Health check
curl -I https://api.nyayamitra.in/health

# Sample query
curl -X POST https://api.nyayamitra.in/api/v1/legal-query \
  -H "Content-Type: application/json" \
  -d '{"user_query": "What is bail?", "top_k": 5}'

# Corpus stats
curl https://api.nyayamitra.in/api/v1/corpus-stats
```

---

For questions, see the main README.md or create an issue on GitHub.
