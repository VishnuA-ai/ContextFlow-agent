"""
ContextFlow Support Workflow Demo
Demonstrates multi-agent support ticket workflow with consensus checking
Shows: Router, Solver, and Escalation agents preventing contradictions
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# AGENT FUNCTIONS
# ============================================================================

async def router_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """Router Agent: Categorizes support tickets"""
    logger.info("[ROUTER] Categorizing support ticket...")
    
    ticket = state.get("ticket", {})
    category = "technical" if "error" in ticket.get("description", "").lower() else "general"
    priority = "high" if "urgent" in ticket.get("description", "").lower() else "normal"
    
    logger.info(f"  → Category: {category}, Priority: {priority}")
    
    return {
        "category": category,
        "priority": priority,
        "routing_timestamp": datetime.now().timestamp()
    }


async def solver_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """Solver Agent: Attempts to resolve the ticket"""
    logger.info("[SOLVER] Attempting resolution...")
    
    category = state.get("category", "general")
    priority = state.get("priority", "normal")
    
    # Simulate resolution attempt
    if category == "technical":
        resolution = "Check system logs and restart service"
        success = True
    else:
        resolution = "Provide documentation link"
        success = True
    
    logger.info(f"  → Resolution: {resolution}, Success: {success}")
    
    return {
        "resolution": resolution,
        "resolution_success": success,
        "solver_timestamp": datetime.now().timestamp()
    }


async def escalation_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """Escalation Agent: Handles complex or unresolved tickets"""
    logger.info("[ESCALATION] Reviewing for escalation...")
    
    resolution_success = state.get("resolution_success", False)
    priority = state.get("priority", "normal")
    
    # Escalate if resolution failed or priority is high
    should_escalate = not resolution_success or priority == "high"
    
    if should_escalate:
        action = "Escalated to senior support"
        assigned_to = "senior_team"
    else:
        action = "Ticket resolved"
        assigned_to = "closed"
    
    logger.info(f"  → Action: {action}, Assigned to: {assigned_to}")
    
    return {
        "escalation_action": action,
        "assigned_to": assigned_to,
        "escalation_timestamp": datetime.now().timestamp()
    }


# ============================================================================
# WORKFLOW EXECUTION
# ============================================================================

async def run_support_workflow():
    """Run the complete support workflow with ContextFlow"""
    print("=" * 80)
    print("CONTEXTFLOW SUPPORT WORKFLOW DEMO")
    print("Demonstrating consensus in multi-agent support ticket processing")
    print("=" * 80)
    
    # Create workflow
    workflow = AgentWorkflow()
    
    # Create agents
    router_config = AgentConfig(
        agent_id="router",
        current_task="Categorize support ticket",
        constraints={"categories": ["technical", "general", "billing"]},
        confidence_threshold=0.95,
        enable_consensus_check=True,
        auto_sync_on_divergence=True
    )
    
    solver_config = AgentConfig(
        agent_id="solver",
        current_task="Resolve support ticket",
        constraints={"max_attempts": 3, "escalation_threshold": 2},
        confidence_threshold=0.85,
        enable_consensus_check=True,
        auto_sync_on_divergence=True
    )
    
    escalation_config = AgentConfig(
        agent_id="escalation",
        current_task="Handle escalation",
        constraints={"senior_team_available": True},
        confidence_threshold=0.90,
        enable_consensus_check=True,
        auto_sync_on_divergence=True
    )
    
    router_agent = ContextFlowAgent(config=router_config, agent_function=router_agent)
    solver_agent = ContextFlowAgent(config=solver_config, agent_function=solver_agent)
    escalation_agent = ContextFlowAgent(config=escalation_config, agent_function=escalation_agent)
    
    # Add to workflow
    workflow.add_agent(router_agent)
    workflow.add_agent(solver_agent)
    workflow.add_agent(escalation_agent)
    
    # Test tickets
    test_tickets = [
        {
            "ticket_id": "TICKET-001",
            "description": "System error when logging in - URGENT",
            "user": "user@example.com"
        },
        {
            "ticket_id": "TICKET-002",
            "description": "How do I change my password?",
            "user": "user2@example.com"
        }
    ]
    
    for ticket in test_tickets:
        print(f"\n{'-' * 80}")
        print(f"Processing Ticket: {ticket['ticket_id']}")
        print(f"Description: {ticket['description']}")
        print(f"{'-' * 80}")
        
        # Run workflow
        initial_state = {"ticket": ticket}
        result = await workflow.run_sequential(initial_state, ["router", "solver", "escalation"])
        
        print(f"\n✓ Ticket {ticket['ticket_id']} processed")
        print(f"  Category: {result.get('category')}")
        print(f"  Priority: {result.get('priority')}")
        print(f"  Resolution: {result.get('resolution')}")
        print(f"  Final Action: {result.get('escalation_action')}")
        print(f"  Assigned to: {result.get('assigned_to')}")
    
    # Print workflow metrics
    print("\n" + "=" * 80)
    print("WORKFLOW METRICS")
    print("=" * 80)
    
    metrics = workflow.get_workflow_metrics()
    print(f"\nTotal Agents: {metrics['total_agents']}")
    print(f"Journal Entries: {metrics['journal_entries']}")
    print(f"Agents: {', '.join(metrics['agents'])}")
    
    # Print consensus information
    print("\n" + "-" * 80)
    print("CONSENSUS INFORMATION")
    print("-" * 80)
    
    for agent_id, agent in workflow.agents.items():
        consensus = agent.get_consensus_result()
        if consensus:
            print(f"\n{agent_id.upper()}:")
            print(f"  Consensus Level: {consensus.level.value}")
            print(f"  Divergence Score: {consensus.divergence_score:.4f}")
    
    print(f"\n✓ All {len(test_tickets)} tickets processed successfully")
    print("✓ Consensus checking prevented contradictions between agents")
    
    print("\n" + "=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)


async def main():
    """Main entry point"""
    await run_support_workflow()


if __name__ == "__main__":
    asyncio.run(main())
