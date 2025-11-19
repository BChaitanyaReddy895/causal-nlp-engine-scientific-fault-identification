# ⚡ Quick Start Guide - Causal-NLP Engine

## 🚀 Start the Application (30 seconds)

### Method 1: Run Backend Only (Testing)

```powershell
cd "c:\Users\chait\OneDrive\Desktop\NLP Project"
python backend/app.py
```

**Expected Output:**
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
 * Press CTRL+C to quit
```

**Verify it's working:**
```powershell
# In another terminal
python -c "
import requests
response = requests.get('http://localhost:5000/health')
print(response.json())
"
```

### Method 2: Run Full Stack (Frontend + Backend)

#### Terminal 1 - Backend:
```powershell
cd "c:\Users\chait\OneDrive\Desktop\NLP Project"
python backend/app.py
```

#### Terminal 2 - Frontend:
```powershell
cd "c:\Users\chait\OneDrive\Desktop\NLP Project\frontend"
npm install  # Only first time
npm start
```

**Access:**
- Frontend: http://localhost:3000
- Backend: http://localhost:5000

### Method 3: Docker (All-in-one)

```powershell
cd "c:\Users\chait\OneDrive\Desktop\NLP Project"
docker-compose up -d
```

**Access:**
- Frontend: http://localhost:3000
- Backend: http://localhost:5000

---

## ✅ Verify Everything Works

### Test 1: Health Check
```powershell
python -c "
import requests
r = requests.get('http://localhost:5000/health')
print('✅ Backend healthy:', r.json())
"
```

### Test 2: API Endpoints
```powershell
python -c "
import requests, json
r = requests.get('http://localhost:5000/')
print(json.dumps(r.json(), indent=2))
"
```

### Test 3: Data Pipeline
```powershell
python scripts/ingest_datasets.py
```

### Test 4: Model Training
```powershell
python scripts/train_graph_model.py
```

### Test 5: Run All Tests
```powershell
pytest tests/ -v
```

---

## 🛠️ Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'backend'"

**Solution:** Make sure you're in the project root directory:
```powershell
cd "c:\Users\chait\OneDrive\Desktop\NLP Project"
python backend/app.py
```

### Issue: Port 5000 already in use

**Solution:** Use a different port:
```powershell
# Set environment variable
$env:FLASK_PORT = 5001
python backend/app.py
```

Or kill the process using port 5000:
```powershell
netstat -ano | findstr :5000
# Get the PID, then:
taskkill /PID <PID> /F
```

### Issue: npm install fails

**Solution:**
```powershell
cd frontend
npm cache clean --force
rm -Force -Recurse node_modules
rm package-lock.json
npm install
```

### Issue: React won't load on http://localhost:3000

**Solution:**
```powershell
cd frontend
npm cache clean --force
npm install
npm start
```

---

## 📊 Expected Results

✅ Backend runs on http://localhost:5000
✅ Frontend runs on http://localhost:3000
✅ Health endpoint returns JSON with "status": "healthy"
✅ Data files created in data/ directories
✅ Model trained and saved to models/
✅ All 27+ tests pass

---

## 📝 Next Steps

1. **Access Frontend**: Open http://localhost:3000 in your browser
2. **Test API**: Use the Verify page to test claim verification
3. **Check Data**: View generated datasets in `data/` folder
4. **View Logs**: Monitor backend output in terminal 1
5. **Run Tests**: Execute `pytest tests/ -v` in a new terminal

---

## 🎯 Common Commands

```powershell
# Start Backend
python backend/app.py

# Start Frontend
cd frontend && npm start

# Run Tests
pytest tests/ -v

# Generate Data
python scripts/ingest_datasets.py

# Train Model
python scripts/train_graph_model.py

# Docker Start
docker-compose up -d

# Docker Stop
docker-compose down

# Check Status
curl http://localhost:5000/health
```

---

## 📚 Documentation

- **Main Guide**: HOW_TO_RUN_AND_TEST.md
- **Deployment**: DEPLOYMENT.md
- **Audit**: AUDIT_REPORT.md
- **API**: docs/api.md

---

**Your app is ready! Start with `python backend/app.py` 🚀**
