"""
ContextFlow: Multi-Agent AI Consensus Engine
Prevents hallucination through consensus-based context drift detection
"""

from contextflow.contextflow_langgraph import ContextFlowAgent
from ssv_core import (
    SemanticStateVector,
    DynamicConsensusProtocol,
    ConsensusLevel,
    AsyncStateJournal,
    SSVGenerator,
    ConsensusResult
)

__version__ = "1.0.0"
__all__ = [
    "ContextFlowAgent",
    "SemanticStateVector",
    "DynamicConsensusProtocol",
    "ConsensusLevel",
    "AsyncStateJournal",
    "SSVGenerator",
    "ConsensusResult"
]
