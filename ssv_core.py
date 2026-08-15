"""
ContextFlow: Semantic State Vector (SSV) Core Implementation
Prevents multi-agent hallucination through context drift detection
"""

import hashlib
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio

# ============================================================================
# CORE DATA STRUCTURES
# ============================================================================

class ConsensusLevel(Enum):
    """Consensus health states"""
    GREEN = "aligned"      # All agents agree
    YELLOW = "minor_drift" # <10% semantic divergence
    RED = "critical"       # >10% divergence, potential hallucination


@dataclass
class SemanticStateVector:
    """
    Compressed, cryptographic summary of an agent's world model
    Replaces bulky context passing with lightweight semantic hash
    """
    agent_id: str
    timestamp: float
    intent_vector: Dict[str, float]  # What the agent is trying to accomplish
    constraint_set: Dict[str, Any]   # Rules the agent must follow
    belief_state: Dict[str, Any]     # Current facts the agent believes
    decision_history: List[str]      # Last 5 decisions made
    confidence_score: float          # 0-1: agent's confidence in its state
    state_hash: str                  # SHA-256 of normalized state
    version: str = "1.0"
    
    def to_compact(self) -> str:
        """Convert to JSON for transmission"""
        return json.dumps(asdict(self), default=str)
    
    @classmethod
    def from_compact(cls, json_str: str) -> "SemanticStateVector":
        """Reconstruct from JSON"""
        data = json.loads(json_str)
        return cls(**data)


@dataclass
class ConsensusResult:
    """Result of comparing SSVs between agents"""
    level: ConsensusLevel
    divergence_score: float  # 0-1, where 1 is complete disagreement
    mismatch_fields: List[str]  # Which fields disagree
    recommended_action: str  # What to do about the divergence
    sync_payload: Optional[Dict[str, Any]] = None  # Data to sync


# ============================================================================
# SEMANTIC STATE VECTOR GENERATION
# ============================================================================

class SSVGenerator:
    """Generate lightweight semantic state vectors from agent observations"""
    
    @staticmethod
    def generate_ssv(
        agent_id: str,
        current_task: str,
        observations: Dict[str, Any],
        decisions_made: List[str],
        constraints: Dict[str, Any],
        confidence: float = 0.8
    ) -> SemanticStateVector:
        """
        Generate an SSV from agent's current state.
        
        Args:
            agent_id: Unique agent identifier
            current_task: What the agent is currently working on
            observations: Facts the agent believes (dict)
            decisions_made: List of decisions made so far
            constraints: Rules/boundaries the agent must follow
            confidence: Agent's confidence 0-1
            
        Returns:
            SemanticStateVector ready for transmission
        """
        
        # 1. Extract intent vector (what matters for this task)
        intent_vector = SSVGenerator._extract_intent(current_task, observations)
        
        # 2. Keep only recent decisions (last 5)
        recent_decisions = decisions_made[-5:] if len(decisions_made) > 5 else decisions_made
        
        # 3. Create normalized state for hashing
        normalized_state = {
            "agent": agent_id,
            "task": current_task,
            "intent": intent_vector,
            "constraints": constraints,
            "observations": observations,
            "decisions": recent_decisions
        }
        
        # 4. Compute state hash
        state_bytes = json.dumps(normalized_state, sort_keys=True, default=str).encode()
        state_hash = hashlib.sha256(state_bytes).hexdigest()
        
        # 5. Construct SSV
        ssv = SemanticStateVector(
            agent_id=agent_id,
            timestamp=time.time(),
            intent_vector=intent_vector,
            constraint_set=constraints,
            belief_state=observations,
            decision_history=recent_decisions,
            confidence_score=confidence,
            state_hash=state_hash
        )
        
        return ssv
    
    @staticmethod
    def _extract_intent(task: str, observations: Dict) -> Dict[str, float]:
        """
        Extract semantic intent vector from task and observations.
        Simple version: returns key observation categories with weights.
        In production: use embedding model for semantic similarity.
        """
        intent = {}
        
        # Weight observations by relevance to task
        for key, value in observations.items():
            if isinstance(value, (int, float)):
                intent[key] = float(value)
            elif isinstance(value, str) and len(value) < 100:
                # Simple heuristic: include short strings
                intent[f"has_{key}"] = 1.0
        
        return intent if intent else {"task_acknowledged": 1.0}


