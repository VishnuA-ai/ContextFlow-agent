"""
Performance tests for ContextFlow
Tests SSV generation <50ms, consensus check <10ms, API responses <100ms
"""

import pytest
import time
import asyncio
from ssv_core import SSVGenerator, DynamicConsensusProtocol
from contextflow.contextflow_langgraph import ContextFlowAgent, AgentConfig
from fastapi.testclient import TestClient
from contextflow_api import app


class TestSSVPerformance:
    """Test SSV generation performance"""
    
    def test_ssv_generation_under_50ms(self):
        """Test SSV generation completes in under 50ms"""
        start = time.time()
        
        ssv = SSVGenerator.generate_ssv(
            agent_id="perf_test",
            current_task="Performance test task",
            observations={"data": "value" * 100},
            decisions_made=["decision"] * 10,
            constraints={"constraint": "value"},
            confidence=0.8
        )
        
        elapsed = (time.time() - start) * 1000  # Convert to ms
        
        assert elapsed < 50, f"SSV generation took {elapsed:.2f}ms, expected <50ms"
        assert ssv.state_hash is not None
    
    def test_ssv_generation_with_large_observations(self):
        """Test SSV generation with large observation set"""
        large_observations = {f"key_{i}": f"value_{i}" * 10 for i in range(100)}
        
        start = time.time()
        
        ssv = SSVGenerator.generate_ssv(
            agent_id="perf_test",
            current_task="Performance test",
            observations=large_observations,
            decisions_made=[],
            constraints={},
            confidence=0.8
        )
        
        elapsed = (time.time() - start) * 1000
        
        assert elapsed < 50, f"Large SSV generation took {elapsed:.2f}ms, expected <50ms"
    
    def test_ssv_serialization_performance(self):
        """Test SSV serialization performance"""
        ssv = SSVGenerator.generate_ssv(
            agent_id="perf_test",
            current_task="Test",
            observations={"data": "value"},
            decisions_made=[],
            constraints={},
            confidence=0.8
        )
        
        start = time.time()
        compact = ssv.to_compact()
        elapsed = (time.time() - start) * 1000
        
        assert elapsed < 10, f"SSV serialization took {elapsed:.2f}ms, expected <10ms"
        assert len(compact) > 0


class TestConsensusPerformance:
    """Test consensus check performance"""
    
    def test_consensus_check_under_10ms(self):
        """Test consensus check completes in under 10ms"""
        ssv1 = SSVGenerator.generate_ssv(
            agent_id="agent1",
            current_task="Task",
            observations={"data": "value"},
            decisions_made=[],
            constraints={},
            confidence=0.8
        )
        
        ssv2 = SSVGenerator.generate_ssv(
            agent_id="agent2",
            current_task="Task",
            observations={"data": "value"},
            decisions_made=[],
            constraints={},
            confidence=0.8
        )
        
        start = time.time()
        result = DynamicConsensusProtocol.compare_states(ssv1, ssv2)
        elapsed = (time.time() - start) * 1000
        
        assert elapsed < 10, f"Consensus check took {elapsed:.2f}ms, expected <10ms"
        assert result is not None
    
    def test_consensus_check_with_divergence(self):
        """Test consensus check performance with divergent states"""
        ssv1 = SSVGenerator.generate_ssv(
            agent_id="agent1",
            current_task="Task1",
            observations={"data": "value1"},
            decisions_made=[],
            constraints={},
            confidence=0.8
        )
        
        ssv2 = SSVGenerator.generate_ssv(
            agent_id="agent2",
            current_task="Task2",
            observations={"data": "value2"},
            decisions_made=[],
            constraints={},
            confidence=0.8
        )
        
        start = time.time()
        result = DynamicConsensusProtocol.compare_states(ssv1, ssv2)
        elapsed = (time.time() - start) * 1000
        
        assert elapsed < 10, f"Divergent consensus check took {elapsed:.2f}ms, expected <10ms"
    
    def test_consensus_check_large_states(self):
        """Test consensus check with large state vectors"""
        large_observations = {f"key_{i}": f"value_{i}" for i in range(50)}
        
        ssv1 = SSVGenerator.generate_ssv(
            agent_id="agent1",
            current_task="Task",
            observations=large_observations,
            decisions_made=[f"decision_{i}" for i in range(10)],
            constraints={f"constraint_{i}": i for i in range(10)},
            confidence=0.8
        )
        
        ssv2 = SSVGenerator.generate_ssv(
            agent_id="agent2",
            current_task="Task",
            observations=large_observations,
            decisions_made=[f"decision_{i}" for i in range(10)],
            constraints={f"constraint_{i}": i for i in range(10)},
            confidence=0.8
        )
        
        start = time.time()
        result = DynamicConsensusProtocol.compare_states(ssv1, ssv2)
        elapsed = (time.time() - start) * 1000
        
        assert elapsed < 10, f"Large state consensus check took {elapsed:.2f}ms, expected <10ms"


