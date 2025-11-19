#!/usr/bin/env python3
"""Quick start script for testing the Causal-NLP Engine application."""

import os
import sys
import subprocess
from pathlib import Path

def print_header(text):
    """Print formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def print_success(text):
    """Print success message."""
    print(f"✅ {text}")

def print_error(text):
    """Print error message."""
    print(f"❌ {text}")

def print_info(text):
    """Print info message."""
    print(f"ℹ️  {text}")

def check_python():
    """Check Python version."""
    print_header("Checking Python Environment")
    
    version = sys.version_info
    print(f"Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print_error("Python 3.10+ required")
        return False
    
    print_success("Python version OK")
    return True

def check_dependencies():
    """Check if key packages are installed."""
    print_header("Checking Dependencies")
    
    required = {
        'flask': 'Flask',
        'torch': 'PyTorch',
        'transformers': 'Transformers',
        'spacy': 'spaCy',
    }
    
    for module, name in required.items():
        try:
            __import__(module)
            print_success(f"{name} installed")
        except ImportError:
            print_error(f"{name} not installed - run: pip install -r requirements.txt")
            return False
    
    return True

def check_data():
    """Check if data files exist."""
    print_header("Checking Data Files")
    
    data_files = {
        'data/raw': 'Raw data',
        'data/processed': 'Processed data',
    }
    
    all_exist = True
    for path, desc in data_files.items():
        if Path(path).exists() and len(list(Path(path).glob('*'))):
            files = len(list(Path(path).glob('*')))
            print_success(f"{desc}: {files} files found")
        else:
            print_error(f"{desc}: Not found")
            all_exist = False
    
    return all_exist

def check_models():
    """Check if trained models exist."""
    print_header("Checking Trained Models")
    
    model_path = Path('models/graph_model/causal_graph_model.pt')
    
    if model_path.exists():
        size_mb = model_path.stat().st_size / (1024 * 1024)
        print_success(f"Model found: {size_mb:.2f} MB")
        return True
    else:
        print_error("Model not found - run: python scripts/train_graph_model.py")
        return False

def test_backend():
    """Test backend imports."""
    print_header("Testing Backend")
    
    try:
        from backend.app import create_app
        app = create_app()
        print_success("Flask app created successfully")
        
        from backend.graph_models.gnn import CausalGraphModel
        print_success("GNN model loaded successfully")
        
        from backend.causal_extractor.extractor import CausalExtractor
        print_success("Causal extractor loaded successfully")
        
        from backend.kg.kg_manager import KGManager
        print_success("KG manager loaded successfully")
        
        return True
    except Exception as e:
        print_error(f"Backend error: {str(e)}")
        return False

def test_data_pipeline():
    """Test data pipeline."""
    print_header("Testing Data Pipeline")
    
    try:
        from scripts.ingest_datasets import SciFact, KGLoader
        print_success("Data ingestion modules loaded")
        
        print_info("Sample data generation is available")
        print_info("Run: python scripts/ingest_datasets.py")
        return True
    except Exception as e:
        print_error(f"Data pipeline error: {str(e)}")
        return False

def test_model_inference():
    """Test model inference."""
    print_header("Testing Model Inference")
    
    try:
        import torch
        from backend.graph_models.gnn import CausalGraphModel
        
        model = CausalGraphModel(num_nodes=10)
        embeddings = torch.randn(1, 10, 128)
        edge_features = torch.randn(1, 10, 10)
        
        output = model(embeddings, edge_features)
        
        print_success("Model inference successful")
        print_info(f"Output keys: {list(output.keys())}")
        return True
    except Exception as e:
        print_error(f"Model inference error: {str(e)}")
        return False

def print_manual_tests():
    """Print manual testing instructions."""
    print_header("Manual Testing Instructions")
    
    print("""
1️⃣  START BACKEND:
   python -c "from backend.app import create_app; app = create_app(); app.run(debug=True)"
   
   Then test health check:
   curl http://localhost:5000/health

2️⃣  START FRONTEND:
   cd frontend
   npm install
   npm start
   
   Frontend opens at http://localhost:3000

3️⃣  TEST DATA INGESTION:
   python scripts/ingest_datasets.py

4️⃣  RUN UNIT TESTS:
   pytest tests/ -v

5️⃣  VIEW AVAILABLE ENDPOINTS:
   python -c "from backend.app import create_app; app = create_app(); 
   [print(f'{rule}') for rule in app.url_map.iter_rules()]"
    """)

def print_quick_commands():
    """Print quick reference commands."""
    print_header("Quick Reference Commands")
    
    print("""
Setup:
  python -m venv venv
  .\\venv\\Scripts\\Activate.ps1
  pip install -r requirements.txt

Data:
  python scripts/ingest_datasets.py
  python scripts/train_graph_model.py

Backend:
  python -c "from backend.app import create_app; app = create_app(); app.run(debug=True)"

Frontend:
  cd frontend && npm install && npm start

Tests:
  pytest tests/ -v

Docker:
  docker-compose up -d

Git:
  git add -A
  git commit -m "message"
  git push -u origin master
    """)

def main():
    """Run all checks and tests."""
    print("\n" + "🚀" * 30)
    print("CAUSAL-NLP ENGINE - Quick Start Test Suite")
    print("🚀" * 30)
    
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    results = []
    
    # Run checks
    results.append(("Python", check_python()))
    results.append(("Dependencies", check_dependencies()))
    results.append(("Data Files", check_data()))
    results.append(("Models", check_models()))
    results.append(("Backend", test_backend()))
    results.append(("Data Pipeline", test_data_pipeline()))
    results.append(("Model Inference", test_model_inference()))
    
    # Print summary
    print_header("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<40} {status}")
    
    print(f"\nResult: {passed}/{total} tests passed")
    
    if passed == total:
        print_success("All checks passed! Application is ready.")
    else:
        print_error("Some checks failed. See errors above.")
    
    # Print instructions
    print_manual_tests()
    print_quick_commands()
    
    print_header("Next Steps")
    print("""
1. Fix any failed checks (see errors above)
2. Start the backend server
3. Start the frontend (optional)
4. Run unit tests with pytest
5. Access application at http://localhost:3000 or http://localhost:5000

For detailed instructions, see: RUNNING_AND_TESTING_GUIDE.md
    """)
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
