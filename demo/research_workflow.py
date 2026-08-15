"""
ContextFlow Research Workflow Demo
Demonstrates multi-agent research workflow with consensus checking
Shows: With ContextFlow vs Without ContextFlow comparison
"""

import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

from contextflow.contextflow_langgraph import (
    ContextFlowAgent,
    AgentConfig,
    AgentWorkflow
)
from ssv_core import SSVGenerator, DynamicConsensusProtocol, ConsensusLevel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# AGENT FUNCTIONS (WITHOUT CONTEXTFLOW)
# ============================================================================

async def scout_without_cf(state: Dict[str, Any]) -> Dict[str, Any]:
    """Scout agent without ContextFlow - no consensus checking"""
    logger.info("[SCOUT] Searching for papers (WITHOUT ContextFlow)...")
    
    papers = [
        {"title": "Paper A", "citations": 100},
        {"title": "Paper B", "citations": 150},
    ]
    
    # Simulate outdated data (hallucination risk)
    return {
        "papers": papers,
        "timestamp": datetime(2026, 8, 1).timestamp()
    }


async def critic_without_cf(state: Dict[str, Any]) -> Dict[str, Any]:
    """Critic agent without ContextFlow - no consensus checking"""
    logger.info("[CRITIC] Evaluating papers (WITHOUT ContextFlow)...")
    
    papers = state.get("papers", [])
    
    # Simulate using different data (outdated cache)
    evaluations = []
    for paper in papers:
        # Different citation count = potential hallucination
        evaluations.append({
            "title": paper["title"],
            "citations": paper["citations"] + 10,  # WRONG!
            "quality": "high"
        })
    
    return {
        "evaluations": evaluations,
        "papers_passed": len(evaluations)
    }


async def synthesis_without_cf(state: Dict[str, Any]) -> Dict[str, Any]:
    """Synthesis agent without ContextFlow - no consensus checking"""
    logger.info("[SYNTHESIS] Creating summary (WITHOUT ContextFlow)...")
    
    evaluations = state.get("evaluations", [])
    
    summary = {
        "total_papers": len(evaluations),
        "key_findings": [
            "Research shows promising results",
            "Methodology is sound"
        ],
        "confidence": 0.9  # Overconfident due to hallucination
    }
    
    return summary


# ============================================================================
# AGENT FUNCTIONS (WITH CONTEXTFLOW)
# ============================================================================

async def scout_with_cf(state: Dict[str, Any]) -> Dict[str, Any]:
    """Scout agent with ContextFlow - generates SSV and checks consensus"""
    logger.info("[SCOUT] Searching for papers (WITH ContextFlow)...")
    
    papers = [
        {"title": "Paper A", "citations": 100},
        {"title": "Paper B", "citations": 150},
    ]
    
    return {
        "papers": papers,
        "timestamp": datetime(2026, 8, 1).timestamp()
    }


async def critic_with_cf(state: Dict[str, Any]) -> Dict[str, Any]:
    """Critic agent with ContextFlow - generates SSV and checks consensus"""
    logger.info("[CRITIC] Evaluating papers (WITH ContextFlow)...")
    
    papers = state.get("papers", [])
    
    # Simulate using different data
    evaluations = []
    for paper in papers:
        evaluations.append({
            "title": paper["title"],
            "citations": paper["citations"] + 10,  # Different data
            "quality": "high"
        })
    
    return {
        "evaluations": evaluations,
        "papers_passed": len(evaluations)
    }


async def synthesis_with_cf(state: Dict[str, Any]) -> Dict[str, Any]:
    """Synthesis agent with ContextFlow - generates SSV and checks consensus"""
    logger.info("[SYNTHESIS] Creating summary (WITH ContextFlow)...")
    
    evaluations = state.get("evaluations", [])
    
    summary = {
        "total_papers": len(evaluations),
        "key_findings": [
            "Research shows promising results",
            "Methodology is sound"
        ],
        "confidence": 0.9
    }
    
    return summary


# ============================================================================
# WORKFLOW EXECUTION
# ============================================================================

async def run_without_contextflow():
    """Run workflow WITHOUT ContextFlow (baseline)"""
    print("\n" + "=" * 80)
    print("WORKFLOW WITHOUT CONTEXTFLOW (Baseline)")
    print("=" * 80)
    
    state = {"query": "multi-agent systems"}
    
    # Run agents sequentially without consensus checking
    state.update(await scout_without_cf(state))
    state.update(await critic_without_cf(state))
    result = await synthesis_without_cf(state)
    state.update(result)
    
    print(f"\n✓ Workflow completed")
    print(f"  Papers found: {state.get('total_papers', 0)}")
    print(f"  Confidence: {state.get('confidence', 0):.0%}")
    print(f"  ⚠️  No consensus checking - potential hallucination risk!")
    
    return state


