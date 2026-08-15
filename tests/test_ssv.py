"""
Tests for Semantic State Vector (SSV) generation
Tests edge cases, intent vector extraction, confidence scoring, and hash consistency
"""

import pytest
import json
from ssv_core import SSVGenerator, SemanticStateVector
from tests.conftest import sample_observations, sample_constraints, sample_decisions


class TestSSVGeneration:
    """Test SSV generation functionality"""
    
    def test_generate_ssv_basic(self, sample_observations, sample_constraints, sample_decisions):
        """Test basic SSV generation"""
        ssv = SSVGenerator.generate_ssv(
            agent_id="test_agent",
            current_task="Test task",
            observations=sample_observations,
            decisions_made=sample_decisions,
            constraints=sample_constraints,
            confidence=0.8
        )
        
        assert isinstance(ssv, SemanticStateVector)
        assert ssv.agent_id == "test_agent"
        assert ssv.confidence_score == 0.8
        assert ssv.state_hash is not None
        assert len(ssv.state_hash) == 64  # SHA-256 hash length
        assert ssv.version == "1.0"
    
    def test_generate_ssv_empty_observations(self):
        """Test SSV generation with empty observations"""
        ssv = SSVGenerator.generate_ssv(
            agent_id="test_agent",
            current_task="Test task",
            observations={},
            decisions_made=[],
            constraints={},
            confidence=0.8
        )
        
        assert ssv.intent_vector is not None
        assert len(ssv.intent_vector) > 0
    
    def test_generate_ssv_long_decisions(self):
        """Test SSV generation truncates decisions to last 5"""
        long_decisions = [f"decision_{i}" for i in range(10)]
        ssv = SSVGenerator.generate_ssv(
            agent_id="test_agent",
            current_task="Test task",
            observations={},
            decisions_made=long_decisions,
            constraints={},
            confidence=0.8
        )
        
        assert len(ssv.decision_history) == 5
        assert ssv.decision_history == long_decisions[-5:]
    
    def test_ssv_serialization(self, sample_observations, sample_constraints, sample_decisions):
        """Test SSV to_compact and from_compact methods"""
        ssv = SSVGenerator.generate_ssv(
            agent_id="test_agent",
            current_task="Test task",
            observations=sample_observations,
            decisions_made=sample_decisions,
            constraints=sample_constraints,
            confidence=0.8
        )
        
        # Serialize
        compact = ssv.to_compact()
        assert isinstance(compact, str)
        
        # Deserialize
        restored = SemanticStateVector.from_compact(compact)
        assert restored.agent_id == ssv.agent_id
        assert restored.state_hash == ssv.state_hash
        assert restored.confidence_score == ssv.confidence_score


class TestIntentVectorExtraction:
    """Test intent vector extraction logic"""
    
    def test_extract_intent_with_numeric_values(self):
        """Test intent extraction with numeric observations"""
        observations = {
            "score": 0.95,
            "count": 42,
            "ratio": 0.75
        }
        
        intent = SSVGenerator._extract_intent("test task", observations)
        
        assert "score" in intent
        assert "count" in intent
        assert "ratio" in intent
        assert intent["score"] == 0.95
        assert intent["count"] == 42.0
    
    def test_extract_intent_with_string_values(self):
        """Test intent extraction with short string observations"""
        observations = {
            "status": "active",
            "mode": "fast"
        }
        
        intent = SSVGenerator._extract_intent("test task", observations)
        
        assert "has_status" in intent
        assert "has_mode" in intent
        assert intent["has_status"] == 1.0
    
    def test_extract_intent_with_long_strings(self):
        """Test intent extraction ignores long strings"""
        observations = {
            "description": "This is a very long description that should be ignored"
        }
        
        intent = SSVGenerator._extract_intent("test task", observations)
        
        # Long strings should not be included
        assert "description" not in intent
    
    def test_extract_intent_empty_observations(self):
        """Test intent extraction with empty observations"""
        intent = SSVGenerator._extract_intent("test task", {})
        
        assert intent is not None
        assert len(intent) > 0
        assert "task_acknowledged" in intent


class TestConfidenceScoring:
    """Test confidence scoring in SSV"""
    
    def test_confidence_within_range(self, sample_observations, sample_constraints, sample_decisions):
        """Test confidence scores are within valid range"""
        for confidence in [0.0, 0.5, 0.8, 1.0]:
            ssv = SSVGenerator.generate_ssv(
                agent_id="test_agent",
                current_task="Test task",
                observations=sample_observations,
                decisions_made=sample_decisions,
                constraints=sample_constraints,
                confidence=confidence
            )
            
            assert 0.0 <= ssv.confidence_score <= 1.0
            assert ssv.confidence_score == confidence


class TestHashConsistency:
    """Test hash consistency and uniqueness"""
    
    def test_hash_deterministic(self, sample_observations, sample_constraints, sample_decisions):
        """Test same inputs produce same hash"""
        ssv1 = SSVGenerator.generate_ssv(
            agent_id="test_agent",
            current_task="Test task",
            observations=sample_observations,
            decisions_made=sample_decisions,
            constraints=sample_constraints,
            confidence=0.8
        )
        
        ssv2 = SSVGenerator.generate_ssv(
            agent_id="test_agent",
            current_task="Test task",
            observations=sample_observations,
            decisions_made=sample_decisions,
            constraints=sample_constraints,
            confidence=0.8
        )
        
        assert ssv1.state_hash == ssv2.state_hash
    
    def test_hash_unique_for_different_inputs(self, sample_observations, sample_constraints, sample_decisions):
        """Test different inputs produce different hashes"""
        ssv1 = SSVGenerator.generate_ssv(
            agent_id="agent_1",
            current_task="Task 1",
            observations=sample_observations,
            decisions_made=sample_decisions,
            constraints=sample_constraints,
            confidence=0.8
        )
        
        ssv2 = SSVGenerator.generate_ssv(
            agent_id="agent_2",
            current_task="Task 2",
            observations=sample_observations,
            decisions_made=sample_decisions,
            constraints=sample_constraints,
            confidence=0.8
        )
        
        assert ssv1.state_hash != ssv2.state_hash
    
    def test_hash_changes_with_observations(self, sample_observations, sample_constraints, sample_decisions):
        """Test hash changes when observations change"""
        ssv1 = SSVGenerator.generate_ssv(
            agent_id="test_agent",
            current_task="Test task",
            observations=sample_observations,
            decisions_made=sample_decisions,
            constraints=sample_constraints,
            confidence=0.8
        )
        
        modified_observations = sample_observations.copy()
        modified_observations["new_field"] = "value"
        
        ssv2 = SSVGenerator.generate_ssv(
            agent_id="test_agent",
            current_task="Test task",
            observations=modified_observations,
            decisions_made=sample_decisions,
            constraints=sample_constraints,
            confidence=0.8
        )
        
        assert ssv1.state_hash != ssv2.state_hash
