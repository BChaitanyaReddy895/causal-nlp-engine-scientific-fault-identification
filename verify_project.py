#!/usr/bin/env python3
"""Verify project completion."""

import os
import json
from pathlib import Path

def verify_project():
    """Verify all project components are complete."""
    
    project_root = Path(__file__).parent
    issues = []
    completed = []
    
    # Check backend code
    backend_files = list((project_root / "backend").glob("**/*.py"))
    if backend_files:
        completed.append(f"✅ Backend code: {len(backend_files)} Python files")
    else:
        issues.append("❌ Backend code missing")
    
    # Check frontend code
    frontend_files = list((project_root / "frontend").glob("**/*.{jsx,js}"))
    if frontend_files:
        completed.append(f"✅ Frontend code: {len(frontend_files)} React files")
    else:
        issues.append("❌ Frontend code missing")
    
    # Check data files
    raw_data = list((project_root / "data" / "raw").glob("*.jsonl"))
    processed_data = list((project_root / "data" / "processed").glob("*.json"))
    if raw_data and processed_data:
        completed.append(f"✅ Data files: {len(raw_data)} raw + {len(processed_data)} processed")
    else:
        issues.append(f"❌ Data files incomplete: {len(raw_data)} raw, {len(processed_data)} processed")
    
    # Check trained models
    models = list((project_root / "models").glob("**/*.pt"))
    if models:
        completed.append(f"✅ Trained models: {len(models)} checkpoint(s)")
        for model in models:
            size_kb = model.stat().st_size / 1024
            completed.append(f"   - {model.name}: {size_kb:.1f} KB")
    else:
        issues.append("❌ Trained models missing")
    
    # Check documentation
    docs = list((project_root / "docs").glob("*.md"))
    if docs:
        completed.append(f"✅ Documentation: {len(docs)} markdown files")
    else:
        issues.append("❌ Documentation missing")
    
    # Check configuration
    config_files = ["app.config.json", "requirements.txt", ".env.example"]
    for config in config_files:
        if (project_root / config).exists():
            completed.append(f"✅ Config: {config}")
        else:
            issues.append(f"❌ Config missing: {config}")
    
    # Check git history
    git_dir = project_root / ".git"
    if git_dir.exists():
        completed.append("✅ Git repository initialized")
    
    # Print results
    print("=" * 60)
    print("PROJECT COMPLETION REPORT")
    print("=" * 60)
    
    print("\n✅ COMPLETED:")
    for item in completed:
        print(f"  {item}")
    
    if issues:
        print("\n❌ ISSUES:")
        for item in issues:
            print(f"  {item}")
    
    print("\n" + "=" * 60)
    print(f"STATUS: {'✅ COMPLETE' if not issues else '⚠️  PARTIAL'}")
    print("=" * 60)
    
    return len(issues) == 0

if __name__ == "__main__":
    success = verify_project()
    exit(0 if success else 1)