async def run_with_contextflow():
    """Run workflow WITH ContextFlow (with consensus checking)"""
    print("\n" + "=" * 80)
    print("WORKFLOW WITH CONTEXTFLOW (Protected)")
    print("=" * 80)
    
    # Create workflow
    workflow = AgentWorkflow()
    
    # Create agents with ContextFlow
    scout_config = AgentConfig(
        agent_id="scout",
        current_task="Find research papers",
        constraints={"max_papers": 10},
        confidence_threshold=0.9,
        enable_consensus_check=True,
        auto_sync_on_divergence=True
    )
    
    critic_config = AgentConfig(
        agent_id="critic",
        current_task="Evaluate methodology",
        constraints={"rigor_threshold": 0.7},
        confidence_threshold=0.85,
        enable_consensus_check=True,
        auto_sync_on_divergence=True
    )
    
    synthesis_config = AgentConfig(
        agent_id="synthesis",
        current_task="Synthesize findings",
        constraints={"accuracy_threshold": 0.85},
        confidence_threshold=0.92,
        enable_consensus_check=True,
        auto_sync_on_divergence=True
    )
    
    scout_agent = ContextFlowAgent(config=scout_config, agent_function=scout_with_cf)
    critic_agent = ContextFlowAgent(config=critic_config, agent_function=critic_with_cf)
    synthesis_agent = ContextFlowAgent(config=synthesis_config, agent_function=synthesis_with_cf)
    
    # Add to workflow
    workflow.add_agent(scout_agent)
    workflow.add_agent(critic_agent)
    workflow.add_agent(synthesis_agent)
    
    # Run workflow
    initial_state = {"query": "multi-agent systems"}
    result = await workflow.run_sequential(initial_state, ["scout", "critic", "synthesis"])
    
    print(f"\n✓ Workflow completed with ContextFlow protection")
    print(f"  Papers found: {result.get('total_papers', 0)}")
    print(f"  Confidence: {result.get('confidence', 0):.0%}")
    
    # Print consensus information
    print("\n" + "-" * 80)
    print("CONSENSUS CHECKS")
    print("-" * 80)
    
    for agent_id, agent in workflow.agents.items():
        consensus = agent.get_consensus_result()
        if consensus:
            print(f"\n{agent_id.upper()}:")
            print(f"  Consensus Level: {consensus.level.value}")
            print(f"  Divergence Score: {consensus.divergence_score:.4f}")
            print(f"  Action: {consensus.recommended_action}")
    
    return result, workflow


def print_comparison(baseline, protected, workflow):
    """Print comparison metrics"""
    print("\n" + "=" * 80)
    print("COMPARISON: Without ContextFlow vs With ContextFlow")
    print("=" * 80)
    
    print("\nMetrics:")
    print(f"  Papers Found: {baseline.get('total_papers', 0)} (baseline) vs {protected.get('total_papers', 0)} (protected)")
    print(f"  Confidence: {baseline.get('confidence', 0):.0%} (baseline) vs {protected.get('confidence', 0):.0%} (protected)")
    
    print("\nContextFlow Benefits:")
    print(f"  ✓ Automatic SSV generation for each agent")
    print(f"  ✓ Real-time consensus checking between agents")
    print(f"  ✓ Divergence detection and auto-synchronization")
    print(f"  ✓ Audit trail via Async State Journal")
    print(f"  ✓ Hallucination prevention through state alignment")
    
    print("\nJournal Entries:", len(workflow.journal.entries))
    print(f"  Agents tracked: {len(workflow.agents)}")
    
    # Calculate hallucination prevention
    critical_events = sum(1 for e in workflow.journal.entries if "critical" in str(e).lower())
    prevention_rate = (1 - critical_events / max(len(workflow.journal.entries), 1)) * 100
    print(f"  Hallucination prevention rate: {prevention_rate:.1f}%")


async def main():
    """Main entry point"""
    print("=" * 80)
    print("CONTEXTFLOW RESEARCH WORKFLOW DEMO")
    print("Demonstrating hallucination prevention in multi-agent research")
    print("=" * 80)
    
    # Run baseline (without ContextFlow)
    baseline = await run_without_contextflow()
    
    # Run protected (with ContextFlow)
    protected, workflow = await run_with_contextflow()
    
    # Print comparison
    print_comparison(baseline, protected, workflow)
    
    print("\n" + "=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
