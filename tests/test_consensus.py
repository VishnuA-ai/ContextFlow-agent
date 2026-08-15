"""
Tests for Dynamic Consensus Protocol
Tests GREEN, YELLOW, RED consensus scenarios, divergence scores, and mismatch detection
"""

import pytest
from ssv_core import DynamicConsensusProtocol, ConsensusLevel, SSVGenerator
from tests.conftest import scout_ssv, critic_ssv


class TestConsensusScenarios:
    """Test different consensus scenarios"""
    
    def test_green_consensus(self, scout_ssv):
        """Test GREEN consensus when agents are aligned"""
        # Create identical SSV
        aligned_ssv = SSVGenerator.generate_ssv(
            agent_id="aligned_agent",
            current_task=scout_ssv.intent_vector.get("task", "test"),
            observations=scout_ssv.belief_state,
            decisions_made=scout_ssv.decision_history,
            constraints=scout_ssv.constraint_set,
            confidence=scout_ssv.confidence_score
        )
        
        result = DynamicConsensusProtocol.compare_states(scout_ssv, aligned_ssv)
        
        assert result.level == ConsensusLevel.GREEN
        assert result.divergence_score < DynamicConsensusProtocol.WARNING_DRIFT_THRESHOLD
        assert result.recommended_action == "PROCEED: Agents aligned"
        assert result.sync_payload is None
    
    def test_yellow_consensus(self, scout_ssv):
        """Test YELLOW consensus with minor drift"""
        # Create SSV with minor divergence
        divergent_observations = scout_ssv.belief_state.copy()
        if "papers_found" in divergent_observations:
            divergent_observations["papers_found"] += 1
        
        divergent_ssv = SSVGenerator.generate_ssv(
            agent_id="divergent_agent",
            current_task=scout_ssv.intent_vector.get("task", "test"),
            observations=divergent_observations,
            decisions_made=scout_ssv.decision_history,
            constraints=scout_ssv.constraint_set,
            confidence=scout_ssv.confidence_score
        )
        
        result = DynamicConsensusProtocol.compare_states(scout_ssv, divergent_ssv)
        
        # May be GREEN or YELLOW depending on the divergence
        assert result.level in [ConsensusLevel.GREEN, ConsensusLevel.YELLOW]
        assert result.divergence_score < DynamicConsensusProtocol.CRITICAL_DRIFT_THRESHOLD
    
    def test_red_consensus(self, scout_ssv):
        """Test RED consensus with critical divergence"""
        # Create SSV with major divergence
        divergent_observations = {"completely_different": "data"}
        divergent_constraints = {"different_constraints": True}
        
        divergent_ssv = SSVGenerator.generate_ssv(
            agent_id="divergent_agent",
            current_task="Different task entirely",
            observations=divergent_observations,
            decisions_made=["different_decision"],
            constraints=divergent_constraints,
            confidence=0.5
        )
        
        result = DynamicConsensusProtocol.compare_states(scout_ssv, divergent_ssv)
        
        assert result.level == ConsensusLevel.RED
        assert result.divergence_score >= DynamicConsensusProtocol.CRITICAL_DRIFT_THRESHOLD
        assert "BLOCK" in result.recommended_action
        assert result.sync_payload is not None


