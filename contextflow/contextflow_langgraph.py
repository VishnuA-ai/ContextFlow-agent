"""
ContextFlow LangGraph Integration
Provides ContextFlowAgent wrapper for LangGraph agents with automatic SSV generation
and consensus checking to prevent multi-agent hallucination.
"""

import logging
from typing import Dict, Any, List, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import json

from ssv_core import (
    SemanticStateVector,
    DynamicConsensusProtocol,
    ConsensusLevel,
    AsyncStateJournal,
    SSVGenerator,
    ConsensusResult
)

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Configuration for ContextFlowAgent"""
    agent_id: str
    current_task: str
    constraints: Dict[str, Any] = field(default_factory=dict)
    confidence_threshold: float = 0.8
    enable_consensus_check: bool = True
    consensus_agent_ids: List[str] = field(default_factory=list)
    auto_sync_on_divergence: bool = True


@dataclass
class AgentState:
    """Internal state for ContextFlowAgent"""
    observations: Dict[str, Any] = field(default_factory=dict)
    decisions_made: List[str] = field(default_factory=list)
    current_ssv: Optional[SemanticStateVector] = None
    last_consensus_result: Optional[ConsensusResult] = None
    last_consensus_agent: Optional[str] = None


class ContextFlowAgent:
    """
    Wrapper class for LangGraph agents that provides automatic SSV generation
    and consensus checking to prevent multi-agent hallucination.
    
    This wrapper is transparent to existing agent code - it intercepts agent
    outputs, generates SSVs, and checks consensus with other agents automatically.
    
    Example:
        # Wrap your existing agent function
        @contextflow_agent
        def my_agent(state: Dict[str, Any]) -> Dict[str, Any]:
            # Your agent logic here
            return {"result": "some output"}
        
        # Or use as a wrapper
        agent = ContextFlowAgent(
            agent_id="scout",
            current_task="Find research papers",
            agent_function=my_agent_function
        )
        result = await agent.run(state)
    """
    
    def __init__(
        self,
        config: AgentConfig,
        agent_function: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
        journal: Optional[AsyncStateJournal] = None
    ):
        """
        Initialize ContextFlowAgent.
        
        Args:
            config: AgentConfig with agent settings
            agent_function: Optional callable that takes state and returns updated state
            journal: Optional AsyncStateJournal for logging state changes
        """
        self.config = config
        self.agent_function = agent_function
        self.state = AgentState()
        self.journal = journal or AsyncStateJournal()
        self._peer_agents: Dict[str, "ContextFlowAgent"] = {}
        
        logger.info(
            f"Initialized ContextFlowAgent: {config.agent_id} "
            f"with task: {config.current_task}"
        )
    
    def register_peer_agent(self, agent: "ContextFlowAgent") -> None:
        """
        Register another ContextFlowAgent for consensus checking.
        
        Args:
            agent: Another ContextFlowAgent instance
        """
        self._peer_agents[agent.config.agent_id] = agent
        logger.debug(
            f"Registered peer agent {agent.config.agent_id} "
            f"for {self.config.agent_id}"
        )
    
    async def run(
        self,
        input_state: Dict[str, Any],
        check_consensus: bool = True
    ) -> Dict[str, Any]:
        """
        Execute the agent with automatic SSV generation and consensus checking.
        
        Args:
            input_state: Input state for the agent
            check_consensus: Whether to check consensus with peer agents
            
        Returns:
            Updated state from the agent
            
        Raises:
            ValueError: If agent_function is not set
            RuntimeError: If consensus check fails and auto_sync is disabled
        """
        if self.agent_function is None:
            raise ValueError("agent_function must be set to run the agent")
        
        logger.debug(f"Running agent {self.config.agent_id} with input state")
        
        # Update observations from input
        self.state.observations.update(input_state)
        
        # Execute the agent function
        try:
            result = await self._execute_agent_function(input_state)
        except Exception as e:
            logger.error(f"Agent {self.config.agent_id} execution failed: {e}")
            raise
        
        # Update state with result
        self.state.observations.update(result)
        self.state.decisions_made.append(f"executed_{self.config.agent_id}")
        
        # Generate SSV
        await self._generate_ssv()
        
        # Check consensus if enabled
        if check_consensus and self.config.enable_consensus_check:
            await self._check_consensus()
        
        logger.info(
            f"Agent {self.config.agent_id} completed successfully. "
            f"SSV hash: {self.state.current_ssv.state_hash[:12] if self.state.current_ssv else 'N/A'}..."
        )
        
        return result
    
    async def _execute_agent_function(
        self,
        input_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute the underlying agent function.
        
        Args:
            input_state: Input state for the agent
            
        Returns:
            Result from agent function
        """
        if asyncio.iscoroutinefunction(self.agent_function):
            return await self.agent_function(input_state)
        else:
            return self.agent_function(input_state)
    
    async def _generate_ssv(self) -> None:
        """
        Generate Semantic State Vector from current agent state.
        """
        try:
            old_hash = self.state.current_ssv.state_hash if self.state.current_ssv else "initial"
            
            ssv = SSVGenerator.generate_ssv(
                agent_id=self.config.agent_id,
                current_task=self.config.current_task,
                observations=self.state.observations,
                decisions_made=self.state.decisions_made,
                constraints=self.config.constraints,
                confidence=self.config.confidence_threshold
            )
            
            self.state.current_ssv = ssv
            
            # Log to journal
            self.journal.log_state_change(
                agent_id=self.config.agent_id,
                action="ssv_generated",
                state_delta={"task": self.config.current_task},
                previous_hash=old_hash,
                new_hash=ssv.state_hash
            )
            
            logger.debug(
                f"Generated SSV for {self.config.agent_id}: "
                f"hash={ssv.state_hash[:12]}..., confidence={ssv.confidence_score:.2f}"
            )
            
        except Exception as e:
            logger.error(f"Failed to generate SSV for {self.config.agent_id}: {e}")
            raise
    
    async def _check_consensus(self) -> None:
        """
        Check consensus with registered peer agents.
        
        Raises:
            RuntimeError: If consensus check fails and auto_sync is disabled
        """
        if not self._peer_agents:
            logger.debug(f"No peer agents registered for {self.config.agent_id}")
            return
        
        for peer_id, peer_agent in self._peer_agents.items():
            if not peer_agent.state.current_ssv:
                logger.debug(f"Peer {peer_id} has no SSV yet, skipping consensus check")
                continue
            
            try:
                consensus = DynamicConsensusProtocol.compare_states(
                    self.state.current_ssv,
                    peer_agent.state.current_ssv
                )
                
                self.state.last_consensus_result = consensus
                self.state.last_consensus_agent = peer_id
                
                # Log consensus check
                self.journal.log_state_change(
                    agent_id=f"{self.config.agent_id}+{peer_id}",
                    action="consensus_check",
                    state_delta={
                        "level": consensus.level.value,
                        "divergence_score": consensus.divergence_score
                    },
                    previous_hash=self.state.current_ssv.state_hash,
                    new_hash=peer_agent.state.current_ssv.state_hash
                )
                
                if consensus.level == ConsensusLevel.GREEN:
                    logger.info(
                        f"Consensus GREEN between {self.config.agent_id} and {peer_id}: "
                        f"divergence={consensus.divergence_score:.4f}"
                    )
                elif consensus.level == ConsensusLevel.YELLOW:
                    logger.warning(
                        f"Consensus YELLOW between {self.config.agent_id} and {peer_id}: "
                        f"divergence={consensus.divergence_score:.4f}, "
                        f"mismatches={consensus.mismatch_fields}"
                    )
                else:  # RED
                    logger.error(
                        f"Consensus RED between {self.config.agent_id} and {peer_id}: "
                        f"divergence={consensus.divergence_score:.4f}, "
                        f"action={consensus.recommended_action}"
                    )
                    
                    if self.config.auto_sync_on_divergence:
                        await self._sync_with_peer(peer_agent, consensus)
                    else:
                        raise RuntimeError(
                            f"Critical divergence detected between {self.config.agent_id} "
                            f"and {peer_id}. Auto-sync disabled."
                        )
                        
            except Exception as e:
                logger.error(f"Consensus check failed for {self.config.agent_id} with {peer_id}: {e}")
                raise
    
    async def _sync_with_peer(
        self,
        peer_agent: "ContextFlowAgent",
        consensus: ConsensusResult
    ) -> None:
        """
        Synchronize state with peer agent using consensus sync payload.
        
        Args:
            peer_agent: Peer agent to sync with
            consensus: Consensus result containing sync payload
        """
        if not consensus.sync_payload:
            logger.warning(f"No sync payload available for {self.config.agent_id}")
            return
        
        try:
            # Apply recommended merge
            recommended_merge = consensus.sync_payload.get("recommended_merge", {})
            
            # Update beliefs
            if "beliefs" in recommended_merge:
                self.state.observations.update(recommended_merge["beliefs"])
            
            # Update constraints
            if "constraints" in recommended_merge:
                self.config.constraints.update(recommended_merge["constraints"])
            
            # Regenerate SSV after sync
            old_hash = self.state.current_ssv.state_hash if self.state.current_ssv else "unknown"
            await self._generate_ssv()
            
            # Log sync
            self.journal.log_state_change(
                agent_id=self.config.agent_id,
                action="state_sync",
                state_delta={"synced_with": peer_agent.config.agent_id},
                previous_hash=old_hash,
                new_hash=self.state.current_ssv.state_hash if self.state.current_ssv else "unknown"
            )
            
            logger.info(
                f"Successfully synced {self.config.agent_id} with {peer_agent.config.agent_id}"
            )
            
        except Exception as e:
            logger.error(f"Failed to sync {self.config.agent_id} with peer: {e}")
            raise
    
    def get_ssv(self) -> Optional[SemanticStateVector]:
        """
        Get the current Semantic State Vector.
        
        Returns:
            Current SSV or None if not generated
        """
        return self.state.current_ssv
    
    def get_consensus_result(self) -> Optional[ConsensusResult]:
        """
        Get the last consensus check result.
        
        Returns:
            Last ConsensusResult or None if no check performed
        """
        return self.state.last_consensus_result
    
    def get_agent_history(self) -> List[Any]:
        """
        Get the agent's state change history from the journal.
        
        Returns:
            List of journal entries for this agent
        """
        return self.journal.get_agent_history(self.config.agent_id)


