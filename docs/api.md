# API Reference

## Base URL

```
http://localhost:5000
```

## Health & Status

### Health Check

```http
GET /health
```

**Response** (200 OK):
```json
{
  "status": "healthy",
  "service": "causal-nlp-engine",
  "version": "0.1.0",
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

### Service Info

```http
GET /
```

**Response** (200 OK):
```json
{
  "service": "Causal-NLP Engine for Fake Scientific Claims Detection",
  "version": "0.1.0",
  "status": "running",
  "api_prefix": "/api",
  "docs": "/api/docs"
}
```

---

## Verification Endpoints

### Verify Claim

```http
POST /api/verify
Content-Type: application/json
```

**Request Body**:
```json
{
  "claim": "Vitamin C cures the common cold",
  "domain": "medicine",
  "include_graph": true,
  "include_evidence": true,
  "threshold": 0.5
}
```

**Response** (200 OK):
```json
{
  "claim_id": "claim_8ac0c8a9",
  "verdict": "CORRELATION_NOT_CAUSAL",
  "confidence": 0.87,
  "explanation": "While Vitamin C may support immune function, evidence does not support direct causal link to common cold cure.",
  "triples": [
    {
      "subject": "Vitamin C",
      "relation": "cures",
      "object": "common cold",
      "confidence": 0.15,
      "status": "INVALID"
    }
  ],
  "causal_graph": {
    "nodes": [
      {"id": "vitamin_c", "label": "Vitamin C", "type": "compound"},
      {"id": "immune_function", "label": "Immune Function", "type": "biological_process"},
      {"id": "cold", "label": "Common Cold", "type": "disease"}
    ],
    "edges": [
      {"source": "vitamin_c", "target": "immune_function", "confidence": 0.82},
      {"source": "immune_function", "target": "cold", "confidence": 0.45}
    ]
  },
  "evidence": [
    {
      "type": "pubmed",
      "pmid": "12345678",
      "title": "Vitamin C and the Common Cold: A Meta-Analysis",
      "snippet": "Meta-analysis shows no significant reduction in cold duration with Vitamin C supplementation.",
      "relation_support": 0.15,
      "url": "https://pubmed.ncbi.nlm.nih.gov/12345678/"
    }
  ],
  "missing_mechanism": [
    "Direct viral inhibition pathway",
    "Clinical efficacy at claimed dosage"
  ],
  "processing_time_ms": 342
}
```

**Parameters**:
- `claim` (string, required): The scientific claim to verify
- `domain` (string, optional): Domain context (medicine, biology, physics)
- `include_graph` (boolean, optional): Include causal graph in response (default: true)
- `include_evidence` (boolean, optional): Include evidence sentences (default: true)
- `threshold` (float, optional): Confidence threshold 0.0-1.0 (default: 0.5)

**Response Codes**:
- `200 OK`: Verification completed
- `400 Bad Request`: Invalid request format
- `422 Unprocessable Entity`: Invalid claim text
- `500 Internal Server Error`: Server error

---

## Knowledge Graph Endpoints

### Get Node

```http
GET /api/kg/node/{node_id}
```

**Response** (200 OK):
```json
{
  "id": "turmeric",
  "label": "Turmeric",
  "type": "compound",
  "aliases": ["curcuma", "curcumin"],
  "properties": {
    "chemical_formula": "C21H20O6",
    "mesh_id": "D046793"
  },
  "connected_entities": [
    {
      "target": "inflammation",
      "relation": "reduces",
      "confidence": 0.82,
      "sources": ["pubmed:123", "umls:456"]
    }
  ]
}
```

### Search Knowledge Graph

```http
GET /api/kg/search?q={query}&limit={limit}
```

**Query Parameters**:
- `q` (string, required): Search term
- `limit` (integer, optional): Maximum results (default: 10, max: 100)
- `entity_type` (string, optional): Filter by type (compound, gene, disease, protein)

**Response** (200 OK):
```json
{
  "query": "turmeric",
  "results": [
    {
      "id": "turmeric",
      "label": "Turmeric",
      "type": "compound",
      "score": 1.0
    },
    {
      "id": "curcumin",
      "label": "Curcumin",
      "type": "compound",
      "score": 0.95
    }
  ],
  "total": 2
}
```

### Get Subgraph

```http
GET /api/kg/subgraph?center={entity_id}&depth={depth}
```

**Query Parameters**:
- `center` (string, required): Central entity ID
- `depth` (integer, optional): Traversal depth (default: 2, max: 5)

**Response** (200 OK):
```json
{
  "center": "turmeric",
  "nodes": [...],
  "edges": [...],
  "depth": 2
}
```

---

## Batch Verification

### Verify Multiple Claims

```http
POST /api/batch/verify
Content-Type: application/json
```

**Request Body**:
```json
{
  "claims": [
    {"text": "Claim 1", "domain": "medicine"},
    {"text": "Claim 2", "domain": "biology"}
  ]
}
```

**Response** (200 OK):
```json
{
  "batch_id": "batch_abc123",
  "results": [
    {...verification result 1...},
    {...verification result 2...}
  ],
  "processing_time_ms": 1250
}
```

---

## Error Responses

### 400 Bad Request

```json
{
  "error": "Bad Request",
  "message": "Invalid JSON format",
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

### 422 Unprocessable Entity

```json
{
  "error": "Unprocessable Entity",
  "message": "Claim text must be between 5 and 500 characters",
  "field": "claim",
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

### 500 Internal Server Error

```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred during verification",
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

---

## Rate Limiting

- Standard: 100 requests/minute per IP
- Batch: 10 requests/minute

Headers returned:
- `X-RateLimit-Limit`: Request limit
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Reset timestamp

---

## Authentication (Future)

API key authentication will be added in a future release:

```http
Authorization: Bearer YOUR_API_KEY
```

---

## Pagination

For list endpoints, use:

```http
GET /api/resource?page=1&per_page=50
```

**Response**:
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 1000,
    "pages": 20
  }
}
```

---

## Webhooks (Future)

For async processing of large batches:

```http
POST /api/verify/async
Content-Type: application/json
```

**Request**:
```json
{
  "claims": [...],
  "webhook_url": "https://your-domain.com/callback"
}
```

---

**API Version**: 0.1.0  
**Last Updated**: 2025-01-15
