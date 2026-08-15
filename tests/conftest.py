"""
Pytest configuration and fixtures for ContextFlow tests
"""

import pytest
import asyncio
from ssv_core import SSVGenerator, DynamicConsensusProtocol, AsyncStateJournal, SemanticStateVector


@pytest.fixture
def sample_observations():
    """Sample observations for testing"""
    return {
        "papers_found": 3,
        "paper_1": {"title": "Test Paper", "citations": 100},
        "timestamp_fetched": 1234567890.0
    }


@pytest.fixture
def sample_constraints():
    """Sample constraints for testing"""
    return {
        "max_papers": 10,
        "date_filter": "2025-2026"
    }


@pytest.fixture
def sample_decisions():
    """Sample decisions for testing"""
    return ["searched", "filtered", "ranked"]


@pytest.fixture
def journal():
    """Fresh AsyncStateJournal instance"""
    return AsyncStateJournal()


@pytest.fixture
def scout_ssv(sample_observations, sample_constraints, sample_decisions):
    """Sample SSV for scout agent"""
    return SSVGenerator.generate_ssv(
        agent_id="scout",
        current_task="Find research papers",
        observations=sample_observations,
        decisions_made=sample_decisions,
        constraints=sample_constraints,
        confidence=0.9
    )


@pytest.fixture
def critic_ssv(sample_observations, sample_constraints, sample_decisions):
    """Sample SSV for critic agent with slight divergence"""
    divergent_observations = sample_observations.copy()
    divergent_observations["paper_1"] = {"title": "Test Paper", "citations": 105}  # Different
    
    return SSVGenerator.generate_ssv(
        agent_id="critic",
        current_task="Evaluate methodology",
        observations=divergent_observations,
        decisions_made=sample_decisions,
        constraints=sample_constraints,
        confidence=0.85
    )
