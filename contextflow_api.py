"""
ContextFlow FastAPI Integration
REST API for managing multi-agent consensus and state synchronization
Ready for deployment on free tier (Render, Railway, or local)
"""

from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import json
import asyncio
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from ssv_core import (
    SemanticStateVector, 
    DynamicConsensusProtocol,
    ConsensusLevel,
    AsyncStateJournal,
    SSVGenerator
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# LIFESPAN MANAGEMENT
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("ContextFlow API started")
    print("Consensus engine ready")
    yield
    # Shutdown
    print("ContextFlow API shutting down")
    print(f"Final journal entries: {len(journal.entries)}")

# Initialize FastAPI app
app = FastAPI(
    title="ContextFlow",
    description="Multi-agent consensus engine preventing hallucination through context drift detection",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:5173", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state (in production: use Redis)
consensus_cache: Dict[str, SemanticStateVector] = {}
journal = AsyncStateJournal()
active_connections: List[WebSocket] = []


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class SSVRequest(BaseModel):
    """Request to generate a Semantic State Vector"""
    agent_id: str
    current_task: str
    observations: Dict
    decisions_made: List[str]
    constraints: Dict
    confidence: float = 0.8


class ConsensusCheckRequest(BaseModel):
    """Request to check consensus between two agents"""
    agent_a_id: str
    agent_b_id: str


class StateUpdateRequest(BaseModel):
    """Request to update an agent's state"""
    agent_id: str
    action: str
    state_delta: Dict


class SyncRequest(BaseModel):
    """Request to synchronize diverged agents"""
    agent_a_id: str
    agent_b_id: str
    merge_strategy: str = "take_most_recent"


# ============================================================================
# REST ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agents_tracked": len(consensus_cache),
        "journal_entries": len(journal.entries)
    }


@app.post("/ssv/generate")
async def generate_ssv(request: SSVRequest):
    """
    Generate a Semantic State Vector for an agent.
    
    This replaces bulky context passing with lightweight semantic hash.
    """
    try:
        ssv = SSVGenerator.generate_ssv(
            agent_id=request.agent_id,
            current_task=request.current_task,
            observations=request.observations,
            decisions_made=request.decisions_made,
            constraints=request.constraints,
            confidence=request.confidence
        )
        
        # Cache the SSV
        consensus_cache[request.agent_id] = ssv
        
        # Log to journal
        journal.log_state_change(
            agent_id=request.agent_id,
            action="ssv_generated",
            state_delta={"task": request.current_task},
            previous_hash="initial",
            new_hash=ssv.state_hash
        )
        
        return {
            "success": True,
            "agent_id": request.agent_id,
            "state_hash": ssv.state_hash,
            "confidence": ssv.confidence_score,
            "timestamp": ssv.timestamp,
            "ssv_compact": ssv.to_compact()
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/consensus/check")
async def check_consensus(request: ConsensusCheckRequest):
    """
    Check consensus between two agents using Dynamic Consensus Protocol.
    
    Returns:
        - GREEN (aligned): Proceed
        - YELLOW (minor drift): Log and proceed
        - RED (critical): Stop and sync
    """
    # Retrieve SSVs from cache
    ssv_a = consensus_cache.get(request.agent_a_id)
    ssv_b = consensus_cache.get(request.agent_b_id)
    
    if not ssv_a or not ssv_b:
        raise HTTPException(
            status_code=404,
            detail=f"One or both agents not found. Have you called /ssv/generate first?"
        )
    
    # Run consensus protocol
    result = DynamicConsensusProtocol.compare_states(ssv_a, ssv_b)
    
    # Log to journal
    journal.log_state_change(
        agent_id=f"{request.agent_a_id}+{request.agent_b_id}",
        action="consensus_check",
        state_delta={"level": result.level.value},
        previous_hash=ssv_a.state_hash,
        new_hash=ssv_b.state_hash
    )
    
    return {
        "consensus_level": result.level.value,
        "divergence_score": round(result.divergence_score, 4),
        "mismatches": result.mismatch_fields,
        "recommended_action": result.recommended_action,
        "sync_payload": result.sync_payload if result.level != ConsensusLevel.GREEN else None,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/consensus/multi-agent")
async def check_multi_agent_consensus(agent_ids: List[str]):
    """
    Check consensus across multiple agents (pairwise).
    Returns consensus graph showing which pairs diverged.
    """
    results = []
    consensus_graph = {}
    
    for i, agent_a in enumerate(agent_ids):
        for agent_b in agent_ids[i+1:]:
            ssv_a = consensus_cache.get(agent_a)
            ssv_b = consensus_cache.get(agent_b)
            
            if ssv_a and ssv_b:
                consensus = DynamicConsensusProtocol.compare_states(ssv_a, ssv_b)
                results.append({
                    "pair": f"{agent_a} <-> {agent_b}",
                    "level": consensus.level.value,
                    "divergence": consensus.divergence_score
                })
                consensus_graph[f"{agent_a}<->{agent_b}"] = consensus.level.value
    
    # Determine system health
    levels = [r["level"] for r in results]
    if all(l == "aligned" for l in levels):
        system_health = "healthy"
    elif any(l == "critical" for l in levels):
        system_health = "critical"
    else:
        system_health = "degraded"
    
    return {
        "system_health": system_health,
        "consensus_graph": consensus_graph,
        "pairwise_results": results,
        "total_pairs_checked": len(results)
    }


@app.post("/state/update")
async def update_agent_state(request: StateUpdateRequest):
    """
    Update an agent's state and track the change in journal.
    """
    ssv = consensus_cache.get(request.agent_id)
    
    if not ssv:
        raise HTTPException(status_code=404, detail="Agent SSV not found")
    
    # Update belief state
    old_hash = ssv.state_hash
    ssv.belief_state.update(request.state_delta)
    
    # Recalculate hash using the full normalized state via SSVGenerator
    new_ssv = SSVGenerator.generate_ssv(
        agent_id=ssv.agent_id,
        current_task=ssv.current_task,
        observations=ssv.observations,
        decisions_made=ssv.decisions_made,
        constraints=ssv.constraints,
        confidence=ssv.confidence_score
    )
    new_hash = new_ssv.state_hash
    ssv.state_hash = new_hash
    
    # Log update
    journal.log_state_change(
        agent_id=request.agent_id,
        action=request.action,
        state_delta=request.state_delta,
        previous_hash=old_hash,
        new_hash=new_hash
    )
    
    return {
        "success": True,
        "agent_id": request.agent_id,
        "action": request.action,
        "previous_hash": old_hash,
        "new_hash": new_hash
    }


@app.get("/journal/agent/{agent_id}")
async def get_agent_history(agent_id: str):
    """
    Retrieve full state change history for an agent.
    Useful for debugging "what went wrong?"
    """
    history = journal.get_agent_history(agent_id)#used in history setting
    
    if not history:
        raise HTTPException(status_code=404, detail=f"No history for agent {agent_id}")
    
    return {
        "agent_id": agent_id,
        "entries": len(history),
        "history": [
            {
                "sequence": e.sequence_number,
                "timestamp": e.timestamp,
                "action": e.action,
                "state_delta": e.state_delta,
                "hash_change": f"{e.previous_hash[:8]}... → {e.new_hash[:8]}..."
            }
            for e in history
        ]
    }


@app.get("/journal/divergence/{agent_a}/{agent_b}")
async def find_divergence_point(agent_a: str, agent_b: str):
    """
    Find the exact point where two agents' states diverged.
    Returns the sequence number and changes that caused divergence.
    """
    divergence_seq = journal.get_divergence_point(agent_a, agent_b)
    
    if divergence_seq is None:
        return {
            "diverged": False,
            "message": "Agents never diverged or have no common history"
        }
    
    history_a = journal.get_agent_history(agent_a)
    history_b = journal.get_agent_history(agent_b)
    
    if divergence_seq >= len(history_a) or divergence_seq >= len(history_b):
        return {"error": "Divergence sequence out of range"}
    
    entry_a = history_a[divergence_seq]
    entry_b = history_b[divergence_seq]
    
    return {
        "diverged": True,
        "divergence_sequence": divergence_seq,
        "agent_a_change": {
            "action": entry_a.action,
            "delta": entry_a.state_delta,
            "timestamp": entry_a.timestamp
        },
        "agent_b_change": {
            "action": entry_b.action,
            "delta": entry_b.state_delta,
            "timestamp": entry_b.timestamp
        }
    }


@app.get("/metrics")
async def get_metrics():
    """
    Get consensus system metrics.
    """
    total_entries = len(journal.entries)
    critical_events = len([e for e in journal.entries if "critical" in str(e)])
    
    return {
        "timestamp": datetime.now().isoformat(),
        "agents_tracked": len(consensus_cache),
        "journal_entries": total_entries,
        "critical_events": critical_events,
        "active_connections": len(active_connections),
        "hallucination_prevention_rate": f"{(1 - critical_events / max(total_entries, 1)) * 100:.1f}%"
    }


@app.get("/journal/export")
async def export_journal():
    """
    Export full journal as JSON for analysis.
    """
    return JSONResponse(
        content=json.loads(journal.export_json())
    )


@app.get("/agents")
async def get_agents():
    """
    Get all currently tracked agents.
    """
    return {
        "agents": list(consensus_cache.keys()),
        "count": len(consensus_cache)
    }


@app.post("/demo/run")
async def run_demo():
    """
    Run the research workflow demo.
    Creates Scout, Critic, and Synthesis agents with realistic mock data.
    """
    # Create Scout agent
    scout_ssv = SSVGenerator.generate_ssv(
        agent_id="scout",
        current_task="Research emerging AI safety techniques",
        observations={
            "papers_reviewed": 15,
            "domains": ["RLHF", "Constitutional AI", "Debate"],
            "key_findings": ["Constitutional AI shows promise", "RLHF limitations in edge cases"]
        },
        decisions_made=["Focus on Constitutional AI", "Prioritize scalability"],
        constraints={"max_papers": 20, "time_limit": "2 hours"},
        confidence=0.85
    )
    consensus_cache["scout"] = scout_ssv
    
    # Create Critic agent with intentional drift
    critic_ssv = SSVGenerator.generate_ssv(
        agent_id="critic",
        current_task="Critique AI safety research methodology",
        observations={
            "papers_reviewed": 12,
            "domains": ["Adversarial Testing", "Red Teaming"],
            "key_findings": ["Constitutional AI has blind spots", "Need more adversarial testing"]
        },
        decisions_made=["Question Constitutional AI", "Emphasize adversarial methods"],
        constraints={"max_papers": 15, "focus": "critical_analysis"},
        confidence=0.75
    )
    consensus_cache["critic"] = critic_ssv
    
    # Create Synthesis agent
    synthesis_ssv = SSVGenerator.generate_ssv(
        agent_id="synthesis",
        current_task="Synthesize findings into recommendations",
        observations={
            "conflicts_resolved": 3,
            "consensus_level": "partial",
            "recommendations": ["Hybrid approach needed"]
        },
        decisions_made=["Combine approaches", "Prioritize safety"],
        constraints={"ensure_consensus": True},
        confidence=0.90
    )
    consensus_cache["synthesis"] = synthesis_ssv
    
    # Run consensus checks
    scout_critic = DynamicConsensusProtocol.compare_states(scout_ssv, critic_ssv)
    scout_synthesis = DynamicConsensusProtocol.compare_states(scout_ssv, synthesis_ssv)
    critic_synthesis = DynamicConsensusProtocol.compare_states(critic_ssv, synthesis_ssv)
    
    # Log to journal
    journal.log_state_change("demo", "demo_run", {"agents_created": 3}, "initial", "demo_complete")
    
    return {
        "success": True,
        "message": "Demo workflow executed successfully",
        "agents_created": ["scout", "critic", "synthesis"],
        "consensus_results": {
            "scout_vs_critic": {
                "level": scout_critic.level.value,
                "divergence": scout_critic.divergence_score,
                "mismatches": scout_critic.mismatch_fields
            },
            "scout_vs_synthesis": {
                "level": scout_synthesis.level.value,
                "divergence": scout_synthesis.divergence_score,
                "mismatches": scout_synthesis.mismatch_fields
            },
            "critic_vs_synthesis": {
                "level": critic_synthesis.level.value,
                "divergence": critic_synthesis.divergence_score,
                "mismatches": critic_synthesis.mismatch_fields
            }
        }
    }


# ============================================================================
# WEBSOCKET FOR REAL-TIME CONSENSUS UPDATES
# ============================================================================

@app.websocket("/ws/consensus/{agent_id}")
async def websocket_consensus(websocket: WebSocket, agent_id: str):
    """
    WebSocket connection for real-time consensus updates.
    Clients can watch an agent's consensus status change in real-time.
    """
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Get current SSV
            ssv = consensus_cache.get(agent_id)
            
            if ssv:
                # Check consensus with all other agents
                other_agents = [a for a in consensus_cache.keys() if a != agent_id]
                
                consensus_statuses = []
                for other_agent in other_agents:
                    other_ssv = consensus_cache[other_agent]
                    consensus = DynamicConsensusProtocol.compare_states(ssv, other_ssv)
                    consensus_statuses.append({
                        "agent": other_agent,
                        "level": consensus.level.value,
                        "divergence": consensus.divergence_score
                    })
                
                # Send update
                await websocket.send_json({
                    "type": "consensus_update",
                    "timestamp": datetime.now().isoformat(),
                    "agent": agent_id,
                    "consensus_with_others": consensus_statuses
                })
            
            # Update every 5 seconds
            await asyncio.sleep(5)
    
    except Exception as e:
        logger.error(f"WebSocket error for agent {agent_id}: {str(e)}")
    
    finally:
        active_connections.remove(websocket)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("ContextFlow API Server")
    print("Preventing multi-agent hallucination through context drift detection")
    print("Server: http://localhost:8000")
    print("Docs: http://localhost:8000/docs")
    print("WebSocket: ws://localhost:8000/ws/consensus/{agent_id}")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)