class TestAPIPerformance:
    """Test API response performance"""
    
    def test_health_check_under_100ms(self):
        """Test health check responds in under 100ms"""
        client = TestClient(app)
        
        start = time.time()
        response = client.get("/health")
        elapsed = (time.time() - start) * 1000
        
        assert response.status_code == 200
        assert elapsed < 100, f"Health check took {elapsed:.2f}ms, expected <100ms"
    
    def test_ssv_generation_api_under_100ms(self):
        """Test SSV generation API responds in under 100ms"""
        client = TestClient(app)
        
        request_data = {
            "agent_id": "perf_test",
            "current_task": "Performance test",
            "observations": {"data": "value"},
            "decisions_made": [],
            "constraints": {},
            "confidence": 0.8
        }
        
        start = time.time()
        response = client.post("/ssv/generate", json=request_data)
        elapsed = (time.time() - start) * 1000
        
        assert response.status_code == 200
        assert elapsed < 100, f"SSV generation API took {elapsed:.2f}ms, expected <100ms"
    
    def test_consensus_check_api_under_100ms(self):
        """Test consensus check API responds in under 100ms"""
        client = TestClient(app)
        
        # First generate SSVs
        client.post("/ssv/generate", json={
            "agent_id": "agent_a",
            "current_task": "Task",
            "observations": {"data": "value"},
            "decisions_made": [],
            "constraints": {},
            "confidence": 0.8
        })
        
        client.post("/ssv/generate", json={
            "agent_id": "agent_b",
            "current_task": "Task",
            "observations": {"data": "value"},
            "decisions_made": [],
            "constraints": {},
            "confidence": 0.8
        })
        
        start = time.time()
        response = client.post("/consensus/check", json={
            "agent_a_id": "agent_a",
            "agent_b_id": "agent_b"
        })
        elapsed = (time.time() - start) * 1000
        
        assert response.status_code == 200
        assert elapsed < 100, f"Consensus check API took {elapsed:.2f}ms, expected <100ms"
    
    def test_metrics_api_under_100ms(self):
        """Test metrics API responds in under 100ms"""
        client = TestClient(app)
        
        start = time.time()
        response = client.get("/metrics")
        elapsed = (time.time() - start) * 1000
        
        assert response.status_code == 200
        assert elapsed < 100, f"Metrics API took {elapsed:.2f}ms, expected <100ms"


class TestLangGraphPerformance:
    """Test LangGraph integration performance"""
    
    @pytest.mark.asyncio
    async def test_agent_run_under_100ms(self):
        """Test agent run completes in under 100ms"""
        async def test_func(state):
            return {"result": "success"}
        
        config = AgentConfig(
            agent_id="perf_test",
            current_task="Performance test",
            enable_consensus_check=False
        )
        agent = ContextFlowAgent(config=config, agent_function=test_func)
        
        start = time.time()
        result = await agent.run({})
        elapsed = (time.time() - start) * 1000
        
        assert result == {"result": "success"}
        assert elapsed < 100, f"Agent run took {elapsed:.2f}ms, expected <100ms"
    
    @pytest.mark.asyncio
    async def test_workflow_sequential_performance(self):
        """Test sequential workflow performance"""
        from contextflow.contextflow_langgraph import AgentWorkflow
        
        workflow = AgentWorkflow()
        
        async def func1(state):
            return {"step1": "done"}
        
        async def func2(state):
            return {"step2": "done"}
        
        config1 = AgentConfig(agent_id="agent1", current_task="task1", enable_consensus_check=False)
        config2 = AgentConfig(agent_id="agent2", current_task="task2", enable_consensus_check=False)
        
        agent1 = ContextFlowAgent(config=config1, agent_function=func1)
        agent2 = ContextFlowAgent(config=config2, agent_function=func2)
        
        workflow.add_agent(agent1)
        workflow.add_agent(agent2)
        
        start = time.time()
        result = await workflow.run_sequential({}, ["agent1", "agent2"])
        elapsed = (time.time() - start) * 1000
        
        assert "step1" in result
        assert "step2" in result
        assert elapsed < 200, f"Sequential workflow took {elapsed:.2f}ms, expected <200ms"


class TestJournalPerformance:
    """Test journal performance"""
    
    def test_journal_logging_performance(self):
        """Test journal logging performance"""
        from ssv_core import AsyncStateJournal
        
        journal = AsyncStateJournal()
        
        start = time.time()
        for i in range(100):
            journal.log_state_change(
                agent_id="test",
                action="test_action",
                state_delta={"index": i},
                previous_hash=f"hash_{i}",
                new_hash=f"hash_{i+1}"
            )
        elapsed = (time.time() - start) * 1000
        
        assert elapsed < 100, f"100 journal entries took {elapsed:.2f}ms, expected <100ms"
        assert len(journal.entries) == 100
    
    def test_journal_query_performance(self):
        """Test journal query performance"""
        from ssv_core import AsyncStateJournal
        
        journal = AsyncStateJournal()
        
        # Add entries
        for i in range(100):
            journal.log_state_change(
                agent_id=f"agent_{i % 5}",
                action="test_action",
                state_delta={"index": i},
                previous_hash=f"hash_{i}",
                new_hash=f"hash_{i+1}"
            )
        
        start = time.time()
        history = journal.get_agent_history("agent_0")
        elapsed = (time.time() - start) * 1000
        
        assert elapsed < 10, f"Journal query took {elapsed:.2f}ms, expected <10ms"
        assert len(history) > 0
