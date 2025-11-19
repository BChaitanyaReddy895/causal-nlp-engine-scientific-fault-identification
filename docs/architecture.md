# Architecture Overview

## System Design

The Causal-NLP Engine is built as a microservices architecture with a clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                   React Frontend (Port 3000)                 │
│         - Claim Verification Interface                       │
│         - Graph Visualization (Cytoscape.js)                │
│         - Evidence & Explanation Display                     │
└────────────────┬──────────────────────────────────────────────┘
                 │ HTTP/REST
                 ▼
┌─────────────────────────────────────────────────────────────┐
│              Flask Backend API (Port 5000)                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │          API Blueprints (Modular Routes)             │   │
│  │  - /verify                                           │   │
│  │  - /kg                                               │   │
│  │  - /health                                           │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Core Services & Pipeline                      │   │
│  │  ┌───────────────────────────────────────┐           │   │
│  │  │ Causal Extraction Module              │           │   │
│  │  │  - Rule-based (spaCy)                │           │   │
│  │  │  - Transformer-based (T5/DeBERTa)    │           │   │
│  │  └───────────────────────────────────────┘           │   │
│  │                     ▼                                │   │
│  │  ┌───────────────────────────────────────┐           │   │
│  │  │ Causal Graph Builder                  │           │   │
│  │  │  - DAG Learner (Attention-based)     │           │   │
│  │  │  - GNN Embedder (DGL/PyG)            │           │   │
│  │  └───────────────────────────────────────┘           │   │
│  │                     ▼                                │   │
│  │  ┌───────────────────────────────────────┐           │   │
│  │  │ Verification Pipeline                 │           │   │
│  │  │  - KG Evidence Retrieval              │           │   │
│  │  │  - Counterfactual Reasoning           │           │   │
│  │  │  - Fallacy Detection                  │           │   │
│  │  └───────────────────────────────────────┘           │   │
│  │                                                       │   │
│  └──────────────────────────────────────────────────────┘   │
│                     ▲                                       │
│                     │                                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │    Knowledge Graph (KG) Manager & Storage            │   │
│  │  - UMLS Integration                                 │   │
│  │  - DisGeNET Gene-Disease Relations                 │   │
│  │  - CTD Chemical → Gene → Disease                    │   │
│  │  - Custom Biomedical Triples                        │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         │                                    │
         ▼                                    ▼
    SQLite KG DB                    PyTorch Models
   (kg.db)                         (graph_model, extractors)