def contextflow_agent(
    agent_id: str,
    current_task: str,
    constraints: Optional[Dict[str, Any]] = None,
    confidence_threshold: float = 0.8,
    enable_consensus_check: bool = True,
    auto_sync_on_divergence: bool = True
) -> Callable:
    """
    Decorator to wrap an agent function with ContextFlow capabilities.
    
    Args:
        agent_id: Unique identifier for the agent
        current_task: Description of what the agent is doing
        constraints: Optional constraints for the agent
        confidence_threshold: Minimum confidence threshold (default: 0.8)
        enable_consensus_check: Whether to enable consensus checking (default: True)
        auto_sync_on_divergence: Whether to auto-sync on divergence (default: True)
        
    Returns:
        Decorator function
        
    Example:
        @contextflow_agent(
            agent_id="scout",
            current_task="Find research papers",
            constraints={"max_papers": 10}
        )
        async def scout_agent(state: Dict[str, Any]) -> Dict[str, Any]:
            # Agent logic here
            return {"papers_found": 5}
    """
    def decorator(func: Callable) -> Callable:
        config = AgentConfig(
            agent_id=agent_id,
            current_task=current_task,
            constraints=constraints or {},
            confidence_threshold=confidence_threshold,
            enable_consensus_check=enable_consensus_check,
            auto_sync_on_divergence=auto_sync_on_divergence
        )
        
        # Store config on the function for later retrieval
        func._contextflow_config = config
        
        async def wrapper(state: Dict[str, Any]) -> Dict[str, Any]:
            agent = ContextFlowAgent(config=config, agent_function=func)
            return await agent.run(state)
        
        # Preserve original function metadata
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        wrapper._contextflow_config = config
        
        return wrapper
    
    return decorator


