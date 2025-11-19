"""Tests for API routes."""

import json


def test_verify_endpoint(client):
    """Test verification endpoint."""
    response = client.post('/api/verify', json={
        'claim': 'Turmeric reduces inflammation',
        'domain': 'medicine'
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'verdict' in data
    assert 'confidence' in data
    assert 'triples' in data


def test_verify_missing_claim(client):
    """Test verification with missing claim."""
    response = client.post('/api/verify', json={})
    assert response.status_code == 400


def test_extract_triples(client):
    """Test triple extraction."""
    response = client.post('/api/extract/triples', json={
        'text': 'Aspirin inhibits platelet aggregation through COX-1 inhibition.'
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'triples' in data


def test_kg_search(client):
    """Test knowledge graph search."""
    response = client.get('/api/kg/search?q=turmeric&limit=5')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'results' in data


def test_kg_node_details(client):
    """Test KG node details endpoint."""
    response = client.get('/api/kg/node/concept_001')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'id' in data
    assert 'connected_entities' in data


def test_batch_verify(client):
    """Test batch verification."""
    response = client.post('/api/batch/verify', json={
        'claims': [
            {'text': 'Claim 1'},
            {'text': 'Claim 2'}
        ]
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['total'] == 2


def test_health_endpoint(client):
    """Test health endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'ok'


def test_admin_metrics(client):
    """Test admin metrics."""
    response = client.get('/api/admin/metrics')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'requests_processed' in data


def test_service_status(client):
    """Test service status."""
    response = client.get('/api/status/services')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'backend' in data
    assert 'kg_database' in data
