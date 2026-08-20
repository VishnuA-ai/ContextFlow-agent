"""
Strands Agents SDK Integration for ContextFlow
This module wraps Strands Agents to work with ContextFlow's consensus system.

Each agent is a real Strands Agent that:
1. Receives a task and context
2. Reasons about it using the configured model (Amazon Bedrock via Strands SDK)
3. Returns a structured observation that feeds into the SSV consensus layer

With AWS credentials configured, agents run on Amazon Bedrock (Claude 3 Sonnet).
Without credentials, agents run in simulation mode with realistic outputs so the
demo always works end-to-end.
"""

from __future__ import annotations

import json
import time
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Try to import the real Strands SDK
# ---------------------------------------------------------------------------
try:
    from strands import Agent
    from strands.models import BedrockModel
    STRANDS_AVAILABLE = True
    logger.info("Strands Agents SDK loaded successfully")
except ImportError:
    STRANDS_AVAILABLE = False
    logger.warning("Strands SDK not installed – running in simulation mode")

from ssv_core import SemanticStateVector, SSVGenerator


# ---------------------------------------------------------------------------
# Simulation responses — realistic outputs used when AWS creds are absent
# ---------------------------------------------------------------------------

_SIMULATION_RESPONSES: Dict[str, Dict[str, Any]] = {
    "scout": {
        "task_summary": "Researched 15 AI safety papers (2025-2026). "
                        "Key finding: Constitutional AI cited 145 times in peer-reviewed venues.",
        "observations": {
            "papers_reviewed": 15,
            "top_paper_citations": 145,
            "top_paper_title": "Constitutional AI: Harmlessness from AI Feedback",
            "top_venue": "NeurIPS 2025",
            "domains": ["Constitutional AI", "RLHF", "Debate"],
            "confidence_in_data": 0.85,
        },
        "decisions": [
            "Prioritised Constitutional AI over RLHF due to citation velocity",
            "Filtered papers by peer-reviewed venues only",
            "Flagged 3 papers for Critic review",
        ],
        "confidence": 0.85,
    },
    "critic": {
        "task_summary": "Evaluated methodology of 12 AI safety papers. "
                        "Note: found citation count discrepancy – top paper shows 156 citations "
                        "in my dataset (newer index, Oct 2026).",
        "observations": {
            "papers_evaluated": 12,
            "top_paper_citations": 156,          # <-- intentional divergence from scout
            "top_paper_title": "Constitutional AI: Harmlessness from AI Feedback",
            "top_venue": "NeurIPS 2025",
            "domains": ["Adversarial Testing", "Red Teaming"],
            "methodology_score": 0.72,
            "confidence_in_data": 0.75,
        },
        "decisions": [
            "Questioned Constitutional AI blind spots in adversarial settings",
            "Recommended red-team testing before deployment",
            "Flagged citation count inconsistency with Scout",
        ],
        "confidence": 0.75,
    },
    "synthesis": {
        "task_summary": "Synthesised Scout and Critic findings. "
                        "After ContextFlow consensus sync, agreed on 150 citations (averaged). "
                        "Hybrid approach recommended.",
        "observations": {
            "papers_synthesised": 15,
            "top_paper_citations": 150,          # post-consensus value
            "top_paper_title": "Constitutional AI: Harmlessness from AI Feedback",
            "conflicts_resolved": 1,
            "consensus_level": "aligned",
            "final_recommendation": "Hybrid Constitutional AI + Red-Team approach",
            "confidence_in_data": 0.92,
        },
        "decisions": [
            "Merged Scout and Critic datasets",
            "Resolved citation discrepancy via ContextFlow weighted average",
            "Produced unified recommendation with 92% confidence",
        ],
        "confidence": 0.90,
    },
}


# ---------------------------------------------------------------------------
# StrandsAgentWrapper
# ---------------------------------------------------------------------------

