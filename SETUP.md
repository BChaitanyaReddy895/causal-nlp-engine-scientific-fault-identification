# SETUP INSTRUCTIONS - Causal-NLP Engine

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker & Docker Compose (optional)
- Git

### Option 1: Local Development Setup

```bash
# 1. Clone the repository
git clone https://github.com/causal-nlp/claim-verifier.git
cd causal-nlp-claim-verifier

# 2. Create Python virtual environment
python -m venv venv
source venv/Scripts/activate  # On Windows

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Download spaCy model
python -m spacy download en_core_web_sm

# 5. Setup directories
mkdir -p data/{raw,processed} models/{graph_model,extractors}

# 6. Start Flask backend
export FLASK_ENV=development
flask run

# Backend will be available at http://localhost:5000
```

### Option 2: Docker Compose (Full Stack)

```bash
# 1. Build and run all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Access services:
# - Backend: http://localhost:5000
# - Frontend: http://localhost:3000
```

### Option 3: Makefile Commands

```bash
# Install dependencies
make setup

# Run local development server
make dev

# Run full Docker stack
make run

# Run tests
make test

# Format code
make format

# Cleanup
make clean
```

---

## 📋 Verification

### Test Backend Health

```bash
# Health check
curl http://localhost:5000/health

# Expected response:
# {
#   "status": "healthy",
#   "service": "causal-nlp-engine",
#   "version": "0.1.0",
#   "timestamp": "2024-01-15T10:30:45.123456"
# }
```

### Test Frontend

Open http://localhost:3000 in your browser. You should see:
- Causal-NLP logo and header
- Home page with service description
- Verify button linking to claim verification interface

### Run Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_health.py -v

# With coverage
pytest tests/ --cov=backend --cov-report=html
```

---

## 📁 Project Structure

```
causal-nlp-claim-verifier/
├── backend/                          # Flask backend
│   ├── app.py                       # App factory
│   ├── config.py                    # Configuration
│   ├── api/
│   │   ├── __init__.py
│   │   └── health_routes.py
│   ├── services/                    # Business logic (TODO: M1+)
│   ├── causal_extractor/            # Extraction models (TODO: M3)
│   ├── graph_models/                # GNN & DAG (TODO: M5)
│   ├── verifier/                    # Verification pipeline (TODO: M6)
│   ├── kg/                          # KG manager (TODO: M4)
│   └── utils/                       # Utilities
├── frontend/                        # React frontend
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── App.jsx
│   │   └── index.jsx
│   ├── public/
│   └── package.json
├── models/                          # Pre-trained models
│   ├── graph_model/
│   └── extractors/
├── data/                            # Dataset management
│   ├── raw/
│   ├── processed/
│   └── README.md
├── scripts/                         # Data & training scripts
├── tests/                           # Test suite
├── docs/                            # Documentation
├── docker/                          # Docker configuration
├── docker-compose.yml
├── Makefile                         # Build commands
├── requirements.txt                 # Python dependencies
└── README.md
```

---

## ⚙️ Configuration

### Environment Variables

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

Key settings in `.env`:

```
FLASK_ENV=development
FLASK_APP=backend/app.py
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///causal_nlp.db
KG_TYPE=sqlite
LOG_LEVEL=DEBUG
```

---

## 🧪 Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b milestone-1-data-ingestion
```

### 2. Make Changes

Edit code, add tests, commit frequently:

```bash
git add .
git commit -m "Add PubMed ingestion script"
```

### 3. Run Tests

```bash
make test
```

### 4. Format Code

```bash
make format
make lint
```

### 5. Push and Open PR

```bash
git push origin milestone-1-data-ingestion
```

---

## 🐛 Troubleshooting

### Backend Won't Start

```bash
# Check Python version
python --version  # Should be 3.10+

# Check if port 5000 is in use
lsof -i :5000  # macOS/Linux
netstat -ano | findstr :5000  # Windows

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

### Frontend Won't Load

```bash
# Check Node version
node --version  # Should be 18+

# Clear npm cache
npm cache clean --force
rm -rf node_modules package-lock.json
npm install

# Check if port 3000 is available
lsof -i :3000
```

### Docker Issues

```bash
# Rebuild images
docker-compose build --no-cache

# Remove old containers
docker-compose down -v

# Restart
docker-compose up
```

### Tests Failing

```bash
# Clear pytest cache
rm -rf .pytest_cache

# Run with verbose output
pytest tests/ -v -s

# Run specific test
pytest tests/test_health.py::test_health_check -v
```

---

## 📚 Next Steps

1. **Milestone 1** - Set up data ingestion pipelines
2. **Milestone 2** - Create annotation schema
3. **Milestone 3** - Build causal extraction module
4. ... (continue through Milestone 10)

See `docs/architecture.md` for detailed system design.

---

## 🤝 Contributing

Please read `CONTRIBUTING.md` for contribution guidelines.

---

## 📞 Support

- Check documentation in `docs/`
- Review existing issues on GitHub
- Create a new issue for bugs/features

---

**Happy coding! 🚀**
