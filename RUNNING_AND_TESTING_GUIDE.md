# 🚀 How to Run and Test the Causal-NLP Engine

Complete guide for running, testing, and deploying the application.

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Setup](#setup)
3. [Running the Application](#running-the-application)
4. [Testing](#testing)
5. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before you start, ensure you have:

- **Python 3.10+** (tested with 3.13)
  ```powershell
  python --version
  ```

- **Git** (for version control)
  ```powershell
  git --version
  ```

- **Node.js 18+** (for frontend only)
  ```powershell
  node --version
  npm --version
  ```

- **Docker & Docker Compose** (for containerized deployment)
  ```powershell
  docker --version
  docker-compose --version
  ```

---

## Setup

### Step 1: Clone and Navigate

```powershell
# Navigate to project
cd "c:\Users\chait\OneDrive\Desktop\NLP Project"

# Verify git remote
git remote -v
```

**Expected Output:**
```
origin  https://github.com/BChaitanyaReddy895/causal-nlp-engine-scientific-fault-identification.git (fetch)
origin  https://github.com/BChaitanyaReddy895/causal-nlp-engine-scientific-fault-identification.git (push)
```

### Step 2: Create Virtual Environment

```powershell
# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1

# Upgrade pip
python -m pip install --upgrade pip
```

### Step 3: Install Dependencies

```powershell
# Install Python packages
pip install -r requirements.txt

# Verify key packages
python -c "import torch; import transformers; import flask; print('✅ All imports successful')"
```

### Step 4: Setup Data and Models

```powershell
# Ingest datasets
python scripts/ingest_datasets.py

# Expected output:
# Collecting SciFact dataset...
# Collecting FEVER-SCI dataset...
# ✅ All datasets collected successfully!
```

### Step 5: Train Model (Optional - Model Already Exists)

```powershell
# Train GNN model (skip if causal_graph_model.pt exists)
python scripts/train_graph_model.py

# Expected output:
# Epoch 10/20, Loss: 11.0525
# Epoch 20/20, Loss: 11.0128
# ✅ Training complete. Final loss: 11.0128
# ✅ Checkpoint saved to models/graph_model/causal_graph_model.pt
```

---

## Running the Application

### Option 1: Backend Only (Flask API)

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Set environment variables
$env:FLASK_ENV = "development"
$env:FLASK_APP = "backend.app:create_app()"
$env:PYTHONIOENCODING = "utf-8"

# Run Flask server
python -m flask run

# Or use Python directly
python -c "from backend.app import create_app; app = create_app(); app.run(debug=True)"
```

**Expected Output:**
```
 * Serving Flask app 'backend.app:create_app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

**Test the API:**
```powershell
# Health check
curl http://localhost:5000/health

# Expected response:
# {"status":"healthy","service":"causal-nlp-engine","version":"0.1.0","timestamp":"2025-11-19T..."}
```

### Option 2: Frontend Only (React App)

```powershell
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm start

# Frontend will open at http://localhost:3000
```

### Option 3: Full Stack (Backend + Frontend)

**Terminal 1 - Backend:**
```powershell
.\venv\Scripts\Activate.ps1
$env:FLASK_ENV = "development"
python -c "from backend.app import create_app; app = create_app(); app.run(debug=True, port=5000)"
```

**Terminal 2 - Frontend:**
```powershell
cd frontend
npm install
npm start
```

**Access Application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000
- API Docs: http://localhost:5000/api/docs (when implemented)

### Option 4: Docker Compose (Full Stack)

```powershell
# Build and run containers
docker-compose up -d

# Check container status
docker-compose ps

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop containers
docker-compose down
```

**Access Application:**
- Frontend: http://localhost:3000
- Backend: http://localhost:5000

---

## Testing

### Option 1: Unit Tests with Pytest

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_app.py -v

# Run with coverage
pytest tests/ --cov=backend --cov-report=html

# View coverage report
start htmlcov/index.html
```

**Expected Output:**
```
tests/test_app.py::test_app_factory PASSED
tests/test_config.py::test_config_development PASSED
tests/test_health.py::test_health_check PASSED
...
======================== 27 passed in 2.34s ======================
```

### Option 2: API Testing

**Using curl (PowerShell):**

```powershell
# Start backend first
python -c "from backend.app import create_app; app = create_app(); app.run(debug=True)"

# In another terminal, test endpoints:

# 1. Health check
curl http://localhost:5000/health

# 2. Root endpoint
curl http://localhost:5000/

# 3. Verify claim (when endpoint is implemented)
$claim = @{
    claim = "Turmeric cures cancer"
    domain = "medicine"
} | ConvertTo-Json

curl -X POST http://localhost:5000/api/verify `
  -ContentType "application/json" `
  -Body $claim
```

### Option 3: Data Pipeline Testing

```powershell
# Test data ingestion
python scripts/ingest_datasets.py

# Verify generated files
Get-ChildItem data/raw/*.jsonl
Get-ChildItem data/processed/*.json

# Test KG loading
python -c "from backend.kg.kg_manager import setup_kg; kg = setup_kg(); print('✅ KG loaded successfully')"
```

### Option 4: Model Testing

```powershell
# Test model loading and inference
python -c "
import torch
from backend.graph_models.gnn import CausalGraphModel

model = CausalGraphModel(num_nodes=10)
embeddings = torch.randn(1, 10, 128)
edge_features = torch.randn(1, 10, 10)
output = model(embeddings, edge_features)
print('✅ Model inference successful')
print(f'Adjacency shape: {output[\"adjacency\"].shape}')
"
```

### Option 5: Frontend Testing

```powershell
# Navigate to frontend
cd frontend

# Run tests
npm test

# Build for production
npm run build

# Check build output
ls build/
```

---

## Manual Testing Checklist

### Backend Testing ✓

- [ ] **Flask App**: `python -c "from backend.app import create_app; create_app()"`
- [ ] **Health Check**: `curl http://localhost:5000/health`
- [ ] **Config**: `python -c "from backend.config import get_config; get_config('development')"`
- [ ] **Data Ingestion**: `python scripts/ingest_datasets.py`
- [ ] **Model Loading**: `python -c "from backend.graph_models.gnn import CausalGraphModel; CausalGraphModel(10)"`
- [ ] **KG Manager**: `python -c "from backend.kg.kg_manager import setup_kg; setup_kg()"`
- [ ] **Extractor**: `python -c "from backend.causal_extractor.extractor import CausalExtractor; CausalExtractor()"`

### Frontend Testing ✓

- [ ] **Dependencies**: `npm install` completes without errors
- [ ] **Start Dev Server**: `npm start` opens on port 3000
- [ ] **Navigation**: Can navigate between Home → Verify → About
- [ ] **Form Submission**: Can type claim and submit
- [ ] **Styling**: Tailwind CSS loads correctly

### Integration Testing ✓

- [ ] **Backend + Frontend**: Both servers running on ports 5000 & 3000
- [ ] **API Calls**: Frontend can reach backend at http://localhost:5000
- [ ] **CORS**: No CORS errors in browser console
- [ ] **Data Flow**: Claims submitted successfully

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'backend'"

**Solution:**
```powershell
# Set PYTHONPATH
$env:PYTHONPATH = "$env:PYTHONPATH;."

# Or run from project root
cd "c:\Users\chait\OneDrive\Desktop\NLP Project"
```

### Issue: "UnicodeEncodeError: 'cp1252' codec can't encode character"

**Solution:**
```powershell
$env:PYTHONIOENCODING = "utf-8"
```

### Issue: Port 5000 already in use

**Solution:**
```powershell
# Check what's using port 5000
netstat -ano | findstr :5000

# Kill process (replace PID with actual process ID)
taskkill /PID <PID> /F

# Or use different port
python -c "from backend.app import create_app; app = create_app(); app.run(port=5001)"
```

### Issue: "spaCy model not found"

**Solution:**
```powershell
python -m spacy download en_core_web_sm
```

### Issue: "CUDA not available" (if using GPU)

**Solution:**
```powershell
# This is OK - will use CPU instead
# To use GPU, reinstall torch with CUDA support:
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

---

## Quick Reference Commands

```powershell
# Setup
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Data
python scripts/ingest_datasets.py
python scripts/train_graph_model.py

# Backend
python -c "from backend.app import create_app; app = create_app(); app.run(debug=True)"

# Frontend
cd frontend
npm install
npm start

# Tests
pytest tests/ -v

# Docker
docker-compose up -d
docker-compose down

# Git
git add -A
git commit -m "message"
git push -u origin master
```

---

## Verification Checklist

Run this to verify everything is working:

```powershell
# 1. Check Python
python --version

# 2. Check dependencies
pip list | findstr "Flask torch transformers"

# 3. Check data
Get-ChildItem data/raw -File
Get-ChildItem data/processed -File

# 4. Check models
Get-ChildItem models/graph_model -File

# 5. Check code
python -m py_compile backend/app.py
python -m py_compile scripts/train_graph_model.py

# 6. Run tests
pytest tests/ -q

echo "✅ All checks complete!"
```

---

## Production Deployment

### Using Docker:

```powershell
# Build images
docker-compose build

# Start services
docker-compose up -d

# View status
docker-compose ps

# View logs
docker-compose logs -f
```

### Manual Deployment:

```powershell
# Set production environment
$env:FLASK_ENV = "production"

# Install Gunicorn
pip install gunicorn

# Run with Gunicorn (4 workers)
gunicorn -w 4 -b 0.0.0.0:5000 "backend.app:create_app()"
```

---

## Next Steps

1. ✅ **Setup**: Follow the setup steps above
2. ✅ **Run**: Start backend and frontend
3. ✅ **Test**: Run unit tests and manual tests
4. ✅ **Verify**: Check the verification checklist
5. ✅ **Deploy**: Use Docker for production deployment

---

## Support

- **GitHub**: https://github.com/BChaitanyaReddy895/causal-nlp-engine-scientific-fault-identification
- **Documentation**: See `docs/` folder
- **Issues**: Check GitHub issues or create a new one

**Happy Testing! 🚀**
