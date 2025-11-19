"""Enhanced deployment guide."""

# Deployment Guide for Causal-NLP Engine

## Local Development

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- 4GB RAM minimum

### Quick Start

1. **Clone repository**
   ```bash
   git clone <repo>
   cd NLP\ Project
   ```

2. **Setup Python environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Setup Node environment**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. **Run with Docker Compose**
   ```bash
   make docker-up
   ```

5. **Access services**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000
   - API Docs: http://localhost:5000/api/docs

## Docker Deployment

### Build Images
```bash
docker build -f docker/Dockerfile.backend -t causal-nlp:backend .
docker build -f docker/Dockerfile.frontend -t causal-nlp:frontend .
```

### Run Containers
```bash
docker-compose -f docker-compose.yml up -d
```

## Production Deployment

### Environment Setup
```bash
cp .env.example .env
# Edit .env with production values
export FLASK_ENV=production
export DEBUG=False
export LOG_LEVEL=INFO
```

### Database Initialization
```bash
python -c "from backend.app import create_app; app = create_app('production'); app.app_context().push()"
```

### Health Checks
```bash
curl http://localhost:5000/health
curl http://localhost:5000/api/status/services
```

## Monitoring

### View Logs
```bash
docker logs -f nlp_backend
docker logs -f nlp_frontend
```

### Performance Metrics
```bash
curl http://localhost:5000/api/admin/metrics
```

## Troubleshooting

### Backend fails to start
- Check logs: `docker logs nlp_backend`
- Verify dependencies: `curl http://localhost:5000/api/status/dependencies`
- Ensure port 5000 is available

### Frontend won't load
- Clear browser cache
- Check Node version: `node --version`
- Rebuild: `docker-compose build frontend`

### Model inference slow
- Increase workers: Update `workers=8` in Dockerfile
- Check GPU: `nvidia-smi` (if CUDA available)
- Profile: Add `--profile` flag to gunicorn

## Scaling

### Horizontal Scaling with Multiple Workers
```yaml
# docker-compose.yml
  backend1:
    image: causal-nlp:backend
    ports: ["5001:5000"]
  backend2:
    image: causal-nlp:backend
    ports: ["5002:5000"]
```

### Load Balancing with Nginx
```nginx
upstream backend {
    server backend1:5000;
    server backend2:5000;
    server backend3:5000;
}
```

## Backup & Recovery

### Backup Knowledge Graph
```bash
sqlite3 data/kg.db ".backup backup_kg.db"
```

### Restore from Backup
```bash
sqlite3 data/kg.db ".restore backup_kg.db"
```
