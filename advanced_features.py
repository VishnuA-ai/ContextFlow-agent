"""
Advanced Features for ContextFlow - Unique Differentiators
These features make ContextFlow stand out from other consensus systems
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from datetime import datetime


class ConsensusStrategy(Enum):
    """Different strategies for reaching consensus"""
    WEIGHTED_AVERAGE = "weighted_average"
    MAJORITY_VOTE = "majority_vote"
    EXPERT_WEIGHTED = "expert_weighted"
    CONFIDENCE_BASED = "confidence_based"


@dataclass
class AgentReputation:
    """Track agent reliability over time"""
    agent_id: str
    total_decisions: int = 0
    correct_decisions: int = 0
    confidence_score: float = 0.5
    specialization_areas: List[str] = None
    
    def __post_init__(self):
        if self.specialization_areas is None:
            self.specialization_areas = []
    
    @property
    def reliability_score(self) -> float:
        """Calculate overall reliability score"""
        if self.total_decisions == 0:
            return 0.5
        return self.correct_decisions / self.total_decisions
    
    def update(self, was_correct: bool):
        """Update reputation based on decision outcome"""
        self.total_decisions += 1
        if was_correct:
            self.correct_decisions += 1
            self.confidence_score = min(0.95, self.confidence_score + 0.05)
        else:
            self.confidence_score = max(0.05, self.confidence_score - 0.1)


class AdaptiveConsensusEngine:
    """
    Adaptive consensus engine that learns from past decisions
    This is a unique feature not found in standard consensus systems
    """
    
    def __init__(self):
        self.agent_reputations: Dict[str, AgentReputation] = {}
        self.consensus_history: List[Dict] = []
        self.learning_rate = 0.1
    
    def register_agent(self, agent_id: str, specializations: List[str] = None):
        """Register an agent with the system"""
        self.agent_reputations[agent_id] = AgentReputation(
            agent_id=agent_id,
            specialization_areas=specializations or []
        )
    
    def calculate_weighted_consensus(
        self, 
        agent_states: Dict[str, Dict],
        strategy: ConsensusStrategy = ConsensusStrategy.WEIGHTED_AVERAGE
    ) -> Dict:
        """
        Calculate consensus using adaptive weights based on agent reputation
        This is a unique adaptive algorithm
        """
        if not agent_states:
            return {}
        
        # Get weights based on strategy
        weights = self._get_weights(agent_states.keys(), strategy)
        
        # Calculate weighted consensus
        consensus_result = {}
        
        # For numeric values, use weighted average
        for key in agent_states.values().__iter__().__next__().keys():
            if isinstance(list(agent_states.values())[0][key], (int, float)):
                weighted_sum = 0
                total_weight = 0
                for agent_id, state in agent_states.items():
                    if key in state and isinstance(state[key], (int, float)):
                        weight = weights.get(agent_id, 1.0)
                        weighted_sum += state[key] * weight
                        total_weight += weight
                
                if total_weight > 0:
                    consensus_result[key] = weighted_sum / total_weight
        
        return consensus_result
    
    def _get_weights(self, agent_ids: List[str], strategy: ConsensusStrategy) -> Dict[str, float]:
        """Calculate weights for each agent based on strategy"""
        weights = {}
        
        for agent_id in agent_ids:
            reputation = self.agent_reputations.get(agent_id)
            
            if strategy == ConsensusStrategy.WEIGHTED_AVERAGE:
                weights[agent_id] = 1.0  # Equal weights
            elif strategy == ConsensusStrategy.MAJORITY_VOTE:
                weights[agent_id] = 1.0  # Equal for voting
            elif strategy == ConsensusStrategy.EXPERT_WEIGHTED:
                if reputation:
                    # Weight by specialization count
                    weights[agent_id] = 1.0 + len(reputation.specialization_areas) * 0.2
                else:
                    weights[agent_id] = 1.0
            elif strategy == ConsensusStrategy.CONFIDENCE_BASED:
                if reputation:
                    weights[agent_id] = reputation.reliability_score
                else:
                    weights[agent_id] = 0.5
        
        return weights
    
    def record_outcome(self, agent_id: str, was_correct: bool):
        """Record decision outcome for learning"""
        if agent_id in self.agent_reputations:
            self.agent_reputations[agent_id].update(was_correct)
    
    def get_agent_stats(self, agent_id: str) -> Optional[Dict]:
        """Get statistics for an agent"""
        if agent_id not in self.agent_reputations:
            return None
        
        rep = self.agent_reputations[agent_id]
        return {
            "agent_id": agent_id,
            "reliability_score": rep.reliability_score,
            "total_decisions": rep.total_decisions,
            "correct_decisions": rep.correct_decisions,
            "specializations": rep.specialization_areas
        }


class PredictiveDivergenceDetector:
    """
    Predictive divergence detection - anticipates conflicts before they happen
    This is a unique proactive feature
    """
    
    def __init__(self):
        self.divergence_patterns: Dict[str, List] = {}
        self.threshold = 0.7
    
    def analyze_divergence_risk(self, agent_states: Dict[str, Dict]) -> Dict[str, float]:
        """
        Analyze risk of future divergence based on current state patterns
        Returns risk scores for each agent pair
        """
        risk_scores = {}
        agent_ids = list(agent_states.keys())
        
        for i, agent_a in enumerate(agent_ids):
            for agent_b in agent_ids[i+1:]:
                risk = self._calculate_pairwise_risk(
                    agent_states[agent_a], 
                    agent_states[agent_b]
                )
                risk_scores[f"{agent_a}_{agent_b}"] = risk
        
        return risk_scores
    
    def _calculate_pairwise_risk(self, state_a: Dict, state_b: Dict) -> float:
        """Calculate divergence risk between two agent states"""
        if not state_a or not state_b:
            return 0.0
        
        # Compare numeric values
        numeric_keys = set()
        for key in state_a:
            if isinstance(state_a[key], (int, float)):
                numeric_keys.add(key)
        
        if not numeric_keys:
            return 0.0
        
        divergences = []
        for key in numeric_keys:
            if key in state_b and isinstance(state_b[key], (int, float)):
                val_a = state_a[key]
                val_b = state_b[key]
                if val_a != 0 and val_b != 0:
                    divergence = abs(val_a - val_b) / max(abs(val_a), abs(val_b))
                    divergences.append(divergence)
        
        if not divergences:
            return 0.0
        
        return sum(divergences) / len(divergences)
    
    def predict_conflict(self, risk_scores: Dict[str, float]) -> List[str]:
        """Predict which agent pairs are likely to conflict"""
        conflicts = []
        for pair, risk in risk_scores.items():
            if risk > self.threshold:
                conflicts.append(pair)
        return conflicts


class ContextFlowOptimizer:
    """
    Optimizes consensus process for efficiency and accuracy
    Unique optimization algorithms for multi-agent systems
    """
    
    def __init__(self):
        self.performance_metrics: Dict[str, List[float]] = {}
    
    def optimize_agent_selection(
        self, 
        available_agents: List[str],
        task_type: str,
        required_specializations: List[str]
    ) -> List[str]:
        """
        Select optimal agents for a given task based on specializations
        """
        # This would integrate with the reputation system
        # For now, return all available agents
        return available_agents
    
    def calculate_consensus_efficiency(
        self, 
        agent_count: int,
        divergence_level: float
    ) -> float:
        """
        Calculate expected efficiency of consensus process
        """
        base_efficiency = 1.0
        agent_penalty = agent_count * 0.05  # More agents = slower
        divergence_penalty = divergence_level * 0.3  # Higher divergence = harder
        
        efficiency = base_efficiency - agent_penalty - divergence_penalty
        return max(0.1, efficiency)  # Minimum 10% efficiency
