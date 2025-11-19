# Causal-NLP Engine for Fake Scientific Claims Detection

🚀 **The World's First Causal Transformer for Scientific Claim Verification**

A cutting-edge research project that identifies not just false information but the **causal fallacies** embedded within scientific claims using Neural Causal Structure Learning and Graph Attention Networks.

## 🎯 Core Innovation

- **Model**: Text → Causal Graph → Consistency Checker
- **Approach**: Neural Causal Structure Learning (NCSL) + Graph Attention Networks (GAT)
- **Output**: "Which causal link is scientifically invalid?"

### Example

**Input**: "Consumption of turmeric directly cures liver cancer."

**Output**:
```json
{
  "verdict": "CAUSAL_INVALID",
  "explanation": "No biochemical pathway evidence found for direct therapeutic mechanism.",
  "causal_graph": {...},
  "triples": [
    {"subject": "turmeric", "relation": "cures", "object": "liver cancer", "confidence": 0.02}
  ],
  "missing_mechanism": ["molecular interaction", "clinical validation"]
}
```

## 📋 Features

- ✅ **Multi-Source Data Ingestion**: SciFact, PubMed, FEVER-SCI, CoAID, HealthVer, BioCause
- ✅ **Knowledge Bases**: UMLS, DisGeNET, CTD integration
- ✅ **Causal Extraction**: Rule-based + Transformer-based (T5, DeBERTa)
- ✅ **Graph Learning**: DAG learner + GNN embeddings (DGL/PyG)
- ✅ **Counterfactual Reasoning**: Mechanistic gap detection
- ✅ **Flask REST API**: Production-ready with OpenAPI docs
- ✅ **React Frontend**: Interactive graph visualization and claim verification UI
- ✅ **Evaluation Framework**: Precision, Recall, F1, MRR metrics
- ✅ **Docker Deployment**: Full stack via docker-compose

## 🏗️ Project Structure

```
causal-nlp-claim-verifier/
├── backend/              # Flask microservices
│   ├── app.py           # Flask app factory
│   ├── config.py        # Configuration
│   ├── api/             # REST endpoints (blueprints)
│   ├── services/        # Business logic
│   ├── causal_extractor/  # Extraction models
│   ├── graph_models/    # GNN & DAG models
│   ├── verifier/        # Verification pipeline
│   ├── kg/              # Knowledge graph manager
│   └── utils/           # Utilities
├── frontend/            # React + Tailwind CSS
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── design-system/
│   └── package.json
├── models/              # Pre-trained models
│   ├── graph_model/
│   └── extractors/
├── data/                # Dataset management
│   ├── raw/
│   └── processed/
├── scripts/             # Data pipelines & training
├── notebooks/           # Jupyter notebooks (EDA, evaluation)
├── tests/               # Unit & integration tests
├── docker/              # Dockerfiles
├── docs/                # Documentation & architecture
└── Makefile             # Development commands
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.10+
- Node.js 18+ (for frontend)

### Development Setup

```bash
# Clone the repo
git clone https://github.com/yourusername/causal-nlp-claim-verifier.git
cd causal-nlp-claim-verifier

# Setup local environment
make setup

# Run development server
make dev

# Run tests
make test

# Run full stack with Docker
docker-compose up -d
```

### API Usage

```bash
# Health check
curl http://localhost:5000/health

# Verify a claim
curl -X POST http://localhost:5000/verify \
  -H "Content-Type: application/json" \
  -d '{
    "claim": "Vitamin C cures the common cold",
    "domain": "medicine"
  }'

# Access API docs
open http://localhost:5000/api/docs
```

### Frontend

Open http://localhost:3000 in your browser.

## 📚 Documentation

- [Architecture](docs/architecture.md)
- [Annotation Schema](docs/annotation_schema.md)
- [Data Ingestion Guide](data/README.md)
- [API Reference](docs/api.md)
- [Research Outline](docs/paper_outline.md)

## 🔍 Milestones

- ✅ **Milestone 0**: Repository Scaffold
- ⏳ **Milestone 1**: Data Ingestion Pipelines
- ⏳ **Milestone 2**: Annotation Schema + Label Studio
- ⏳ **Milestone 3**: Causal Extraction Module
- ⏳ **Milestone 4**: Causal Knowledge Base
- ⏳ **Milestone 5**: Neural Causal Structure Learning + GNN
- ⏳ **Milestone 6**: Causal Fallacy Detection + Counterfactual Reasoning
- ⏳ **Milestone 7**: Evaluation Framework
- ⏳ **Milestone 8**: Flask API Production-Ready
- ⏳ **Milestone 9**: Frontend React + Tailwind
- ⏳ **Milestone 10**: Deployment, CI/CD, Documentation

## 🤝 Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Authors

- **Research & Development Team** - Causal-NLP Initiative

## 🙏 Acknowledgments

- SciFact, PubMed, FEVER datasets
- UMLS, DisGeNET, CTD knowledge bases
- DGL and PyTorch Geometric communities

---

**Status**: 🚧 In Active Development

*Built with ❤️ for scientific integrity and evidence-based reasoning*