class TestDivergenceScore:
    """Test divergence score calculation"""
    
    def test_divergence_score_range(self, scout_ssv):
        """Test divergence score is always between 0 and 1"""
        divergent_ssv = SSVGenerator.generate_ssv(
            agent_id="divergent",
            current_task="Different",
            observations={},
            decisions_made=[],
            constraints={},
            confidence=0.5
        )
        
        result = DynamicConsensusProtocol.compare_states(scout_ssv, divergent_ssv)
        
        assert 0.0 <= result.divergence_score <= 1.0
    
    def test_divergence_zero_for_identical(self, scout_ssv):
        """Test divergence is zero for identical states"""
        identical_ssv = SSVGenerator.generate_ssv(
            agent_id="identical",
            current_task=scout_ssv.intent_vector.get("task", "test"),
            observations=scout_ssv.belief_state,
            decisions_made=scout_ssv.decision_history,
            constraints=scout_ssv.constraint_set,
            confidence=scout_ssv.confidence_score
        )
        
        result = DynamicConsensusProtocol.compare_states(scout_ssv, identical_ssv)
        
        assert result.divergence_score == 0.0
    
    def test_divergence_increases_with_differences(self, scout_ssv):
        """Test divergence increases with more differences"""
        # Small difference
        small_diff_observations = scout_ssv.belief_state.copy()
        if "papers_found" in small_diff_observations:
            small_diff_observations["papers_found"] += 1
        
        small_ssv = SSVGenerator.generate_ssv(
            agent_id="small_diff",
            current_task=scout_ssv.intent_vector.get("task", "test"),
            observations=small_diff_observations,
            decisions_made=scout_ssv.decision_history,
            constraints=scout_ssv.constraint_set,
            confidence=scout_ssv.confidence_score
        )
        
        # Large difference
        large_ssv = SSVGenerator.generate_ssv(
            agent_id="large_diff",
            current_task="Different task",
            observations={},
            decisions_made=[],
            constraints={},
            confidence=0.5
        )
        
        result_small = DynamicConsensusProtocol.compare_states(scout_ssv, small_ssv)
        result_large = DynamicConsensusProtocol.compare_states(scout_ssv, large_ssv)
        
        assert result_large.divergence_score > result_small.divergence_score


class TestMismatchDetection:
    """Test mismatch field detection"""
    
    def test_mismatch_fields_detected(self, scout_ssv):
        """Test mismatched fields are correctly identified"""
        divergent_ssv = SSVGenerator.generate_ssv(
            agent_id="divergent",
            current_task="Different task",
            observations={},
            decisions_made=[],
            constraints={},
            confidence=0.5
        )
        
        result = DynamicConsensusProtocol.compare_states(scout_ssv, divergent_ssv)
        
        assert len(result.mismatch_fields) > 0
        assert "intent_vector" in result.mismatch_fields or "belief_state" in result.mismatch_fields
    
    def test_no_mismatch_for_identical(self, scout_ssv):
        """Test no mismatches for identical states"""
        identical_ssv = SSVGenerator.generate_ssv(
            agent_id="identical",
            current_task=scout_ssv.intent_vector.get("task", "test"),
            observations=scout_ssv.belief_state,
            decisions_made=scout_ssv.decision_history,
            constraints=scout_ssv.constraint_set,
            confidence=scout_ssv.confidence_score
        )
        
        result = DynamicConsensusProtocol.compare_states(scout_ssv, identical_ssv)
        
        assert len(result.mismatch_fields) == 0


class TestSyncPayload:
    """Test sync payload generation"""
    
    def test_sync_payload_generated_for_divergence(self, scout_ssv):
        """Test sync payload is generated for divergent states"""
        divergent_ssv = SSVGenerator.generate_ssv(
            agent_id="divergent",
            current_task="Different task",
            observations={},
            decisions_made=[],
            constraints={},
            confidence=0.5
        )
        
        result = DynamicConsensusProtocol.compare_states(scout_ssv, divergent_ssv)
        
        if result.level != ConsensusLevel.GREEN:
            assert result.sync_payload is not None
            assert "timestamp" in result.sync_payload
            assert "merge_strategy" in result.sync_payload
            assert "recommended_merge" in result.sync_payload
    
    def test_sync_payload_not_generated_for_green(self, scout_ssv):
        """Test sync payload is not generated for GREEN consensus"""
        identical_ssv = SSVGenerator.generate_ssv(
            agent_id="identical",
            current_task=scout_ssv.intent_vector.get("task", "test"),
            observations=scout_ssv.belief_state,
            decisions_made=scout_ssv.decision_history,
            constraints=scout_ssv.constraint_set,
            confidence=scout_ssv.confidence_score
        )
        
        result = DynamicConsensusProtocol.compare_states(scout_ssv, identical_ssv)
        
        assert result.sync_payload is None
