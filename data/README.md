# Data Ingestion and Management

This document describes the datasets, sources, and ingestion procedures for the Causal-NLP Engine.

## Dataset Overview

### Primary Datasets

| Dataset | Source | Focus | Size | License |
|---------|--------|-------|------|---------|
| **SciFact** | FEVER | Fact verification in scientific papers | ~1.4K claims | CC-BY |
| **FEVER-SCI** | Facebook FAIR | Scientific claim verification | ~4.7K claims | CC-BY |
| **CoAID** | - | COVID-19 misinformation | ~5K+ claims | CC-BY-4.0 |
| **HealthVer** | - | Health-related claims | ~13K claims | MIT |
| **ReCOVery** | - | COVID recovery claim verification | ~1.1K claims | CC-BY-4.0 |
| **BioCause** | BioNLP 2009 | Biomedical causality extraction | ~1K annotated sentences | Public |
| **EventCausality** | NLP literature | General causality extraction | ~25K event pairs | Public |

### Knowledge Bases

| KB | Coverage | Scale | License |
|----|----------|-------|---------|
| **UMLS** | Medical terminology & concepts | 4.2M+ concepts | NLM License |
| **DisGeNET** | Gene-disease associations | 600K+ associations | CC-BY-4.0 |
| **CTD** | Chemical-gene-disease interactions | 500K+ interactions | Public |

## Directory Structure

```
data/
├── raw/                          # Original downloaded files
│   ├── scifact/
│   ├── fever_sci/
│   ├── coaid/
│   ├── healthver/
│   ├── recovery/
│   ├── biocause/
│   ├── eventcausality/
│   ├── kg/
│   │   ├── umls/
│   │   ├── disgenet/
│   │   └── ctd/
│   └── README.md                 # Data sources & citations
├── processed/
│   ├── claims.jsonl             # Unified claim format
│   ├── triples.jsonl            # Extracted triples
│   ├── kg_graph.json            # Merged knowledge graph
│   └── train_test_split.json    # Splits for ML
└── README.md                    # This file
```

## Unified Data Schema

### Claim Format (JSONL)

```json
{
  "claim_id": "scifact_001",
  "claim_text": "Turmeric consumption reduces inflammation",
  "source": "SciFact",
  "label": "SUPPORTS",
  "claim_domain": "medicine",
  "triples": [
    {
      "subject": "turmeric",
      "relation": "reduces",
      "object": "inflammation",
      "confidence": 0.85
    }
  ],
  "evidence_sentences": [
    {
      "pmid": "12345678",
      "text": "Curcumin, the active ingredient in turmeric, has well-documented anti-inflammatory properties.",
      "relevance_score": 0.92
    }
  ],
  "pmids": ["12345678", "87654321"],
  "annotated_by": "crowdsourced | expert | automatic",
  "annotation_date": "2024-01-15"
}
```

### Triple Format

```json
{
  "subject": "entity_name",
  "subject_type": "compound | gene | disease | protein",
  "relation": "cures | causes | prevents | treats | correlates_with",
  "object": "entity_name",
  "object_type": "disease | protein | pathway",
  "confidence": 0.85,
  "source": "extracted | kg | literature",
  "supporting_evidence": ["pmid_1", "pmid_2"]
}
```

## Data Ingestion Scripts

All scripts are located in `scripts/` directory.

### 1. SciFact Ingestion

```bash
python scripts/ingest_scifact.py \
  --output data/raw/scifact/claims.jsonl \
  --include-evidence
```

**Source**: https://github.com/allenai/scifact

### 2. FEVER-SCI Ingestion

```bash
python scripts/ingest_fever_sci.py \
  --output data/raw/fever_sci/claims.jsonl
```

**Source**: https://github.com/allenai/fever-sci

### 3. CoAID Ingestion

```bash
python scripts/ingest_coaid.py \
  --output data/raw/coaid/claims.jsonl
```

**Source**: https://github.com/ece-ubc/coaid

### 4. PubMed Collection

```bash
python scripts/collect_pubmed.py \
  --query "turmeric AND cancer" \
  --max-results 5000 \
  --output data/raw/pubmed/
```

**Requirements**:
- Biopython with NCBI Entrez (rate-limited to 3 requests/second)
- Email configured for NCBI

### 5. BioCause Ingestion

```bash
python scripts/ingest_biocause.py \
  --output data/raw/biocause/causal_sentences.jsonl
```

### 6. Knowledge Graph Ingestion

```bash
# UMLS
python scripts/ingest_umls.py \
  --input data/raw/kg/umls/ \
  --output data/processed/kg_umls.json

# DisGeNET
python scripts/ingest_disgenet.py \
  --output data/processed/kg_disgenet.json

# CTD
python scripts/ingest_ctd.py \
  --output data/processed/kg_ctd.json
```

## Data Processing Pipeline

### Unified Processing

```bash
python scripts/process_all_datasets.py \
  --input-dirs data/raw/* \
  --output data/processed/claims.jsonl \
  --validate
```

**Steps**:
1. Load all dataset files
2. Normalize to unified schema
3. Deduplicate claims
4. Validate JSON schemas
5. Generate train/test splits
6. Create KG graph

### Output

```
data/processed/
├── claims.jsonl                 # 15K+ claims
├── triples.jsonl               # 45K+ triples
├── kg_graph.json               # Merged KG
└── splits/
    ├── train_claims.jsonl      # 70%
    ├── val_claims.jsonl        # 10%
    └── test_claims.jsonl       # 20%
```

## Citation & Licensing

### Academic Use

If using these datasets in research, please cite:

```bibtex
@dataset{scifact,
  title={SCIFACT: Verifying Scientific Claims with Structured Evidence},
  author={Wadden, David and Lo, Kyle and Wang, Lucy Lu and Walsh, Shenwu and Wang, Ian and Cohan, Arman},
  year={2020}
}

@dataset{fevercovid,
  title={FEVER-SCI: A Corpus for Scientific Claim Verification},
  author={Thakur, Nishant and Cohan, Arman},
  year={2021}
}
```

### License Compliance

- **MIT Datasets**: Can be used freely with attribution
- **CC-BY-4.0**: Attribution required, commercial use allowed
- **UMLS**: Restricted license, requires registration at nlm.nih.gov
- **DisGeNET**: CC-BY-4.0 license
- **CTD**: Public domain

## Accessing Pre-Processed Data

For quicker setup, download pre-processed data:

```bash
# Download all processed datasets (~2GB)
make download-data

# Or individually
make download-scifact
make download-fever-sci
make download-coaid
```

## Data Statistics

```
Total Claims: ~15,000
Total Triples Extracted: ~45,000
Average Claim Length: 15 words
Average Evidence Documents per Claim: 3
Knowledge Graph Size: ~1.5M nodes, ~5M edges
```

## Quality Assurance

### Validation Rules

- Claim text length: 5-500 characters
- Triple confidence: 0.0-1.0
- Relations: Predefined vocabulary
- Entity types: Standardized taxonomy

### Testing

```bash
python scripts/validate_data.py --data data/processed/claims.jsonl
```

## Updating Datasets

To refresh datasets with latest publications:

```bash
# Update all sources
make refresh-data

# Or specific sources
python scripts/ingest_pubmed.py --refresh
```

---

**Last Updated**: 2025-01-15
**Maintained By**: Causal-NLP Team