```

## Component Details

### 1. **Frontend (React + Tailwind CSS)**
- **Purpose**: User-facing interface
- **Features**:
  - Home page with service overview
  - Claim verification form
  - Interactive causal graph visualization
  - Evidence display panel
  - Search and history functionality
- **Technologies**: React 18, Tailwind CSS, Cytoscape.js, Axios

### 2. **Backend API (Flask with Blueprints)**

#### Blueprints:
- **Health Routes** (`health_routes.py`): Service status checks
- **Verify Routes** (`verify_routes.py`): Claim verification endpoint
- **KG Routes** (`kg_routes.py`): Knowledge graph queries

#### Structure:
```
backend/
├── app.py                    # Flask app factory
├── config.py               # Configuration management
├── api/                    # REST endpoints (blueprints)
├── services/               # Business logic layer
├── causal_extractor/       # Extraction models
├── graph_models/           # GNN and DAG models
├── verifier/               # Verification pipeline
├── kg/                     # Knowledge graph
└── utils/                  # Utility functions
```

### 3. **Causal Extraction Module**

**Pipeline**:
1. **Input**: Scientific claim (text)
2. **Preprocessing**: Tokenization, POS tagging
3. **Extraction** (dual approach):
   - **Rule-based**: spaCy dependency patterns + heuristics
   - **Transformer-based**: Fine-tuned T5/DeBERTa on causal datasets
4. **Output**: Triples with confidence scores

**Datasets**:
- BioCause (biomedical causality)
- EventCausality (general causality)
- SemEval Causal Task
- Custom annotated corpus

### 4. **Causal Graph Learning**

**Components**:
- **DAG Learner**: Differentiable Acyclic Graph structure learning
- **GNN Embedder**: Graph Attention Networks (DGL/PyG)
- **Node Embeddings**: Entity and relation embeddings

**Process**:
```
Extracted Triples → DAG Structure Learning → GNN Embeddings → 
→ Consistency Scoring → Evidence Alignment
```

### 5. **Knowledge Graph Manager**

**Knowledge Sources**:
- **UMLS**: Unified Medical Language System
- **DisGeNET**: Gene-disease associations
- **CTD**: Chemical-gene-disease interactions
- **Custom Triples**: Verified biomedical facts

**Operations**:
- Entity canonicalization
- Graph traversal and relevance scoring
- Evidence retrieval

### 6. **Verification Pipeline**

**Flow**:
```
Claim → Extract Triples → Build Causal Graph → 
→ Query KG → Collect Evidence → Counterfactual Analysis → 
→ Generate Verdict
```

**Verdicts**:
- `SUPPORTS_CAUSALITY`: Strong evidence for causal link
- `REFUTES_CAUSALITY`: Evidence contradicts claim
- `CORRELATION_NOT_CAUSAL`: Evidence shows only correlation
- `UNVERIFIABLE`: Insufficient evidence
- `MISSING_MECHANISM`: No mechanistic pathway found

## Data Flow

### Claim Verification Request
```json
{
  "claim": "Turmeric consumption cures liver cancer",
  "domain": "medicine"
}
```

### Processing Steps
1. **Extraction**: Extract triples (turmeric, cures, liver cancer)
2. **Graph Building**: Create causal graph structure
3. **KG Lookup**: Query UMLS, DisGeNET, CTD for evidence
4. **Analysis**: Apply counterfactual reasoning
5. **Reasoning**: Check for missing mechanistic nodes
6. **Verdict**: Generate final assessment

### Response
```json
{
  "claim_id": "claim_001",
  "verdict": "CAUSAL_INVALID",
  "confidence": 0.92,
  "triples": [
    {
      "subject": "turmeric",
      "relation": "cures",
      "object": "liver cancer",
      "confidence": 0.02,
      "status": "INVALID"
    }
  ],
  "causal_graph": { ... },
  "evidence": [
    {
      "type": "pubmed",
      "pmid": "12345678",
      "title": "...",
      "snippet": "...",
      "relation_support": 0.1
    }
  ],
  "missing_mechanism": [
    "molecular interaction",
    "cellular pathway"
  ],
  "explanation": "While turmeric contains curcumin with anti-inflammatory properties, there is no evidence of direct therapeutic efficacy against liver cancer. The claim lacks biochemical pathway evidence and clinical validation."
}
```

## Deployment Architecture

### Docker Containers
- **Backend**: Flask app with Gunicorn (4 workers)
- **Frontend**: React served via Node.js
- **KG DB**: SQLite (or Neo4j for advanced features)

### Local Development
```bash
docker-compose up -d
# Backend: http://localhost:5000
# Frontend: http://localhost:3000
```

### Production Considerations
- Use production-grade database (PostgreSQL, Neo4j)
- Implement caching layer (Redis)
- Use load balancer (Nginx)
- Enable HTTPS/TLS
- Implement rate limiting
- Add monitoring (Prometheus, Grafana)
- Use secrets management (Vault)

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Tailwind CSS, Cytoscape.js |
| Backend | Flask, Python 3.10+ |
| ML/NLP | PyTorch, Transformers, spaCy, DGL/PyG |
| Bioinformatics | BioPython, UMLS, DisGeNET |
| Database | SQLite (dev), PostgreSQL (prod) |
| Graph DB | Neo4j (optional) |
| Containers | Docker, Docker Compose |
| CI/CD | GitHub Actions |
| Testing | pytest, Jest |
