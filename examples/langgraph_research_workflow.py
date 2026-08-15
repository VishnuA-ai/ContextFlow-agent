"""
ContextFlow LangGraph Research Workflow Example
Demonstrates multi-agent research workflow with automatic consensus checking
to prevent hallucination.

This example shows:
- Scout Agent: Searches for research papers
- Critic Agent: Evaluates methodology
- Synthesis Agent: Creates summary
- Automatic SSV generation and consensus checking between agents
"""

import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

from contextflow.contextflow_langgraph import (
    ContextFlowAgent,
    AgentConfig,
    AgentWorkflow,
    contextflow_agent
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# AGENT FUNCTIONS
# ============================================================================

async def scout_agent_function(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Scout Agent: Searches for research papers on a given topic.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with found papers
    """
    logger.info("[SCOUT] Searching for research papers...")
    
    # Simulate paper search
    papers_found = [
        {
            "title": "Context Drift in Multi-Agent Systems",
            "citations": 145,
            "year": 2026,
            "methodology": "empirical"
        },
        {
            "title": "Agent Coordination Protocols",
            "citations": 89,
            "year": 2025,
            "methodology": "theoretical"
        },
        {
            "title": "Hallucination Prevention in LLMs",
            "citations": 234,
            "year": 2026,
            "methodology": "experimental"
        }
    ]
    
    return {
        "papers_found": papers_found,
        "search_timestamp": datetime.now().isoformat(),
        "papers_count": len(papers_found)
    }


async def critic_agent_function(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Critic Agent: Evaluates methodology of found papers.
    
    Args:
        state: Current workflow state with papers
        
    Returns:
        Updated state with paper evaluations
    """
    logger.info("[CRITIC] Evaluating paper methodologies...")
    
    papers = state.get("papers_found", [])
    evaluations = []
    
    for paper in papers:
        # Simulate methodology evaluation
        rigor_score = 0.8 if paper["methodology"] == "experimental" else 0.6
        evaluations.append({
            "title": paper["title"],
            "rigor_score": rigor_score,
            "methodology": paper["methodology"],
            "passes_threshold": rigor_score >= 0.7
        })
    
    return {
        "paper_evaluations": evaluations,
        "papers_passed": sum(1 for e in evaluations if e["passes_threshold"]),
        "evaluation_timestamp": datetime.now().isoformat()
    }


async def synthesis_agent_function(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Synthesis Agent: Creates summary from evaluated papers.
    
    Args:
        state: Current workflow state with evaluations
        
    Returns:
        Updated state with synthesis summary
    """
    logger.info("[SYNTHESIS] Creating research summary...")
    
    evaluations = state.get("paper_evaluations", [])
    papers_passed = state.get("papers_passed", 0)
    
    # Create synthesis
    summary = {
        "total_papers_reviewed": len(evaluations),
        "papers_passing_rigor": papers_passed,
        "key_themes": [
            "Context drift is a critical issue in multi-agent systems",
            "Experimental methodologies show higher rigor scores",
            "Coordination protocols need consensus mechanisms"
        ],
        "confidence_score": papers_passed / max(len(evaluations), 1),
        "synthesis_timestamp": datetime.now().isoformat()
    }
    
    return summary


# ============================================================================
# WORKFLOW EXECUTION
# ============================================================================

async def run_research_workflow():
    """
    Run the complete research workflow with ContextFlow integration.
    """
    print("=" * 80)
    print("CONTEXTFLOW LANGGRAPH RESEARCH WORKFLOW")
    print("=" * 80)
    print()
    
    # Create workflow
    workflow = AgentWorkflow()
    
    # Create agents
    scout_config = AgentConfig(
        agent_id="scout",
        current_task="Search for research papers on multi-agent systems",
        constraints={"max_papers": 10, "date_range": "2025-2026"},
        confidence_threshold=0.9,
        enable_consensus_check=True,
        auto_sync_on_divergence=True
    )
    
    critic_config = AgentConfig(
        agent_id="critic",
        current_task="Evaluate paper methodology rigor",
        constraints={"rigor_threshold": 0.7, "methodology_weight": 0.8},
        confidence_threshold=0.85,
        enable_consensus_check=True,
        auto_sync_on_divergence=True
    )
    
    synthesis_config = AgentConfig(
        agent_id="synthesis",
        current_task="Synthesize findings into summary",
        constraints={"accuracy_threshold": 0.85},
        confidence_threshold=0.92,
        enable_consensus_check=True,
        auto_sync_on_divergence=True
    )
    
    scout_agent = ContextFlowAgent(
        config=scout_config,
        agent_function=scout_agent_function
    )
    
    critic_agent = ContextFlowAgent(
        config=critic_config,
        agent_function=critic_agent_function
    )
    
    synthesis_agent = ContextFlowAgent(
        config=synthesis_config,
        agent_function=synthesis_agent_function
    )
    
    # Add agents to workflow
    workflow.add_agent(scout_agent)
    workflow.add_agent(critic_agent)
    workflow.add_agent(synthesis_agent)
    
    print(f"✓ Initialized {len(workflow.agents)} agents")
    print(f"  - scout: {scout_config.current_task}")
    print(f"  - critic: {critic_config.current_task}")
    print(f"  - synthesis: {synthesis_config.current_task}")
    print()
    
    # Run workflow sequentially
    print("-" * 80)
    print("RUNNING SEQUENTIAL WORKFLOW")
    print("-" * 80)
    
    initial_state = {
        "query": "multi-agent hallucination prevention",
        "workflow_start": datetime.now().isoformat()
    }
    
    final_state = await workflow.run_sequential(
        initial_state=initial_state,
        agent_order=["scout", "critic", "synthesis"]
    )
    
    print()
    print("-" * 80)
    print("WORKFLOW RESULTS")
    print("-" * 80)
    
    # Print results
    print(f"\nPapers Found: {final_state.get('papers_count', 0)}")
    print(f"Papers Passing Rigor: {final_state.get('papers_passed', 0)}")
    print(f"Confidence Score: {final_state.get('confidence_score', 0):.2%}")
    
    print("\nKey Themes:")
    for theme in final_state.get("key_themes", []):
        print(f"  • {theme}")
    
    # Print SSV information
    print()
    print("-" * 80)
    print("SEMANTIC STATE VECTORS")
    print("-" * 80)
    
    for agent_id, agent in workflow.agents.items():
        ssv = agent.get_ssv()
        if ssv:
            print(f"\n{agent_id.upper()}:")
            print(f"  Hash: {ssv.state_hash[:16]}...")
            print(f"  Confidence: {ssv.confidence_score:.2%}")
            print(f"  Timestamp: {datetime.fromtimestamp(ssv.timestamp).isoformat()}")
            
            consensus = agent.get_consensus_result()
            if consensus:
                print(f"  Last Consensus: {consensus.level.value}")
                print(f"  Divergence Score: {consensus.divergence_score:.4f}")
    
    # Print workflow metrics
    print()
    print("-" * 80)
    print("WORKFLOW METRICS")
    print("-" * 80)
    
    metrics = workflow.get_workflow_metrics()
    print(f"\nTotal Agents: {metrics['total_agents']}")
    print(f"Journal Entries: {metrics['journal_entries']}")
    print(f"Agents: {', '.join(metrics['agents'])}")
    
    # Print agent histories
    print()
    print("-" * 80)
    print("AGENT HISTORIES")
    print("-" * 80)
    
    for agent_id in ["scout", "critic", "synthesis"]:
        history = workflow.journal.get_agent_history(agent_id)
        print(f"\n{agent_id.upper()} History ({len(history)} entries):")
        for entry in history:
            print(f"  [{entry.sequence_number}] {entry.action} - {entry.new_hash[:12]}...")
    
    print()
    print("=" * 80)
    print("WORKFLOW COMPLETED SUCCESSFULLY")
    print("=" * 80)


async def run_decorator_example():
    """
    Run workflow using the @contextflow_agent decorator.
    """
    print("\n" + "=" * 80)
    print("DECORATOR EXAMPLE")
    print("=" * 80)
    print()
    
    # Create decorated agents
    @contextflow_agent(
        agent_id="decorated_scout",
        current_task="Search with decorator",
        constraints={"max_papers": 5}
    )
    async def decorated_scout(state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("[DECORATED_SCOUT] Running with decorator")
        return {"papers": 3, "method": "decorator"}
    
    @contextflow_agent(
        agent_id="decorated_critic",
        current_task="Evaluate with decorator"
    )
    async def decorated_critic(state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("[DECORATED_CRITIC] Running with decorator")
        return {"evaluations": 3, "passed": 2}
    
    # Run agents
    state = {"query": "test"}
    
    result1 = await decorated_scout(state)
    print(f"✓ Scout result: {result1}")
    
    result2 = await decorated_critic(result1)
    print(f"✓ Critic result: {result2}")
    
    print("\nDecorator example completed successfully")


# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Main entry point."""
    await run_research_workflow()
    await run_decorator_example()


if __name__ == "__main__":
    asyncio.run(main())