class AgentWorkflow:
    """
    Orchestrates multiple ContextFlowAgents in a workflow.
    Manages agent registration and sequential execution with consensus checking.
    """
    
    def __init__(self, journal: Optional[AsyncStateJournal] = None):
        """
        Initialize AgentWorkflow.
        
        Args:
            journal: Optional shared AsyncStateJournal for all agents
        """
        self.agents: Dict[str, ContextFlowAgent] = {}
        self.journal = journal or AsyncStateJournal()
        logger.info("Initialized AgentWorkflow")
    
    def add_agent(self, agent: ContextFlowAgent) -> None:
        """
        Add an agent to the workflow.
        
        Args:
            agent: ContextFlowAgent instance
        """
        self.agents[agent.config.agent_id] = agent
        agent.journal = self.journal
        
        # Register all other agents as peers
        for other_agent_id, other_agent in self.agents.items():
            if other_agent_id != agent.config.agent_id:
                agent.register_peer_agent(other_agent)
                other_agent.register_peer_agent(agent)
        
        logger.info(f"Added agent {agent.config.agent_id} to workflow")
    
    async def run_sequential(
        self,
        initial_state: Dict[str, Any],
        agent_order: List[str]
    ) -> Dict[str, Any]:
        """
        Run agents sequentially in the specified order.
        
        Args:
            initial_state: Initial state for the workflow
            agent_order: List of agent IDs in execution order
            
        Returns:
            Final state after all agents have run
            
        Raises:
            KeyError: If agent_id not found in workflow
        """
        state = initial_state.copy()
        
        for agent_id in agent_order:
            if agent_id not in self.agents:
                raise KeyError(f"Agent {agent_id} not found in workflow")
            
            logger.info(f"Executing agent {agent_id} in sequential workflow")
            agent = self.agents[agent_id]
            result = await agent.run(state)
            state.update(result)
        
        logger.info(f"Sequential workflow completed with {len(agent_order)} agents")
        return state
    
    async def run_parallel(
        self,
        initial_state: Dict[str, Any],
        agent_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Run agents in parallel.
        
        Args:
            initial_state: Initial state for the workflow
            agent_ids: List of agent IDs to run in parallel
            
        Returns:
            Combined state from all agents
            
        Raises:
            KeyError: If agent_id not found in workflow
        """
        tasks = []
        
        for agent_id in agent_ids:
            if agent_id not in self.agents:
                raise KeyError(f"Agent {agent_id} not found in workflow")
            
            agent = self.agents[agent_id]
            tasks.append(agent.run(initial_state.copy(), check_consensus=False))
        
        logger.info(f"Running {len(agent_ids)} agents in parallel")
        results = await asyncio.gather(*tasks)
        
        # Merge results
        merged_state = initial_state.copy()
        for result in results:
            merged_state.update(result)
        
        # Check consensus after parallel execution
        for agent_id in agent_ids:
            agent = self.agents[agent_id]
            await agent._check_consensus()
        
        logger.info(f"Parallel workflow completed with {len(agent_ids)} agents")
        return merged_state
    
    def get_workflow_metrics(self) -> Dict[str, Any]:
        """
        Get metrics for the entire workflow.
        
        Returns:
            Dictionary with workflow metrics
        """
        return {
            "total_agents": len(self.agents),
            "journal_entries": len(self.journal.entries),
            "agents": list(self.agents.keys())
        }
