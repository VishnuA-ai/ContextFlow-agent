"""
Tests for LangGraph Integration
Tests agent wrapping, SSV auto-generation, consensus auto-checking, and multi-agent workflows
"""

import pytest
import asyncio
from contextflow.contextflow_langgraph import (
    ContextFlowAgent,
    AgentConfig,
    AgentWorkflow,
    contextflow_agent,
    AgentState
)
from ssv_core import ConsensusLevel


class TestContextFlowAgent:
    """Test ContextFlowAgent wrapper functionality"""
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """Test agent initialization with config"""
        config = AgentConfig(
            agent_id="test_agent",
            current_task="Test task",
            constraints={"max_items": 10}
        )
        
        agent = ContextFlowAgent(config=config)
        
        assert agent.config.agent_id == "test_agent"
        assert agent.config.current_task == "Test task"
        assert agent.config.constraints == {"max_items": 10}
        assert agent.state.observations == {}
        assert agent.state.decisions_made == []
    
    @pytest.mark.asyncio
    async def test_agent_run_without_function(self):
        """Test agent run fails without agent_function"""
        config = AgentConfig(agent_id="test", current_task="test")
        agent = ContextFlowAgent(config=config)
        
        with pytest.raises(ValueError, match="agent_function must be set"):
            await agent.run({})
    
    @pytest.mark.asyncio
    async def test_agent_run_with_function(self):
        """Test agent runs successfully with agent_function"""
        async def test_function(state):
            return {"result": "success"}
        
        config = AgentConfig(
            agent_id="test_agent",
            current_task="Test task",
            enable_consensus_check=False
        )
        agent = ContextFlowAgent(config=config, agent_function=test_function)
        
        result = await agent.run({})
        
        assert result == {"result": "success"}
        assert agent.state.current_ssv is not None
        assert agent.state.current_ssv.agent_id == "test_agent"
    
    @pytest.mark.asyncio
    async def test_ssv_auto_generation(self):
        """Test SSV is automatically generated after agent run"""
        async def test_function(state):
            return {"output": "test"}
        
        config = AgentConfig(
            agent_id="test_agent",
            current_task="Test task",
            enable_consensus_check=False
        )
        agent = ContextFlowAgent(config=config, agent_function=test_function)
        
        await agent.run({})
        
        assert agent.state.current_ssv is not None
        assert agent.state.current_ssv.state_hash is not None
        assert len(agent.state.current_ssv.state_hash) == 64
    
    @pytest.mark.asyncio
    async def test_peer_agent_registration(self):
        """Test peer agent registration"""
        config1 = AgentConfig(agent_id="agent1", current_task="task1")
        config2 = AgentConfig(agent_id="agent2", current_task="task2")
        
        agent1 = ContextFlowAgent(config=config1)
        agent2 = ContextFlowAgent(config=config2)
        
        agent1.register_peer_agent(agent2)
        
        assert "agent2" in agent1._peer_agents
        assert agent1._peer_agents["agent2"] == agent2
    
    @pytest.mark.asyncio
    async def test_consensus_auto_check(self):
        """Test consensus is automatically checked between agents"""
        async def func1(state):
            return {"data": "value1"}
        
        async def func2(state):
            return {"data": "value2"}
        
        config1 = AgentConfig(
            agent_id="agent1",
            current_task="task1",
            enable_consensus_check=True,
            auto_sync_on_divergence=False
        )
        config2 = AgentConfig(
            agent_id="agent2",
            current_task="task2",
            enable_consensus_check=True,
            auto_sync_on_divergence=False
        )
        
        agent1 = ContextFlowAgent(config=config1, agent_function=func1)
        agent2 = ContextFlowAgent(config=config2, agent_function=func2)
        
        agent1.register_peer_agent(agent2)
        
        await agent1.run({})
        await agent2.run({})
        
        assert agent1.state.last_consensus_result is not None
    
    @pytest.mark.asyncio
    async def test_auto_sync_on_divergence(self):
        """Test auto-sync on divergence"""
        async def func1(state):
            return {"data": "value1"}
        
        async def func2(state):
            return {"data": "value2"}
        
        config1 = AgentConfig(
            agent_id="agent1",
            current_task="task1",
            enable_consensus_check=True,
            auto_sync_on_divergence=True
        )
        config2 = AgentConfig(
            agent_id="agent2",
            current_task="task2",
            enable_consensus_check=True,
            auto_sync_on_divergence=True
        )
        
        agent1 = ContextFlowAgent(config=config1, agent_function=func1)
        agent2 = ContextFlowAgent(config=config2, agent_function=func2)
        
        agent1.register_peer_agent(agent2)
        
        await agent1.run({})
        await agent2.run({})
        
        # Should not raise error even with divergence due to auto_sync
        assert agent1.state.last_consensus_result is not None


class TestDecorator:
    """Test @contextflow_agent decorator"""
    
    @pytest.mark.asyncio
    async def test_decorator_wraps_function(self):
        """Test decorator wraps function correctly"""
        @contextflow_agent(
            agent_id="decorated_agent",
            current_task="Decorated task"
        )
        async def decorated_func(state):
            return {"result": "decorated"}
        
        assert hasattr(decorated_func, "_contextflow_config")
        assert decorated_func._contextflow_config.agent_id == "decorated_agent"
        
        result = await decorated_func({})
        assert result == {"result": "decorated"}
    
    @pytest.mark.asyncio
    async def test_decorator_generates_ssv(self):
        """Test decorated function generates SSV"""
        @contextflow_agent(
            agent_id="decorated_agent",
            current_task="Decorated task"
        )
        async def decorated_func(state):
            return {"result": "test"}
        
        await decorated_func({})
        
        # SSV should be generated internally