class StrandsAgentWrapper:
    """
    Wraps a Strands Agent to integrate with ContextFlow's consensus system.

    Behaviour:
    - If AWS credentials are configured → uses real Strands Agent on Bedrock.
    - If not → uses simulation mode so the demo always runs cleanly.

    Either way the SSV (Semantic State Vector) is generated from the agent's
    output and fed into the ContextFlow consensus layer.
    """

    def __init__(self, agent_id: str, task: str, model_id: str = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"):
        self.agent_id = agent_id
        self.task = task
        self.model_id = model_id
        self.ssv: Optional[SemanticStateVector] = None
        self.current_state: Dict[str, Any] = {}
        self._last_response: Dict[str, Any] = {}

        # Try to initialise a real Strands Agent
        self.strands_agent: Optional[Any] = None
        self.using_strands = False

        if STRANDS_AVAILABLE:
            try:
                model = BedrockModel(model_id=model_id)
                self.strands_agent = Agent(
                    system_prompt=(
                        f"You are a specialised AI research agent. Your role: {task}. "
                        "When given a research context, analyse it carefully and return a "
                        "JSON object with keys: task_summary (str), observations (dict), "
                        "decisions (list[str]), confidence (float 0-1)."
                    ),
                    model=model,
                )
                self.using_strands = True
                logger.info(f"[{agent_id}] Strands Agent initialised on Bedrock ({model_id})")
            except Exception as exc:
                logger.warning(
                    f"[{agent_id}] Bedrock init failed ({exc}). Using simulation mode."
                )

    # ------------------------------------------------------------------
    # Core method: run the agent and generate an SSV
    # ------------------------------------------------------------------

    async def run_and_generate_ssv(self, context: Dict[str, Any]) -> SemanticStateVector:
        """
        Run the Strands agent (or simulation) with the given context,
        then generate and return a Semantic State Vector.
        """
        if self.using_strands and self.strands_agent is not None:
            response_data = await self._run_strands(context)
        else:
            response_data = self._run_simulation()

        self._last_response = response_data
        self.current_state = {
            "agent_id": self.agent_id,
            "task": self.task,
            "context": context,
            "response": response_data,
            "timestamp": time.time(),
            "using_strands": self.using_strands,
        }

        observations = response_data.get("observations", context)
        decisions = response_data.get("decisions", [])
        confidence = float(response_data.get("confidence", 0.8))

        self.ssv = SSVGenerator.generate_ssv(
            agent_id=self.agent_id,
            current_task=self.task,
            observations=observations,
            decisions_made=decisions,
            constraints={"model": self.model_id, "using_strands": self.using_strands},
            confidence=confidence,
        )

        logger.info(
            f"[{self.agent_id}] SSV generated. "
            f"Hash={self.ssv.state_hash[:12]}... "
            f"Strands={'real' if self.using_strands else 'sim'}"
        )
        return self.ssv

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _run_strands(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke the real Strands Agent and parse its JSON response."""
        prompt = (
            f"Context provided to you:\n{json.dumps(context, indent=2)}\n\n"
            "Return ONLY a valid JSON object with keys: "
            "task_summary, observations, decisions, confidence."
        )
        try:
            # Strands Agent is synchronous; run in executor to avoid blocking
            import asyncio
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: self.strands_agent(prompt))
            # Extract text content from Strands response
            raw_text = str(result)
            # Find JSON block
            start = raw_text.find("{")
            end = raw_text.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(raw_text[start:end])
        except Exception as exc:
            logger.error(f"[{self.agent_id}] Strands call failed: {exc}. Falling back to simulation.")
        return self._run_simulation()

    def _run_simulation(self) -> Dict[str, Any]:
        """Return realistic simulated output for demo purposes."""
        sim = _SIMULATION_RESPONSES.get(self.agent_id)
        if sim:
            return sim
        # Generic fallback for custom agents
        return {
            "task_summary": f"Completed task: {self.task}",
            "observations": {"task": self.task, "status": "completed"},
            "decisions": [f"Executed {self.task}"],
            "confidence": 0.80,
        }

    # ------------------------------------------------------------------
    # Convenience accessors
    # ------------------------------------------------------------------

    def get_state_hash(self) -> str:
        return self.ssv.state_hash if self.ssv else ""

    def get_observations(self) -> Dict[str, Any]:
        return self._last_response.get("observations", {})

    def get_task_summary(self) -> str:
        return self._last_response.get("task_summary", self.task)

    def get_confidence(self) -> float:
        return float(self._last_response.get("confidence", 0.8))

    def is_using_real_strands(self) -> bool:
        return self.using_strands


# ---------------------------------------------------------------------------
# StrandsAgentFactory
# ---------------------------------------------------------------------------

class StrandsAgentFactory:
    """Factory for creating the standard ContextFlow demo agents."""

    @staticmethod
    def create_scout_agent() -> StrandsAgentWrapper:
        return StrandsAgentWrapper(
            agent_id="scout",
            task=(
                "Research and gather information on AI safety techniques. "
                "Focus on citation counts, publication venues, and key findings."
            ),
        )

    @staticmethod
    def create_critic_agent() -> StrandsAgentWrapper:
        return StrandsAgentWrapper(
            agent_id="critic",
            task=(
                "Critically evaluate AI safety research methodology. "
                "Identify weaknesses, verify data accuracy, and flag inconsistencies."
            ),
        )

    @staticmethod
    def create_synthesis_agent() -> StrandsAgentWrapper:
        return StrandsAgentWrapper(
            agent_id="synthesis",
            task=(
                "Synthesise findings from Scout and Critic agents into a unified, "
                "consensus-based recommendation. Resolve any conflicts."
            ),
        )

    @staticmethod
    def create_custom_agent(agent_id: str, task: str) -> StrandsAgentWrapper:
        return StrandsAgentWrapper(agent_id=agent_id, task=task)
