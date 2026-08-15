"""
Tests for ContextFlow API
Tests REST endpoints, request validation, error responses, and WebSocket connections
"""

import pytest
from fastapi.testclient import TestClient
from contextflow_api import app


@pytest.fixture
def client():
    """Test client for FastAPI app"""
    return TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check(self, client):
        """Test health check returns healthy status"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "agents_tracked" in data
        assert "journal_entries" in data


class TestSSVGeneration:
    """Test SSV generation endpoint"""
    
    def test_generate_ssv_success(self, client):
        """Test successful SSV generation"""
        request_data = {
            "agent_id": "test_agent",
            "current_task": "Test task",
            "observations": {"data": "value"},
            "decisions_made": ["decision1"],
            "constraints": {"max_items": 10},
            "confidence": 0.8
        }
        
        response = client.post("/ssv/generate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["agent_id"] == "test_agent"
        assert "state_hash" in data
        assert "confidence" in data
        assert "ssv_compact" in data
    
    def test_generate_ssv_invalid_request(self, client):
        """Test SSV generation with invalid request"""
        request_data = {
            "agent_id": "test",
            # Missing required fields
        }
        
        response = client.post("/ssv/generate", json=request_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_generate_ssv_caches_result(self, client):
        """Test SSV generation caches the result"""
        request_data = {
            "agent_id": "cache_test",
            "current_task": "Test task",
            "observations": {"data": "value"},
            "decisions_made": [],
            "constraints": {},
            "confidence": 0.8
        }
        
        response1 = client.post("/ssv/generate", json=request_data)
        hash1 = response1.json()["state_hash"]
        
        response2 = client.post("/ssv/generate", json=request_data)
        hash2 = response2.json()["state_hash"]
        
        # Same input should produce same hash
        assert hash1 == hash2


class TestConsensusCheck:
    """Test consensus check endpoint"""
    
    def test_check_consensus_success(self, client):
        """Test successful consensus check"""
        # First, generate SSVs for both agents
        client.post("/ssv/generate", json={
            "agent_id": "agent_a",
            "current_task": "Task A",
            "observations": {"data": "value"},
            "decisions_made": [],
            "constraints": {},
            "confidence": 0.8
        })
        
        client.post("/ssv/generate", json={
            "agent_id": "agent_b",
            "current_task": "Task B",
            "observations": {"data": "value"},
            "decisions_made": [],
            "constraints": {},
            "confidence": 0.8
        })
        
        # Check consensus
        response = client.post("/consensus/check", json={
            "agent_a_id": "agent_a",
            "agent_b_id": "agent_b"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "consensus_level" in data
        assert "divergence_score" in data
        assert "mismatches" in data
        assert "recommended_action" in data
    
    def test_check_consensus_agents_not_found(self, client):
        """Test consensus check with non-existent agents"""
        response = client.post("/consensus/check", json={
            "agent_a_id": "nonexistent_a",
            "agent_b_id": "nonexistent_b"
        })
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data


class TestMultiAgentConsensus:
    """Test multi-agent consensus endpoint"""
    
    def test_multi_agent_consensus(self, client):
        """Test multi-agent consensus check"""
        # Generate SSVs for multiple agents
        for i in range(3):
            client.post("/ssv/generate", json={
                "agent_id": f"agent_{i}",
                "current_task": f"Task {i}",
                "observations": {"data": f"value_{i}"},
                "decisions_made": [],
                "constraints": {},
                "confidence": 0.8
            })
        
        response = client.post("/consensus/multi-agent", json=["agent_0", "agent_1", "agent_2"])
        
        assert response.status_code == 200
        data = response.json()
        assert "system_health" in data
        assert "consensus_graph" in data
        assert "pairwise_results" in data
        assert "total_pairs_checked" in data


class TestStateUpdate:
    """Test state update endpoint"""
    
    def test_update_agent_state(self, client):
        """Test updating agent state"""
        # First generate SSV
        client.post("/ssv/generate", json={
            "agent_id": "update_test",
            "current_task": "Test task",
            "observations": {"data": "value"},
            "decisions_made": [],
            "constraints": {},
            "confidence": 0.8
        })
        
        # Update state
        response = client.post("/state/update", json={
            "agent_id": "update_test",
            "action": "update_data",
            "state_delta": {"new_field": "new_value"}
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "previous_hash" in data
        assert "new_hash" in data
    
    def test_update_nonexistent_agent(self, client):
        """Test updating non-existent agent"""
        response = client.post("/state/update", json={
            "agent_id": "nonexistent",
            "action": "update",
            "state_delta": {}
        })
        
        assert response.status_code == 404


class TestJournalEndpoints:
    """Test journal-related endpoints"""
    
    def test_get_agent_history(self, client):
        """Test getting agent history"""
        # Generate SSV to create journal entry
        client.post("/ssv/generate", json={
            "agent_id": "history_test",
            "current_task": "Test task",
            "observations": {"data": "value"},
            "decisions_made": [],
            "constraints": {},
            "confidence": 0.8
        })
        
        response = client.get("/journal/agent/history_test")
        
        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == "history_test"
        assert "entries" in data
        assert "history" in data
    
    def test_get_nonexistent_agent_history(self, client):
        """Test getting history for non-existent agent"""
        response = client.get("/journal/agent/nonexistent")
        
        assert response.status_code == 404
    
    def test_find_divergence_point(self, client):
        """Test finding divergence point between agents"""
        # Generate SSVs for two agents
        client.post("/ssv/generate", json={
            "agent_id": "div_a",
            "current_task": "Task",
            "observations": {"data": "value"},
            "decisions_made": [],
            "constraints": {},
            "confidence": 0.8
        })
        
        client.post("/ssv/generate", json={
            "agent_id": "div_b",
            "current_task": "Task",
            "observations": {"data": "value"},
            "decisions_made": [],
            "constraints": {},
            "confidence": 0.8
        })
        
        response = client.get("/journal/divergence/div_a/div_b")
        
        assert response.status_code == 200
        data = response.json()
        assert "diverged" in data
    
    def test_export_journal(self, client):
        """Test exporting journal as JSON"""
        response = client.get("/journal/export")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestMetricsEndpoint:
    """Test metrics endpoint"""
    
    def test_get_metrics(self, client):
        """Test getting system metrics"""
        response = client.get("/metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert "agents_tracked" in data
        assert "journal_entries" in data
        assert "critical_events" in data
        assert "active_connections" in data
        assert "hallucination_prevention_rate" in data


class TestRequestValidation:
    """Test request validation"""
    
    def test_invalid_json(self, client):
        """Test invalid JSON request"""
        response = client.post("/ssv/generate", data="invalid json")
        
        assert response.status_code == 422
    
    def test_missing_required_fields(self, client):
        """Test missing required fields in request"""
        response = client.post("/ssv/generate", json={
            "agent_id": "test"
            # Missing other required fields
        })
        
        assert response.status_code == 422


class TestErrorResponses:
    """Test error response handling"""
    
    def test_404_error_format(self, client):
        """Test 404 error has proper format"""
        response = client.get("/nonexistent/endpoint")
        
        assert response.status_code == 404
    
    def test_method_not_allowed(self, client):
        """Test method not allowed error"""
        response = client.get("/ssv/generate")
        
        assert response.status_code == 405