class TestAgentWorkflow:
    """Test AgentWorkflow orchestration"""
    
    @pytest.mark.asyncio
    async def test_workflow_initialization(self):
        """Test workflow initialization"""
        workflow = AgentWorkflow()
        
        assert workflow.agents == {}
        assert workflow.journal is not None
    
    @pytest.mark.asyncio
    async def test_add_agent_to_workflow(self):
        """Test adding agent to workflow"""
        workflow = AgentWorkflow()
        
        async def test_func(state):
            return {}
        
        config = AgentConfig(agent_id="test", current_task="test")
        agent = ContextFlowAgent(config=config, agent_function=test_func)
        
        workflow.add_agent(agent)
        
        assert "test" in workflow.agents
        assert workflow.agents["test"] == agent
    
    @pytest.mark.asyncio
    async def test_peer_registration_in_workflow(self):
        """Test agents are registered as peers in workflow"""
        workflow = AgentWorkflow()
        
        async def func1(state):
            return {}
        
        async def func2(state):
            return {}
        
        config1 = AgentConfig(agent_id="agent1", current_task="task1")
        config2 = AgentConfig(agent_id="agent2", current_task="task2")
        
        agent1 = ContextFlowAgent(config=config1, agent_function=func1)
        agent2 = ContextFlowAgent(config=config2, agent_function=func2)
        
        workflow.add_agent(agent1)
        workflow.add_agent(agent2)
        
        assert "agent2" in agent1._peer_agents
        assert "agent1" in agent2._peer_agents
    
    @pytest.mark.asyncio
    async def test_sequential_execution(self):
        """Test sequential workflow execution"""
        workflow = AgentWorkflow()
        
        execution_order = []
        
        async def func1(state):
            execution_order.append("agent1")
            return {"step1": "done"}
        
        async def func2(state):
            execution_order.append("agent2")
            return {"step2": "done"}
        
        config1 = AgentConfig(agent_id="agent1", current_task="task1", enable_consensus_check=False)
        config2 = AgentConfig(agent_id="agent2", current_task="task2", enable_consensus_check=False)
        
        agent1 = ContextFlowAgent(config=config1, agent_function=func1)
        agent2 = ContextFlowAgent(config=config2, agent_function=func2)
        
        workflow.add_agent(agent1)
        workflow.add_agent(agent2)
        
        result = await workflow.run_sequential({}, ["agent1", "agent2"])
        
        assert execution_order == ["agent1", "agent2"]
        assert result["step1"] == "done"
        assert result["step2"] == "done"
    
    @pytest.mark.asyncio
    async def test_parallel_execution(self):
        """Test parallel workflow execution"""
        workflow = AgentWorkflow()
        
        execution_order = []
        
        async def func1(state):
            execution_order.append("agent1")
            await asyncio.sleep(0.1)
            return {"result1": "done"}
        
        async def func2(state):
            execution_order.append("agent2")
            await asyncio.sleep(0.1)
            return {"result2": "done"}
        
        config1 = AgentConfig(agent_id="agent1", current_task="task1", enable_consensus_check=False)
        config2 = AgentConfig(agent_id="agent2", current_task="task2", enable_consensus_check=False)
        
        agent1 = ContextFlowAgent(config=config1, agent_function=func1)
        agent2 = ContextFlowAgent(config=config2, agent_function=func2)
        
        workflow.add_agent(agent1)
        workflow.add_agent(agent2)
        
        result = await workflow.run_parallel({}, ["agent1", "agent2"])
        
        assert "result1" in result
        assert "result2" in result
        assert len(execution_order) == 2
    
    @pytest.mark.asyncio
    async def test_workflow_metrics(self):
        """Test workflow metrics"""
        workflow = AgentWorkflow()
        
        async def test_func(state):
            return {}
        
        config = AgentConfig(agent_id="test", current_task="test")
        agent = ContextFlowAgent(config=config, agent_function=test_func)
        
        workflow.add_agent(agent)
        
        metrics = workflow.get_workflow_metrics()
        
        assert metrics["total_agents"] == 1
        assert "test" in metrics["agents"]
    
    @pytest.mark.asyncio
    async def test_sequential_execution_invalid_agent(self):
        """Test sequential execution with invalid agent ID"""
        workflow = AgentWorkflow()
        
        with pytest.raises(KeyError, match="Agent.*not found"):
            await workflow.run_sequential({}, ["nonexistent_agent"])


class TestErrorHandling:
    """Test error handling in LangGraph integration"""
    
    @pytest.mark.asyncio
    async def test_agent_function_error_handling(self):
        """Test agent function errors are handled"""
        async def failing_func(state):
            raise ValueError("Test error")
        
        config = AgentConfig(agent_id="test", current_task="test")
        agent = ContextFlowAgent(config=config, agent_function=failing_func)
        
        with pytest.raises(ValueError, match="Test error"):
            await agent.run({})
    
    @pytest.mark.asyncio
    async def test_empty_response_handling(self):
        """Test handling of empty agent responses"""
        async def empty_func(state):
            return {}
        
        config = AgentConfig(agent_id="test", current_task="test", enable_consensus_check=False)
        agent = ContextFlowAgent(config=config, agent_function=empty_func)
        
        result = await agent.run({})
        
        assert result == {}
        assert agent.state.current_ssv is not None
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test handling of slow agent functions"""
        async def slow_func(state):
            await asyncio.sleep(0.1)
            return {"result": "done"}
        
        config = AgentConfig(agent_id="test", current_task="test", enable_consensus_check=False)
        agent = ContextFlowAgent(config=config, agent_function=slow_func)
        
        result = await agent.run({})
        
        assert result == {"result": "done"}
