"""
ContextFlow: Agent State Fingerprint (ASF) Core Implementation
==============================================================

TERMINOLOGY NOTE (Problem 12):
  The "Semantic State Vector" in this codebase is NOT a mathematical
  embedding vector. It is a structured agent-state snapshot with a
  SHA-256 cryptographic fingerprint for tamper detection.

  Accurate name: "Agent State Fingerprint" (ASF) / "Structured Agent State"
  SHA-256 is used ONLY for state integrity checking — NOT for semantic
  similarity, NOT for correctness detection.

  The class retains the name SemanticStateVector for API backward
  compatibility, but all documentation now reflects the true nature.

Prevents multi-agent context drift through structured state comparison
and evidence-based conflict verification.
"""

import hashlib
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import asyncio


# ============================================================================
# CORE DATA STRUCTURES
# ============================================================================

class ConsensusLevel(Enum):
    """
    Consensus health states after DCP comparison.

    GREEN     — agents agree, proceed
    YELLOW    — minor drift detected, monitor
    RED       — critical divergence, block and verify
    UNRESOLVED — conflict detected but evidence insufficient to resolve
                 (Problem 5: do NOT auto-sync when UNRESOLVED)
    """
    GREEN      = "aligned"
    YELLOW     = "minor_drift"
    RED        = "critical"
    UNRESOLVED = "unresolved"   # NEW — conflict with insufficient evidence


class VerificationStatus(Enum):
    """Result of the evidence-based Verifier."""
    RESOLVED_A   = "RESOLVED_A"    # Agent A's claim is better supported
    RESOLVED_B   = "RESOLVED_B"    # Agent B's claim is better supported
    UNRESOLVED   = "UNRESOLVED"    # Insufficient evidence to choose


@dataclass
class EvidenceMeta:
    """
    Evidence metadata attached to a specific claim field.
    (Problem 3: WHY an agent believes something, not just WHAT)
    """
    claim_value: Any                        # The value the agent is claiming
    source: str                             # Where this value came from
    source_type: str                        # "live_api" | "database" | "document" | "cache" | "inferred"
    source_timestamp: float                 # When the source was last updated (Unix)
    confidence: float                       # Agent's per-field confidence 0–1
    task_id: Optional[str] = None          # Which task produced this claim


# Source type reliability hierarchy (higher = more reliable)
SOURCE_RELIABILITY: Dict[str, int] = {
    "live_api":   5,
    "database":   4,
    "document":   3,
    "cache":      2,
    "inferred":   1,
    "unknown":    0,
}


@dataclass
class VerificationResult:
    """
    Result returned by the EvidenceVerifier.
    (Problem 4: structured verifier output)
    """
    status: VerificationStatus
    recommended_value: Any
    reason: str
    evidence: List[Dict[str, Any]]
    confidence: float
    field_name: str
    agent_a_id: str
    agent_b_id: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class SemanticStateVector:
    """
    Structured agent-state snapshot with SHA-256 integrity fingerprint.

    ACCURATE DESCRIPTION (Problem 12):
      This is NOT a mathematical semantic embedding.
      It is a structured snapshot of an agent's beliefs, decisions,
      intent, and constraints — with a SHA-256 hash for tamper detection.

    SHA-256 (state_hash) is used ONLY to detect if a state was modified.
    It is NOT used for semantic similarity or correctness comparison.

    Evidence fields (Problem 3):
      field_evidence maps each observation field name to an EvidenceMeta
      object describing WHERE that belief came from.
    """
    agent_id: str
    timestamp: float
    intent_vector: Dict[str, float]   # What the agent is trying to accomplish
    constraint_set: Dict[str, Any]    # Rules the agent must follow
    belief_state: Dict[str, Any]      # Current facts the agent believes
    decision_history: List[str]       # Last 5 decisions made
    confidence_score: float           # Overall 0-1 confidence
    state_hash: str                   # SHA-256 of normalised state — integrity only
    version: str = "2.0"

    # NEW — per-field evidence metadata (Problem 3)
    field_evidence: Dict[str, Any] = field(default_factory=dict)

    # NEW — sync history: why did this agent change? (Problem 6/7)
    sync_history: List[Dict[str, Any]] = field(default_factory=list)

    def to_compact(self) -> str:
        return json.dumps(asdict(self), default=str)

    @classmethod
    def from_compact(cls, json_str: str) -> "SemanticStateVector":
        data = json.loads(json_str)
        return cls(**data)


