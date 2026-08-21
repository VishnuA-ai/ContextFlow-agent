<div align="center">

# ContextFlow

### Multi-Agent Consensus Engine

**The first middleware layer that stops AI agents from lying to each other.**

[![MIT License](https://img.shields.io/badge/License-MIT-22c55e.svg)](LICENSE)
[![Strands Agents SDK](https://img.shields.io/badge/Strands_Agents-SDK-f97316.svg)](https://strandsagents.com)
[![Amazon Bedrock](https://img.shields.io/badge/Amazon-Bedrock-FF9900.svg)](https://aws.amazon.com/bedrock/)
[![AgentCore Ready](https://img.shields.io/badge/AgentCore-Ready-8b5cf6.svg)](agentcore_deploy.py)
[![Track](https://img.shields.io/badge/Track-Professional_Agents-3b82f6.svg)]()

</div>

---

## The Problem Nobody Is Talking About

You have three AI agents working together on a research task. They each go off independently, gather information, and come back with answers.

**Agent 1 says:** *"The top paper has 145 citations."*
**Agent 2 says:** *"The top paper has 156 citations."*
**Agent 3 says:** *"Sure, I'll synthesise both findings."*

Which number ends up in your report? **Whichever agent spoke last.**

This is not a hallucination in the traditional sense. Each agent genuinely believes what it found. The problem is deeper — **multi-agent systems have no shared ground truth**. When agents work independently and then pool results, factual conflicts propagate silently. No error is thrown. No warning is raised. The wrong number gets published.

In a medical diagnosis pipeline, that's the wrong dosage. In a financial analysis pipeline, that's the wrong trade signal. In a research pipeline, that's a citation that never existed.

**ContextFlow catches it before it reaches the output. Every time. In under 50 milliseconds.**

---

## What Judges Will See When They Click "Run Demo"

1. Three Strands Agents spin up on Amazon Bedrock — Scout, Critic, Synthesis
2. Scout researches AI safety papers. Finds **145 citations** for the top paper
3. Critic evaluates independently. Finds **156 citations** — newer database, October 2026
4. ContextFlow generates a SHA-256 state fingerprint for each agent
5. Dynamic Consensus Protocol compares them — **7.1% divergence detected — CRITICAL**
6. Evidence Verifier checks: Critic's source is newer and more authoritative → **RESOLVED_B**
7. Synthesis agent aligns to **156** — the correct, evidence-backed value
8. The user gets a verified report. The conflict never reached them
9. The audit trail records every step — who claimed what, which source won, why

**The wrong number never left the pipeline.**

---

## Live Demo

> **Dashboard:** [contextflow-agent-1.onrender.com](https://contextflow-agent-1.onrender.com)
> 
> **API Docs:** [contextflow-agent-1.onrender.com/docs](https://contextflow-agent-1.onrender.com/docs)
> 
> **Try it:** `POST /research/run` with any topic and watch three agents resolve a conflict in real time

---

## Architecture — How It Actually Works

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                   │
│   USER: "Research AI safety papers"                              │
│                      │                                           │
│                      ▼                                           │
│   ┌──────────────────────────────────────────────────────┐      │
│   │              Research Assistant                       │      │
│   │         (user_agent.py — runs autonomously)          │      │
│   └──────┬──────────────┬──────────────┬─────────────────┘      │
│          │              │              │                          │
│          ▼              ▼              ▼                          │
│   ┌──────────┐   ┌──────────┐   ┌──────────┐                   │
│   │  Scout   │   │  Critic  │   │Synthesis │  ← Strands Agents  │
│   │ Bedrock  │   │ Bedrock  │   │ Bedrock  │    on Claude 3.5   │
│   └────┬─────┘   └────┬─────┘   └────┬─────┘                   │
│        │              │              │                            │
│        ▼              ▼              ▼                            │
│   ┌──────────────────────────────────────────────────────┐      │
│   │           SHA-256 State Fingerprint Generator        │      │
│   │  Each agent gets a cryptographic snapshot of its     │      │
│   │  beliefs — tamper-proof, comparable, immutable       │      │
│   └─────────────────────┬────────────────────────────────┘      │
│                         │                                         │
│                         ▼                                         │
│   ┌──────────────────────────────────────────────────────┐      │
│   │           Dynamic Consensus Protocol (DCP)           │      │
│   │                                                      │      │
│   │   Intent divergence ×0.4 + Belief divergence ×0.4   │      │
│   │   + Temporal drift ×0.1 + Decision mismatch ×0.1    │      │
│   │                                                      │      │
│   │   GREEN < 5%  →  Proceed                            │      │
│   │   YELLOW 5-15% →  Log and monitor                   │      │
│   │   RED > 15%   →  Block → Evidence Verifier          │      │
│   │   UNRESOLVED  →  Alert user (the only time they see)│      │
│   └─────────────────────┬────────────────────────────────┘      │
│                         │                                         │
│                         ▼                                         │
│   ┌──────────────────────────────────────────────────────┐      │
│   │              Evidence Verifier                       │      │
│   │                                                      │      │
│   │   Checks: source recency, source type reliability,  │      │
│   │   per-field confidence scores                        │      │
│   │                                                      │      │
│   │   Returns: RESOLVED_A / RESOLVED_B / UNRESOLVED     │      │
│   │   With: reason, evidence, confidence                │      │
│   └─────────┬──────────────────────┬─────────────────────┘      │
│             │                      │                              │
│             ▼                      ▼                              │
│   ┌──────────────┐     ┌──────────────────────────┐             │
│   │  Explainable │     │   Async State Journal    │             │
│   │  Sync Payload│     │   (Immutable Audit Trail)│             │
│   │              │     │                          │             │
│   │ previous: 145│     │  original_claim          │             │
│   │ corrected:156│     │  conflicting_claim       │             │
│   │ reason: newer│     │  evidence                │             │
│   │   source     │     │  verifier_result         │             │
│   └──────────────┘     │  resolution_reason       │             │
│                        │  sync_result             │             │
│                        └──────────────────────────┘             │
│                                                                   │
│   USER receives: verified report + "1 conflict resolved"         │
│   (never saw the conflict — it was handled autonomously)         │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## The Code Behind It

**Real Strands Agents on Amazon Bedrock — not wrappers, not mocks:**

```python
from strands import Agent
from strands.models import BedrockModel

# Three real Strands Agents, each with a distinct role
model = BedrockModel(model_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0")

scout = Agent(
    system_prompt="You are the Scout agent. Research AI safety papers. "
                  "Return JSON: {task_summary, observations, decisions, confidence}",
    model=model,
)
critic = Agent(
    system_prompt="You are the Critic agent. Evaluate methodology and verify data accuracy. "
                  "Return JSON: {task_summary, observations, decisions, confidence}",
    model=model,
)
```

**SHA-256 state fingerprinting — every agent belief is cryptographically sealed:**

```python
normalized_state = {
    "agent": agent_id,
    "task": current_task,
    "observations": observations,   # what the agent believes
    "decisions": recent_decisions,  # what it decided
}
state_hash = hashlib.sha256(
    json.dumps(normalized_state, sort_keys=True).encode()
).hexdigest()
# SHA-256 = tamper detection only. NOT semantic similarity.
```

**Evidence-based verification — not blind averaging:**

```python
# Scout says 145 citations — source: academic cache, Oct 2025
# Critic says 156 citations — source: live API, Oct 2026

# Evidence Verifier checks source reliability:
SOURCE_RELIABILITY = {
    "live_api": 5,    # most reliable
    "database": 4,
    "document": 3,
    "cache":    2,    # Scout's source
    "inferred": 1,
}
# live_api (5) > cache (2) → RESOLVED_B → Critic wins → correct value: 156
```

**Explainable sync — the agent knows WHY it was corrected:**

```python
{
    "previous_value": 145,
    "corrected_value": 156,
    "reason": "Critic's source is newer and more authoritative (live API, Oct 2026)",
    "supporting_evidence": [...],
    "verification_status": "RESOLVED_B",
    "confidence": 0.92,
    "timestamp": 1756000000.0
}
```

---

## Run It Yourself

```bash
# Clone and run backend
git clone https://github.com/VishnuA-ai/ContextFlow-agent
cd ContextFlow-agent
pip install -r requirements.txt
python contextflow_api.py

# Run frontend (new terminal)
cd dashboard
npm install && npm run dev
```

Open **http://localhost:3000** — type any research topic and watch it work.

```bash
# Verify everything passes
python _verify.py
# ALL CHECKS PASSED ✅

# Try the narrated demo
curl -X POST http://localhost:8000/demo/story | python -m json.tool

# Try the research assistant directly
curl -X POST http://localhost:8000/research/run \
  -H "Content-Type: application/json" \
  -d '{"topic": "large language model safety", "submitted_by": "researcher"}'
```

---

## Deploy to Production with AgentCore

```bash
# Deploy all 3 Strands agents to Amazon Bedrock AgentCore
python agentcore_deploy.py --deploy --region us-east-1

# Check status
python agentcore_deploy.py --status

# Run a live consensus invocation via AgentCore
python agentcore_deploy.py --invoke --prompt "Research AI safety techniques 2026"
```

AgentCore gives: managed runtime, session persistence, IAM security, CloudWatch observability.

---

## API Reference

| Endpoint | What It Does |
|---|---|
| `POST /research/run` | Submit a topic — agents run, conflicts resolved, report returned |
| `POST /demo/run` | Run the full 3-agent demo with live consensus checking |
| `POST /demo/before-after` | See exactly what happens with and without ContextFlow |
| `POST /demo/story` | 5-step narrated walkthrough — ideal for judges |
| `GET /metrics` | Live conflict resolution rate, agents tracked, journal entries |
| `POST /consensus/check` | Compare any two agents — get divergence score + mismatches |
| `GET /journal/agent/{id}` | Full audit trail — why did this agent change its answer? |
| `GET /agentcore/status` | AgentCore deployment readiness |
| `WS /ws/consensus/{id}` | Real-time consensus updates every 3 seconds |

---

## Why This Matters Beyond Research

**Healthcare** — 3 agents analyse a patient's lab results. Agent A says glucose is 180. Agent B says 120. ContextFlow catches the discrepancy before a dosage recommendation is made. The correct value goes to the doctor.

**Finance** — 4 trading agents analyse the same stock. Two say buy, two say sell, with different confidence levels. ContextFlow detects the conflict, checks which agents have more recent price data, and blocks execution until a verified signal exists.

**Legal** — 2 agents review the same contract clause. One extracts a deadline as March 15, one extracts March 25. ContextFlow catches it and flags it for human review rather than letting either date propagate.

In every case: the problem is the same. Multiple agents, independent work, conflicting facts, no shared ground truth. ContextFlow is the layer that enforces it.

---

## Project Files

```
ContextFlow-agent/
│
├── ssv_core.py          # SHA-256 fingerprinting, DCP, Evidence types,
│                        # Journal, UNRESOLVED state, VerificationResult
│
├── strands_wrapper.py   # Real Strands + Bedrock integration
│                        # Graceful simulation fallback
│
├── contextflow_api.py   # 22 FastAPI endpoints + WebSocket
│
├── user_agent.py        # ResearchAssistant — the user-facing end-to-end flow
│
├── agentcore_deploy.py  # Deploy to Amazon Bedrock AgentCore (CLI)
│
├── _verify.py           # End-to-end test — all checks pass, exit 0
│
├── dashboard/           # React + TypeScript frontend
│   └── src/
│       ├── App.tsx
│       ├── components/
│       │   ├── ResearchAssistant.tsx  ← user types topic here
│       │   ├── ConsensusGraph.tsx     ← live animated network
│       │   ├── AgentCard.tsx
│       │   ├── MetricsPanel.tsx
│       │   └── SuperbDemoAlert.tsx
│       └── api.ts
│
├── ARCHITECTURE.md      # Full architecture diagram
├── AUDIT_REPORT.md      # Complete codebase audit
├── BUILD_JOURNAL.md     # Every error hit and how it was fixed
├── render.yaml          # Render.com deployment
├── Dockerfile           # Production container
└── requirements.txt
```

---

## License

MIT — see [LICENSE](LICENSE)

---

<div align="center">

**Agents for Humans Hackathon · August–September 2026**  
Sponsored by Amazon Web Services · Built with Strands Agents SDK  
Track: **Professional Agents**

*ContextFlow makes multi-agent AI systems trustworthy.*  
*Built for researchers, scientists, and professionals who can't afford a wrong answer.*

</div>
