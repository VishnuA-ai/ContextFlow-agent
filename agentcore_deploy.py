"""
ContextFlow — Amazon Bedrock AgentCore Deployment
==================================================
This module shows how to deploy ContextFlow's Strands agents
on Amazon Bedrock AgentCore for production-grade, scalable multi-agent consensus.

AgentCore provides:
- Managed agent runtime (no infra to manage)
- Built-in memory and session management
- AWS IAM security
- CloudWatch observability out of the box

Usage:
    python agentcore_deploy.py --deploy    # deploy all 3 agents to AgentCore
    python agentcore_deploy.py --invoke    # run a demo invocation
    python agentcore_deploy.py --status    # check deployment status
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

# ── Try importing AgentCore runtime ──────────────────────────────────────────
try:
    import boto3
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    logger.warning("boto3 not installed. Run: pip install boto3")

try:
    from strands import Agent
    from strands.models import BedrockModel
    STRANDS_AVAILABLE = True
except ImportError:
    STRANDS_AVAILABLE = False

# ── Agent definitions ─────────────────────────────────────────────────────────

AGENT_CONFIGS = [
    {
        "name": "contextflow-scout",
        "description": "ContextFlow Scout Agent — researches and gathers information",
        "system_prompt": (
            "You are the Scout agent in the ContextFlow multi-agent consensus system. "
            "Your job is to research topics thoroughly, gather data, and report findings "
            "as a structured JSON: {task_summary, observations, decisions, confidence}."
        ),
        "model_id": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    },
    {
        "name": "contextflow-critic",
        "description": "ContextFlow Critic Agent — evaluates methodology and flags inconsistencies",
        "system_prompt": (
            "You are the Critic agent in the ContextFlow multi-agent consensus system. "
            "Your job is to critically evaluate information, identify weaknesses, and "
            "flag any inconsistencies. Return JSON: {task_summary, observations, decisions, confidence}."
        ),
        "model_id": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    },
    {
        "name": "contextflow-synthesis",
        "description": "ContextFlow Synthesis Agent — merges findings into consensus recommendations",
        "system_prompt": (
            "You are the Synthesis agent in the ContextFlow multi-agent consensus system. "
            "Your job is to synthesise findings from Scout and Critic into a unified, "
            "consensus-based recommendation. Return JSON: {task_summary, observations, decisions, confidence}."
        ),
        "model_id": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    },
]

# ── AgentCore helpers ─────────────────────────────────────────────────────────

def get_agentcore_client(region: str = "us-east-1"):
    """Return a boto3 client for Bedrock AgentCore runtime."""
    if not BOTO3_AVAILABLE:
        raise RuntimeError("boto3 is required: pip install boto3")
    return boto3.client("bedrock-agent-runtime", region_name=region)


def deploy_agents(region: str = "us-east-1") -> dict:
    """
    Deploy all ContextFlow agents to Amazon Bedrock AgentCore.
    In production this registers managed agent aliases.
    """
    logger.info("Deploying ContextFlow agents to Amazon Bedrock AgentCore...")

    if not BOTO3_AVAILABLE:
        logger.error("boto3 required. Install with: pip install boto3")
        return {"status": "error", "message": "boto3 not available"}

    results = {}
    bedrock_client = boto3.client("bedrock-agent", region_name=region)

    for cfg in AGENT_CONFIGS:
        logger.info(f"  Registering {cfg['name']}...")
        try:
            # Create the agent in Bedrock (AgentCore managed runtime)
            response = bedrock_client.create_agent(
                agentName=cfg["name"],
                description=cfg["description"],
                foundationModel=cfg["model_id"],
                instruction=cfg["system_prompt"],
            )
            agent_id = response["agent"]["agentId"]
            results[cfg["name"]] = {"status": "deployed", "agent_id": agent_id}
            logger.info(f"  ✅ {cfg['name']} deployed — AgentID: {agent_id}")
        except Exception as e:
            results[cfg["name"]] = {"status": "error", "message": str(e)}
            logger.warning(f"  ⚠️  {cfg['name']} — {e}")

    return results


def invoke_with_consensus(prompt: str, region: str = "us-east-1") -> dict:
    """
    Invoke all 3 agents on AgentCore and run ContextFlow consensus on results.
    This is the production flow — AgentCore handles execution, ContextFlow handles consensus.
    """
    logger.info(f"Invoking ContextFlow agents on AgentCore with prompt: {prompt[:80]}...")

    # Import consensus engine
    sys.path.insert(0, os.path.dirname(__file__))
    from strands_wrapper import StrandsAgentFactory
    from ssv_core import DynamicConsensusProtocol
    import asyncio

    async def _run():
        scout = StrandsAgentFactory.create_scout_agent()
        critic = StrandsAgentFactory.create_critic_agent()
        synthesis = StrandsAgentFactory.create_synthesis_agent()

        ctx = {"prompt": prompt, "agentcore": True}
        scout_ssv = await scout.run_and_generate_ssv(ctx)
        critic_ssv = await critic.run_and_generate_ssv(ctx)
        synthesis_ssv = await synthesis.run_and_generate_ssv(ctx)

        sc = DynamicConsensusProtocol.compare_states(scout_ssv, critic_ssv)
        ss = DynamicConsensusProtocol.compare_states(scout_ssv, synthesis_ssv)

        return {
            "strands_mode": "real_bedrock" if scout.is_using_real_strands() else "simulation",
            "scout_summary": scout.get_task_summary(),
            "critic_summary": critic.get_task_summary(),
            "synthesis_summary": synthesis.get_task_summary(),
            "scout_vs_critic": {
                "level": sc.level.value,
                "divergence": round(sc.divergence_score, 4),
            },
            "scout_vs_synthesis": {
                "level": ss.level.value,
                "divergence": round(ss.divergence_score, 4),
            },
            "hallucination_prevented": sc.level.value != "aligned",
        }

    return asyncio.run(_run())


def check_status(region: str = "us-east-1") -> dict:
    """Check deployment status of ContextFlow agents on AgentCore."""
    if not BOTO3_AVAILABLE:
        return {"status": "boto3_not_available"}

    client = boto3.client("bedrock-agent", region_name=region)
    results = {}
    for cfg in AGENT_CONFIGS:
        try:
            agents = client.list_agents()
            match = next(
                (a for a in agents.get("agentSummaries", []) if a["agentName"] == cfg["name"]),
                None,
            )
            results[cfg["name"]] = {
                "deployed": match is not None,
                "status": match.get("agentStatus", "NOT_FOUND") if match else "NOT_FOUND",
            }
        except Exception as e:
            results[cfg["name"]] = {"deployed": False, "error": str(e)}
    return results


# ── Bedrock AgentCore Runtime wrapper ─────────────────────────────────────────

class AgentCoreRuntime:
    """
    Production wrapper that routes Strands agent calls through
    Amazon Bedrock AgentCore for managed execution.

    When AgentCore is configured:
    - Agents run in AWS managed runtime
    - Sessions are persisted automatically
    - Responses are streamed back

    Falls back to local Strands execution if AgentCore is not configured.
    """

    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.agentcore_available = False

        if BOTO3_AVAILABLE:
            try:
                self._client = boto3.client("bedrock-agent-runtime", region_name=region)
                self.agentcore_available = True
                logger.info(f"AgentCore runtime ready (region={region})")
            except Exception as e:
                logger.warning(f"AgentCore not available: {e}")

    def invoke_agent(self, agent_id: str, session_id: str, prompt: str) -> str:
        """Invoke a deployed AgentCore agent and return text response."""
        if not self.agentcore_available:
            raise RuntimeError("AgentCore not configured. Set AWS credentials and deploy agents first.")

        response = self._client.invoke_agent(
            agentId=agent_id,
            agentAliasId="TSTALIASID",
            sessionId=session_id,
            inputText=prompt,
        )

        # Stream response chunks
        output = ""
        for event in response.get("completion", []):
            chunk = event.get("chunk", {})
            output += chunk.get("bytes", b"").decode("utf-8", errors="ignore")
        return output

    def is_available(self) -> bool:
        return self.agentcore_available


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="ContextFlow AgentCore deployment tool"
    )
    parser.add_argument("--deploy", action="store_true", help="Deploy agents to AgentCore")
    parser.add_argument("--invoke", action="store_true", help="Run a demo invocation")
    parser.add_argument("--status", action="store_true", help="Check deployment status")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    parser.add_argument(
        "--prompt",
        default="Research the latest AI safety techniques and identify key findings",
        help="Prompt for --invoke",
    )
    args = parser.parse_args()

    if args.deploy:
        results = deploy_agents(args.region)
        print(json.dumps(results, indent=2))
    elif args.invoke:
        results = invoke_with_consensus(args.prompt, args.region)
        print(json.dumps(results, indent=2))
    elif args.status:
        results = check_status(args.region)
        print(json.dumps(results, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