@dataclass
class ConsensusResult:
    """
    Result of DCP comparison between two agent states.
    (Problem 11: sync_payload now has honest terminology)
    """
    level: ConsensusLevel
    divergence_score: float           # 0–1, structural divergence between states
    mismatch_fields: List[str]        # Which state fields differ
    recommended_action: str           # What to do next
    sync_payload: Optional[Dict[str, Any]] = None

    # NEW — verification result, populated after EvidenceVerifier runs
    verification: Optional[VerificationResult] = None


# ============================================================================
# AGENT STATE FINGERPRINT GENERATOR
# (formerly SSVGenerator — name kept for backward compatibility)
# ============================================================================

class SSVGenerator:
    """
    Generates a structured agent-state snapshot with SHA-256 integrity hash.

    SHA-256 is used ONLY for tamper detection (state integrity).
    It is NOT a semantic similarity measure.
    """

    @staticmethod
    def generate_ssv(
        agent_id: str,
        current_task: str,
        observations: Dict[str, Any],
        decisions_made: List[str],
        constraints: Dict[str, Any],
        confidence: float = 0.8,
        field_evidence: Optional[Dict[str, Any]] = None,   # NEW (Problem 3)
    ) -> SemanticStateVector:
        """
        Generate a structured agent-state snapshot from agent observations.

        Args:
            agent_id:       Unique agent identifier
            current_task:   What the agent is currently working on
            observations:   Facts the agent believes
            decisions_made: List of decisions made so far
            constraints:    Rules the agent must follow
            confidence:     Overall agent confidence 0–1
            field_evidence: Per-field EvidenceMeta dicts (optional)

        Returns:
            SemanticStateVector — structured snapshot with SHA-256 fingerprint
        """
        intent_vector = SSVGenerator._extract_intent(current_task, observations)
        recent_decisions = decisions_made[-5:]

        # Normalised state for SHA-256 fingerprint
        # SHA-256 here = tamper detection only, NOT semantic comparison
        normalized_state = {
            "agent":       agent_id,
            "task":        current_task,
            "intent":      intent_vector,
            "constraints": constraints,
            "observations": observations,
            "decisions":   recent_decisions,
        }
        state_bytes = json.dumps(normalized_state, sort_keys=True, default=str).encode()
        state_hash  = hashlib.sha256(state_bytes).hexdigest()

        return SemanticStateVector(
            agent_id        = agent_id,
            timestamp       = time.time(),
            intent_vector   = intent_vector,
            constraint_set  = constraints,
            belief_state    = observations,
            decision_history= recent_decisions,
            confidence_score= confidence,
            state_hash      = state_hash,
            field_evidence  = field_evidence or {},
        )

    @staticmethod
    def _extract_intent(task: str, observations: Dict) -> Dict[str, float]:
        """
        Extract a simple intent representation from task and observations.
        Returns numeric observation values as intent weights.
        (NOT a semantic embedding — just a structural summary)
        """
        intent = {}
        for key, value in observations.items():
            if isinstance(value, (int, float)):
                intent[key] = float(value)
            elif isinstance(value, str) and len(value) < 100:
                intent[f"has_{key}"] = 1.0
        return intent if intent else {"task_acknowledged": 1.0}


# ============================================================================
# DYNAMIC CONSENSUS PROTOCOL (DCP)
# ============================================================================

