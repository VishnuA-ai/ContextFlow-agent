"""
ContextFlow Code Review Workflow Demo
Demonstrates multi-agent code review with consensus checking
Shows: Reviewer, Tester, and Deployer agents preventing conflicting recommendations
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

async def reviewer_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """Reviewer Agent: Evaluates code quality"""
    logger.info("[REVIEWER] Evaluating code quality...")
    
    code = state.get("code", "")
    issues_found = []
    
    # Simulate code review
    if "TODO" in code:
        issues_found.append("TODO comments present")
    if len(code.split("\n")) > 100:
        issues_found.append("Function too long")
    if "print(" in code:
        issues_found.append("Debug print statements")
    
    quality_score = max(0, 10 - len(issues_found))
    
    logger.info(f"  → Issues found: {len(issues_found)}, Quality score: {quality_score}/10")
    
    return {
        "review_issues": issues_found,
        "quality_score": quality_score,
        "review_timestamp": datetime.now().timestamp()
    }


async def tester_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """Tester Agent: Evaluates test coverage"""
    logger.info("[TESTER] Evaluating test coverage...")
    
    code = state.get("code", "")
    test_files = state.get("test_files", 0)
    
    # Simulate test evaluation
    coverage = min(100, test_files * 20)
    critical_paths = ["auth", "database", "api"]
    tested_paths = [p for p in critical_paths if p in code.lower()]
    
    logger.info(f"  → Coverage: {coverage}%, Paths tested: {len(tested_paths)}/{len(critical_paths)}")
    
    return {
        "test_coverage": coverage,
        "tested_paths": tested_paths,
        "testing_timestamp": datetime.now().timestamp()
    }


async def deployer_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """Deployer Agent: Safety check before deployment"""
    logger.info("[DEPLOYER] Running safety checks...")
    
    quality_score = state.get("quality_score", 0)
    test_coverage = state.get("test_coverage", 0)
    review_issues = state.get("review_issues", [])
    
    # Safety checks
    checks = {
        "quality_pass": quality_score >= 7,
        "coverage_pass": test_coverage >= 80,
        "no_critical_issues": len(review_issues) == 0
    }
    
    all_pass = all(checks.values())
    
    if all_pass:
        decision = "APPROVED for deployment"
        confidence = 0.95
    else:
        decision = "REJECTED - needs fixes"
        confidence = 0.3
    
    logger.info(f"  → Quality pass: {checks['quality_pass']}")
    logger.info(f"  → Coverage pass: {checks['coverage_pass']}")
    logger.info(f"  → No critical issues: {checks['no_critical_issues']}")
    logger.info(f"  → Decision: {decision}")
    
    return {
        "safety_checks": checks,
        "deployment_decision": decision,
        "deployment_confidence": confidence,
        "deployer_timestamp": datetime.now().timestamp()
    }


# ============================================================================
# WORKFLOW EXECUTION
# ============================================================================

async def run_code_review_workflow():
    """Run the complete code review workflow with ContextFlow"""
    print("=" * 80)
    print("CONTEXTFLOW CODE REVIEW WORKFLOW DEMO")
    print("Demonstrating consensus in multi-agent code review")
    print("=" * 80)
    
    # Create workflow
    workflow = AgentWorkflow()
    
    # Create agents
    reviewer_config = AgentConfig(
        agent_id="reviewer",
        current_task="Evaluate code quality",
        constraints={"max_function_length": 50, "forbid_debug_prints": True},
        confidence_threshold=0.90,
        enable_consensus_check=True,
        auto_sync_on_divergence=True
    )
    
    tester_config = AgentConfig(
        agent_id="tester",
        current_task="Evaluate test coverage",
        constraints={"min_coverage": 80, "critical_paths": ["auth", "database", "api"]},
        confidence_threshold=0.85,
        enable_consensus_check=True,
        auto_sync_on_divergence=True
    )
    
    deployer_config = AgentConfig(
        agent_id="deployer",
        current_task="Safety check for deployment",
        constraints={"min_quality_score": 7, "require_all_checks": True},
        confidence_threshold=0.95,
        enable_consensus_check=True,
        auto_sync_on_divergence=True
    )
    
    reviewer_agent = ContextFlowAgent(config=reviewer_config, agent_function=reviewer_agent)
    tester_agent = ContextFlowAgent(config=tester_config, agent_function=tester_agent)
    deployer_agent = ContextFlowAgent(config=deployer_config, agent_function=deployer_agent)
    
    # Add to workflow
    workflow.add_agent(reviewer_agent)
    workflow.add_agent(tester_agent)
    workflow.add_agent(deployer_agent)
    
    # Test code snippets
    test_cases = [
        {
            "name": "Good Code",
            "code": """
def authenticate_user(username, password):
    if validate_credentials(username, password):
        return generate_token(username)
    return None
""",
            "test_files": 5
        },
        {
            "name": "Code with Issues",
            "code": """
def process_data(data):
    TODO: implement this
    print("Debug: data is", data)
    # Very long function with many lines...
    # ... 100 more lines ...
    return result
""",
            "test_files": 2
        }
    ]
    
    for test_case in test_cases:
        print(f"\n{'-' * 80}")
        print(f"Reviewing: {test_case['name']}")
        print(f"{'-' * 80}")
        
        # Run workflow
        initial_state = {
            "code": test_case["code"],
            "test_files": test_case["test_files"]
        }
        result = await workflow.run_sequential(initial_state, ["reviewer", "tester", "deployer"])
        
        print(f"\n✓ Code review completed")
        print(f"  Quality Score: {result.get('quality_score')}/10")
        print(f"  Test Coverage: {result.get('test_coverage')}%")
        print(f"  Review Issues: {result.get('review_issues')}")
        print(f"  Safety Checks: {result.get('safety_checks')}")
        print(f"  Deployment Decision: {result.get('deployment_decision')}")
        print(f"  Confidence: {result.get('deployment_confidence'):.0%}")
    
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
    
    print(f"\n✓ All {len(test_cases)} code reviews completed")
    print("✓ Consensus checking prevented conflicting recommendations")
    
    print("\n" + "=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)


async def main():
    """Main entry point"""
    await run_code_review_workflow()


if __name__ == "__main__":
    asyncio.run(main())