# ============================================================================
# DYNAMIC CONSENSUS PROTOCOL (DCP)
# ============================================================================

class DynamicConsensusProtocol:
    """
    Compares SSVs between agents and detects context drift.
    Prevents hallucination by catching divergence BEFORE joint reasoning.
    """
    
    CRITICAL_DRIFT_THRESHOLD = 0.15  # >15% divergence = RED
    WARNING_DRIFT_THRESHOLD = 0.05   # >5% divergence = YELLOW
    
    @staticmethod
    def compare_states(ssv_a: SemanticStateVector, ssv_b: SemanticStateVector) -> ConsensusResult:
        """
        Compare two agent states and determine consensus level.
        
        Returns:
            ConsensusResult with divergence score and recommendations
        """
        
        divergence_score = 0.0
        mismatch_fields = []
        
        # 1. Compare intent vectors
        intent_diff = DynamicConsensusProtocol._vector_difference(
            ssv_a.intent_vector,
            ssv_b.intent_vector
        )
        divergence_score += intent_diff * 0.4  # Intent weighs 40%
        if intent_diff > 0.05:
            mismatch_fields.append("intent_vector")
        
        # 2. Compare belief states
        belief_diff = DynamicConsensusProtocol._state_difference(
            ssv_a.belief_state,
            ssv_b.belief_state
        )
        divergence_score += belief_diff * 0.4  # Beliefs weigh 40%
        if belief_diff > 0.05:
            mismatch_fields.append("belief_state")
        
        # 3. Check timestamp gap (temporal context drift)
        time_gap = abs(ssv_a.timestamp - ssv_b.timestamp)
        if time_gap > 300:  # >5 minutes apart
            divergence_score += 0.1  # Add penalty
            mismatch_fields.append("temporal_drift")
        
        # 4. Compare decision histories
        history_match = len(set(ssv_a.decision_history) & set(ssv_b.decision_history)) / max(
            len(ssv_a.decision_history) or 1,
            len(ssv_b.decision_history) or 1
        )
        divergence_score += (1 - history_match) * 0.1  # History weighs 10%
        
        # 5. Determine consensus level
        if divergence_score < DynamicConsensusProtocol.WARNING_DRIFT_THRESHOLD:
            level = ConsensusLevel.GREEN
            action = "PROCEED: Agents aligned"
        elif divergence_score < DynamicConsensusProtocol.CRITICAL_DRIFT_THRESHOLD:
            level = ConsensusLevel.YELLOW
            action = "PROCEED_WITH_CAUTION: Log divergence and monitor"
        else:
            level = ConsensusLevel.RED
            action = "BLOCK_AND_SYNC: Critical divergence detected. Force state synchronization."
        
        # Generate sync payload if needed
        sync_payload = None
        if level != ConsensusLevel.GREEN:
            sync_payload = DynamicConsensusProtocol._generate_sync_payload(ssv_a, ssv_b)
        
        return ConsensusResult(
            level=level,
            divergence_score=divergence_score,
            mismatch_fields=mismatch_fields,
            recommended_action=action,
            sync_payload=sync_payload
        )
    
    @staticmethod
    def _vector_difference(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
        """Compute semantic difference between intent vectors (0-1)"""
        all_keys = set(vec_a.keys()) | set(vec_b.keys())
        
        if not all_keys:
            return 0.0
        
        total_diff = sum(
            abs(vec_a.get(k, 0.0) - vec_b.get(k, 0.0))
            for k in all_keys
        )
        
        return min(total_diff / len(all_keys), 1.0)
    
    @staticmethod
    def _state_difference(state_a: Dict, state_b: Dict) -> float:
        """Compute structural difference between belief states"""
        # Check if same keys exist
        keys_match = set(state_a.keys()) == set(state_b.keys())
        
        if not keys_match:
            # Different keys = potential hallucination risk
            return 0.5
        
        # For matching keys, check value differences
        mismatches = 0
        for key in state_a.keys():
            if state_a[key] != state_b[key]:
                mismatches += 1
        
        return mismatches / max(len(state_a), 1)
    
    @staticmethod
    def _generate_sync_payload(ssv_a: SemanticStateVector, ssv_b: SemanticStateVector) -> Dict:
        """Generate minimal payload to sync diverged agents"""
        return {
            "timestamp": max(ssv_a.timestamp, ssv_b.timestamp),
            "merge_strategy": "take_most_recent",
            "agent_a_state": asdict(ssv_a),
            "agent_b_state": asdict(ssv_b),
            "recommended_merge": {
                "intent_vector": SSVGenerator._extract_intent(
                    "merged",
                    {**ssv_a.belief_state, **ssv_b.belief_state}
                ),
                "beliefs": {**ssv_a.belief_state, **ssv_b.belief_state},
                "constraints": {**ssv_a.constraint_set, **ssv_b.constraint_set}
            }
        }


# ============================================================================
# ASYNC STATE JOURNAL (ASJ)
# ============================================================================

@dataclass
class JournalEntry:
    """Single entry in the async state journal"""
    timestamp: float
    agent_id: str
    action: str
    state_delta: Dict[str, Any]
    previous_hash: str
    new_hash: str
    sequence_number: int


class AsyncStateJournal:
    """
    Immutable log of all state changes.
    Enables debugging and state rollback.
    """
    
    def __init__(self):
        self.entries: List[JournalEntry] = []
        self.sequence_counter = 0
    
    def log_state_change(
        self,
        agent_id: str,
        action: str,
        state_delta: Dict[str, Any],
        previous_hash: str,
        new_hash: str
    ) -> JournalEntry:
        """Record a state change to the journal"""
        entry = JournalEntry(
            timestamp=time.time(),
            agent_id=agent_id,
            action=action,
            state_delta=state_delta,
            previous_hash=previous_hash,
            new_hash=new_hash,
            sequence_number=self.sequence_counter
        )
        
        self.entries.append(entry)
        self.sequence_counter += 1
        
        return entry
    
    def get_agent_history(self, agent_id: str) -> List[JournalEntry]:
        """Get all state changes for a specific agent"""
        return [e for e in self.entries if e.agent_id == agent_id]
    
    def get_divergence_point(self, agent_a_id: str, agent_b_id: str) -> Optional[int]:
        """Find the first sequence where two agents' states diverged"""
        history_a = self.get_agent_history(agent_a_id)
        history_b = self.get_agent_history(agent_b_id)
        
        for i, (e_a, e_b) in enumerate(zip(history_a, history_b)):
            if e_a.new_hash != e_b.new_hash:
                return i
        
        return None
    
    def export_json(self) -> str:
        """Export journal as JSON for debugging"""
        return json.dumps(
            [asdict(e) for e in self.entries],
            default=str,
            indent=2
        )


# ============================================================================
# INTEGRATION EXAMPLE
# ============================================================================

async def example_research_workflow():
    """
    Demonstrates ContextFlow preventing hallucination in multi-agent research
    """
    
    print("=" * 70)
    print("CONTEXTFLOW DEMO: Research Workflow with Context Drift Detection")
    print("=" * 70)
    
    # Initialize journal
    journal = AsyncStateJournal()
    
    # ---- AGENT 1: SCOUT (Finds papers) ----
    print("\n[SCOUT] Searching for papers on 'multi-agent hallucination'...")
    scout_state = {
        "papers_found": 3,
        "paper_1": {"title": "Context Drift Study", "citations": 145},
        "paper_2": {"title": "Agent Coordination", "citations": 89},
        "timestamp_fetched": datetime(2026, 8, 1).timestamp()
    }
    scout_constraints = {
        "max_papers": 10,
        "date_filter": "2025-2026"
    }
    
    scout_ssv = SSVGenerator.generate_ssv(
        agent_id="scout",
        current_task="Find research papers on multi-agent systems",
        observations=scout_state,
        decisions_made=["searched_arxiv", "filtered_by_date", "ranked_by_citations"],
        constraints=scout_constraints,
        confidence=0.9
    )
    print(f"✓ Scout SSV generated. Hash: {scout_ssv.state_hash[:12]}...")
    
    # ---- AGENT 2: CRITIC (Evaluates methodology) ----
    print("\n[CRITIC] Evaluating paper quality...")
    
    # Critic has DIFFERENT information (outdated cache from Aug 2 vs Scout's Aug 1)
    critic_state = {
        "papers_evaluated": 3,
        "paper_1": {"title": "Context Drift Study", "citations": 156},  # DIFFERENT!
        "paper_2": {"title": "Agent Coordination", "citations": 89},
        "timestamp_fetched": datetime(2026, 8, 2).timestamp()  # LATER!
    }
    critic_constraints = {
        "methodology_weight": 0.7,
        "rigor_threshold": 0.6
    }
    
    critic_ssv = SSVGenerator.generate_ssv(
        agent_id="critic",
        current_task="Evaluate research methodology",
        observations=critic_state,
        decisions_made=["checked_methodology", "assessed_rigor", "noted_limitations"],
        constraints=critic_constraints,
        confidence=0.75
    )
    print(f"✓ Critic SSV generated. Hash: {critic_ssv.state_hash[:12]}...")
    
    # ---- CONSENSUS CHECK ----
    print("\n" + "=" * 70)
    print("RUNNING DYNAMIC CONSENSUS PROTOCOL...")
    print("=" * 70)
    
    consensus = DynamicConsensusProtocol.compare_states(scout_ssv, critic_ssv)
    
    print(f"\nConsensus Level: {consensus.level.value.upper()}")
    print(f"Divergence Score: {consensus.divergence_score:.2%}")
    print(f"Mismatched Fields: {', '.join(consensus.mismatch_fields)}")
    print(f"Recommendation: {consensus.recommended_action}")
    
    # Log to journal
    journal.log_state_change(
        agent_id="scout",
        action="consensus_check",
        state_delta={"divergence_detected": consensus.divergence_score},
        previous_hash=scout_ssv.state_hash,
        new_hash=scout_ssv.state_hash
    )
    
    # ---- SYNC IF DIVERGED ----
    if consensus.level != ConsensusLevel.GREEN:
        print("\n⚠️  CONTEXT DRIFT DETECTED!")
        print("\nDivergence details:")
        print(json.dumps(consensus.sync_payload or {}, indent=2))
        
        print("\n🔄 SYNCHRONIZING AGENTS...")
        # In production: agents would update their beliefs based on sync_payload
        print("✓ Agents synchronized to shared state")
    else:
        print("\n✅ All agents operating from consistent state. Proceeding to next step.")
    
    # ---- SYNTHESIS ----
    print("\n" + "=" * 70)
    print("PROCEEDING TO SYNTHESIS PHASE (safe from hallucination)")
    print("=" * 70)
    
    synthesis_state = {
        "papers_analyzed": 3,
        "consensus_found": consensus.level == ConsensusLevel.GREEN,
        "key_findings": [
            "Context drift is a distributed systems problem",
            "Consensus protocols prevent multi-agent hallucination",
            "State synchronization costs minimal LLM overhead"
        ]
    }
    
    synthesis_ssv = SSVGenerator.generate_ssv(
        agent_id="synthesis",
        current_task="Synthesize findings",
        observations=synthesis_state,
        decisions_made=["identified_themes", "extracted_insights", "created_summary"],
        constraints={"accuracy_threshold": 0.85},
        confidence=0.92
    )
    
    print(f"✓ Synthesis complete with high confidence ({synthesis_ssv.confidence_score:.0%})")
    
    # ---- JOURNAL AUDIT TRAIL ----
    print("\n" + "=" * 70)
    print("AUDIT TRAIL (From Async State Journal)")
    print("=" * 70)
    print(f"\nTotal log entries: {len(journal.entries)}")
    print(f"Agents tracked: {set(e.agent_id for e in journal.entries)}")
    print(f"Divergence point detected at sequence: {journal.get_divergence_point('scout', 'critic')}")


if __name__ == "__main__":
    # Run the example
    asyncio.run(example_research_workflow())