class DynamicConsensusProtocol:
    """
    Detects structural divergence between two agent state snapshots.

    IMPORTANT (Problem 2):
      DCP detects DISAGREEMENT between agents.
      It does NOT determine which agent is CORRECT.
      Truth/correctness determination is handled by EvidenceVerifier.

    Flow:
      compare_states() → detects divergence level
      If RED → caller should invoke EvidenceVerifier
      EvidenceVerifier → returns RESOLVED_A / RESOLVED_B / UNRESOLVED
    """

    CRITICAL_DRIFT_THRESHOLD = 0.15   # > 15% → RED
    WARNING_DRIFT_THRESHOLD  = 0.05   # > 5%  → YELLOW

    @staticmethod
    def compare_states(
        ssv_a: SemanticStateVector,
        ssv_b: SemanticStateVector,
    ) -> ConsensusResult:
        """
        Compare two agent state snapshots.
        Returns a ConsensusResult indicating divergence level.
        Does NOT resolve truth — use EvidenceVerifier for that.
        """
        divergence_score = 0.0
        mismatch_fields  = []

        # 1. Intent vector divergence (40%)
        intent_diff = DynamicConsensusProtocol._vector_difference(
            ssv_a.intent_vector, ssv_b.intent_vector
        )
        divergence_score += intent_diff * 0.4
        if intent_diff > 0.05:
            mismatch_fields.append("intent_vector")

        # 2. Belief state divergence (40%)
        belief_diff = DynamicConsensusProtocol._state_difference(
            ssv_a.belief_state, ssv_b.belief_state
        )
        divergence_score += belief_diff * 0.4
        if belief_diff > 0.05:
            mismatch_fields.append("belief_state")

        # 3. Temporal drift penalty (10%)
        time_gap = abs(ssv_a.timestamp - ssv_b.timestamp)
        if time_gap > 300:
            divergence_score += 0.1
            mismatch_fields.append("temporal_drift")

        # 4. Decision history mismatch (10%)
        history_match = len(
            set(ssv_a.decision_history) & set(ssv_b.decision_history)
        ) / max(len(ssv_a.decision_history) or 1, len(ssv_b.decision_history) or 1)
        divergence_score += (1 - history_match) * 0.1

        # 5. Determine level
        if divergence_score < DynamicConsensusProtocol.WARNING_DRIFT_THRESHOLD:
            level  = ConsensusLevel.GREEN
            action = "PROCEED: Agents aligned"
        elif divergence_score < DynamicConsensusProtocol.CRITICAL_DRIFT_THRESHOLD:
            level  = ConsensusLevel.YELLOW
            action = "PROCEED_WITH_CAUTION: Log divergence and monitor"
        else:
            level  = ConsensusLevel.RED
            action = (
                "BLOCK_AND_VERIFY: Critical divergence detected. "
                "Invoke EvidenceVerifier before synchronising."
            )

        # 6. Generate sync context (NOT a resolution — Problem 11)
        sync_payload = None
        if level != ConsensusLevel.GREEN:
            sync_payload = DynamicConsensusProtocol._generate_divergence_context(ssv_a, ssv_b)

        return ConsensusResult(
            level             = level,
            divergence_score  = divergence_score,
            mismatch_fields   = mismatch_fields,
            recommended_action= action,
            sync_payload      = sync_payload,
        )

    @staticmethod
    def _vector_difference(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
        all_keys = set(vec_a.keys()) | set(vec_b.keys())
        if not all_keys:
            return 0.0
        total_diff = sum(abs(vec_a.get(k, 0.0) - vec_b.get(k, 0.0)) for k in all_keys)
        return min(total_diff / len(all_keys), 1.0)

    @staticmethod
    def _state_difference(state_a: Dict, state_b: Dict) -> float:
        if set(state_a.keys()) != set(state_b.keys()):
            return 0.5
        mismatches = sum(1 for k in state_a if state_a[k] != state_b[k])
        return mismatches / max(len(state_a), 1)

    @staticmethod
    def _generate_divergence_context(
        ssv_a: SemanticStateVector,
        ssv_b: SemanticStateVector,
    ) -> Dict:
        """
        Generate context payload describing the divergence.
        (Problem 11: no longer called 'merge_strategy: take_most_recent'
        and no longer merges dicts — it describes the conflict)
        """
        conflicting_fields = {}
        for key in ssv_a.belief_state:
            if key in ssv_b.belief_state and ssv_a.belief_state[key] != ssv_b.belief_state[key]:
                conflicting_fields[key] = {
                    "agent_a_value":     ssv_a.belief_state[key],
                    "agent_b_value":     ssv_b.belief_state[key],
                    "agent_a_evidence":  ssv_a.field_evidence.get(key),
                    "agent_b_evidence":  ssv_b.field_evidence.get(key),
                }

        return {
            "description":        "Divergence context for EvidenceVerifier",
            "agent_a_id":         ssv_a.agent_id,
            "agent_b_id":         ssv_b.agent_id,
            "conflicting_fields": conflicting_fields,
            "agent_a_timestamp":  ssv_a.timestamp,
            "agent_b_timestamp":  ssv_b.timestamp,
            "note": (
                "This payload describes the conflict. "
                "Do not merge values until EvidenceVerifier returns RESOLVED_A or RESOLVED_B."
            ),
        }


# ============================================================================
# ASYNC STATE JOURNAL
# ============================================================================

@dataclass
class JournalEntry:
    """
    Single immutable audit record.
    (Problem 7: extended to record full conflict lifecycle)
    """
    timestamp:       float
    agent_id:        str
    action:          str
    state_delta:     Dict[str, Any]
    previous_hash:   str
    new_hash:        str
    sequence_number: int

    # NEW — conflict lifecycle fields (Problem 7)
    original_claim:      Optional[Any]              = None
    conflicting_claim:   Optional[Any]              = None
    evidence:            Optional[Dict[str, Any]]   = None
    verifier_result:     Optional[str]              = None   # RESOLVED_A / RESOLVED_B / UNRESOLVED
    resolution_reason:   Optional[str]              = None
    sync_result:         Optional[str]              = None   # synced | blocked | skipped


class AsyncStateJournal:
    """
    Immutable append-only log of all agent state changes.
    Answers: "Why did this agent change its answer?"

    (Problem 7: now records original_claim, evidence, verifier_result,
     resolution_reason, sync_result for every conflict event)
    """

    def __init__(self):
        self.entries: List[JournalEntry] = []
        self.sequence_counter = 0

        # NEW — conflict resolution counters (Problem 8)
        self._conflicts_detected  = 0
        self._conflicts_resolved  = 0
        self._conflicts_blocked   = 0   # UNRESOLVED — sync blocked

    def log_state_change(
        self,
        agent_id:          str,
        action:            str,
        state_delta:       Dict[str, Any],
        previous_hash:     str,
        new_hash:          str,
        original_claim:    Optional[Any]            = None,
        conflicting_claim: Optional[Any]            = None,
        evidence:          Optional[Dict[str, Any]] = None,
        verifier_result:   Optional[str]            = None,
        resolution_reason: Optional[str]            = None,
        sync_result:       Optional[str]            = None,
    ) -> JournalEntry:

        entry = JournalEntry(
            timestamp        = time.time(),
            agent_id         = agent_id,
            action           = action,
            state_delta      = state_delta,
            previous_hash    = previous_hash,
            new_hash         = new_hash,
            sequence_number  = self.sequence_counter,
            original_claim   = original_claim,
            conflicting_claim= conflicting_claim,
            evidence         = evidence,
            verifier_result  = verifier_result,
            resolution_reason= resolution_reason,
            sync_result      = sync_result,
        )

        self.entries.append(entry)
        self.sequence_counter += 1

        # Track conflict counters
        if action in ("conflict_detected", "consensus_check") and state_delta.get("level") == "critical":
            self._conflicts_detected += 1
        if verifier_result == VerificationStatus.RESOLVED_A.value or verifier_result == VerificationStatus.RESOLVED_B.value:
            self._conflicts_resolved += 1
        if verifier_result == VerificationStatus.UNRESOLVED.value:
            self._conflicts_blocked += 1

        return entry

    @property
    def conflict_resolution_rate(self) -> str:
        """
        Honest metric (Problem 8):
        Conflict Resolution Rate = resolved / detected
        Only counts cases where EvidenceVerifier actually ran.
        """
        if self._conflicts_detected == 0:
            return "N/A"
        rate = (self._conflicts_resolved / self._conflicts_detected) * 100
        return f"{rate:.1f}%"

    @property
    def conflicts_detected(self) -> int:
        return self._conflicts_detected

    @property
    def conflicts_resolved(self) -> int:
        return self._conflicts_resolved

    @property
    def conflicts_blocked(self) -> int:
        return self._conflicts_blocked

    def get_agent_history(self, agent_id: str) -> List[JournalEntry]:
        return [e for e in self.entries if e.agent_id == agent_id]

    def get_divergence_point(self, agent_a_id: str, agent_b_id: str) -> Optional[int]:
        history_a = self.get_agent_history(agent_a_id)
        history_b = self.get_agent_history(agent_b_id)
        for i, (e_a, e_b) in enumerate(zip(history_a, history_b)):
            if e_a.new_hash != e_b.new_hash:
                return i
        return None

    def export_json(self) -> str:
        return json.dumps(
            [asdict(e) for e in self.entries],
            default=str,
            indent=2,
        )


# ============================================================================
# EXPLAINABLE SYNC PAYLOAD (Problem 6)
# ============================================================================

def build_explainable_sync(
    previous_value: Any,
    corrected_value: Any,
    reason: str,
    supporting_evidence: List[Dict[str, Any]],
    verification_status: str,
    confidence: float,
    agent_id: str,
) -> Dict[str, Any]:
    """
    Build a sync payload that explains WHY an agent's value changed.
    (Problem 6: sync must explain the correction, not just overwrite)
    """
    return {
        "agent_id":            agent_id,
        "previous_value":      previous_value,
        "corrected_value":     corrected_value,
        "reason":              reason,
        "supporting_evidence": supporting_evidence,
        "verification_status": verification_status,
        "confidence":          confidence,
        "timestamp":           time.time(),
        "note": (
            "This agent's state was updated based on evidence comparison. "
            "See reason and supporting_evidence for full explanation."
        ),
    }


# ============================================================================
# INTEGRATION EXAMPLE
# ============================================================================

async def example_research_workflow():
    """Demonstrates ContextFlow drift detection and evidence-based resolution."""

    print("=" * 70)
    print("CONTEXTFLOW: Agent State Fingerprint Demo")
    print("=" * 70)

    journal = AsyncStateJournal()

    # Scout state — stale cache source
    scout_evidence = {
        "top_paper_citations": {
            "claim_value":       145,
            "source":            "academic_db_cache",
            "source_type":       "cache",
            "source_timestamp":  datetime(2025, 10, 1).timestamp(),
            "confidence":        0.85,
        }
    }
    scout_ssv = SSVGenerator.generate_ssv(
        agent_id="scout",
        current_task="Find research papers",
        observations={"top_paper_citations": 145, "papers_found": 3},
        decisions_made=["searched_arxiv", "filtered_by_date"],
        constraints={"date_filter": "2025-2026"},
        confidence=0.85,
        field_evidence=scout_evidence,
    )
    print(f"Scout state fingerprint:  {scout_ssv.state_hash[:12]}...")

    # Critic state — newer live API source
    critic_evidence = {
        "top_paper_citations": {
            "claim_value":       156,
            "source":            "semantic_scholar_live_api",
            "source_type":       "live_api",
            "source_timestamp":  datetime(2026, 8, 1).timestamp(),
            "confidence":        0.92,
        }
    }
    critic_ssv = SSVGenerator.generate_ssv(
        agent_id="critic",
        current_task="Evaluate methodology",
        observations={"top_paper_citations": 156, "papers_found": 3},
        decisions_made=["checked_methodology"],
        constraints={"rigor_threshold": 0.6},
        confidence=0.75,
        field_evidence=critic_evidence,
    )
    print(f"Critic state fingerprint: {critic_ssv.state_hash[:12]}...")

    # DCP — detects divergence only
    result = DynamicConsensusProtocol.compare_states(scout_ssv, critic_ssv)
    print(f"\nDCP result: {result.level.value} | divergence={result.divergence_score:.4f}")
    print(f"Action: {result.recommended_action}")

    # Journal records conflict
    journal.log_state_change(
        agent_id="contextflow",
        action="conflict_detected",
        state_delta={"level": result.level.value, "divergence": result.divergence_score},
        previous_hash=scout_ssv.state_hash,
        new_hash=critic_ssv.state_hash,
        original_claim=145,
        conflicting_claim=156,
    )

    print(f"\nJournal entries: {len(journal.entries)}")
    print(f"Conflict resolution rate: {journal.conflict_resolution_rate}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(example_research_workflow())
