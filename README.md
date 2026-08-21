# ContextFlow: Multi-Agent Consensus Engine

> Built for the **Agents for Humans Hackathon** — Amazon Web Services · Strands Agents SDK

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Strands Agents SDK](https://img.shields.io/badge/Strands_Agents-SDK-orange.svg)](https://strandsagents.com)
[![Amazon Bedrock](https://img.shields.io/badge/Amazon-Bedrock-FF9900.svg)](https://aws.amazon.com/bedrock/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://reactjs.org)
[![Track](https://img.shields.io/badge/Track-Professional_Agents-purple.svg)]()

---

## What It Does

ContextFlow is an AI research assistant that handles the repetitive, time-consuming work of literature research autonomously.

A researcher types a topic. Three Strands Agents run silently in the background — Scout gathers papers, Critic evaluates them, Synthesis merges the findings. ContextFlow monitors them the whole time, catches any disagreements, resolves conflicts automatically, and delivers a clean verified report. The researcher only gets notified if a conflict cannot be resolved.

This is the **Professional Agents track**: it makes researchers, data scientists, and academics dramatically better at a task they do every day.

---

## The Problem It Solves

When multiple AI agents work independently on the same research task, they develop conflicting beliefs. Without a consensus layer, the wrong information gets published silently.

| | Without ContextFlow | With ContextFlow |
|---|---|---|
| Scout Agent | "Paper has **145** citations" (Oct 2025 index) | "Paper has **156** citations ✅" |
| Critic Agent | "Paper has **156** citations" (Oct 2026 index) | "Paper has **156** citations ✅" |
| Result | Wrong number published silently | Divergence caught, correct value used |
| Divergence detected | Never | In **< 50ms** |
| Extra LLM calls needed | N/A | **0** |
| User notified? | No | Only if conflict cannot be resolved |

This is called **context drift** — agents developing different beliefs about the same fact. It causes cascading errors across entire multi-agent pipelines. ContextFlow is the first middleware layer that detects and resolves it automatically.

---

## How It Works

```
User types topic
       ↓
Scout Agent (Strands + Bedrock)    →  researches papers
Critic Agent (Strands + Bedrock)   →  evaluates methodology
       ↓
ContextFlow Consensus Engine
  - Generates SHA-256 state fingerprint for each agent
  - Dynamic Consensus Protocol detects divergence in < 50ms
  - If conflict: Evidence Verifier checks source recency + reliability
  - If resolved: Synthesis Agent produces unified report
  - If unresolved: User is alerted (only then)
       ↓
Verified Research Report delivered
       ↓
Immutable audit trail — every agent action recorded
```

---

## Strands Agents SDK Integration

Every agent in the system is a real Strands Agent running on Amazon Bedrock:

```python
from strands import Agent
from strands.models import BedrockModel

model = BedrockModel(model_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0")

scout_agent = Agent(
    system_prompt=(
        "You are the Scout agent. Research and gather information on AI safety techniques. "
        "Return a JSON with: task_summary, observations, decisions, confidence."
    ),
    model=model,
)

# Agent runs on Bedrock, output feeds ContextFlow consensus layer
response = scout_agent(research_prompt)
ssv = SSVGenerator.generate_ssv(agent_id="scout", observations=response.observations, ...)
```

Three Strands Agents run in every research task:
- **Scout** — searches papers, gathers citation data
- **Critic** — evaluates methodology, finds inconsistencies, flags conflicts
- **Synthesis** — merges verified findings into the final report

Without AWS credentials, agents run in simulation mode with realistic outputs — the demo always works end to end.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  ContextFlow System                  │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐    │
│  │   Scout    │  │   Critic   │  │ Synthesis  │    │
│  │  (Strands) │  │  (Strands) │  │  (Strands) │    │
│  │  (Bedrock) │  │  (Bedrock) │  │  (Bedrock) │    │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘    │
│        └───────────────┼───────────────┘            │
│                        ↓                            │
│         ┌──────────────────────────┐                │
│         │  SHA-256 State Fingerprint│               │
│         │  (SSV Generator)          │               │
│         └──────────────┬───────────┘                │
│                        ↓                            │
│         ┌──────────────────────────┐                │
│         │  Dynamic Consensus       │                │
│         │  Protocol (DCP)          │                │
│         │  GREEN / YELLOW / RED /  │                │
│         │  UNRESOLVED              │                │
│         └──────┬───────────┬───────┘                │
│                ↓           ↓                        │
│        ┌───────────┐  ┌──────────────┐             │
│        │  Evidence │  │  Async State │             │
│        │  Verifier │  │  Journal     │             │
│        │ RESOLVED_A│  │ (Immutable)  │             │
│        │ RESOLVED_B│  │ Audit Trail  │             │
│        │ UNRESOLVED│  └──────────────┘             │
│        └───────────┘                               │
├─────────────────────────────────────────────────────┤
│         FastAPI REST + WebSocket (Real-time)         │
├─────────────────────────────────────────────────────┤
│         React + TypeScript Dashboard                 │
└─────────────────────────────────────────────────────┘
```

---

## Quick Start

### Requirements
- Python 3.11+
- Node.js 18+
- AWS credentials (optional — simulation mode works without them)

### Run the Backend
```bash
cd contextflow-hackathon
pip install -r requirements.txt
python contextflow_api.py
```
API: http://localhost:8000  
Docs: http://localhost:8000/docs

### Run the Frontend
```bash
cd dashboard
npm install
npm run dev
```
Dashboard: http://localhost:3000

### Try It
1. Open http://localhost:3000
2. Type any research topic in the Research Assistant box
3. Click Research — agents run in the background
4. See the verified report with conflict resolution details

Or click **Run Demo** to see the full consensus detection flow with before/after comparison.

### Verify Everything Works
```bash
python _verify.py
# Expected: ALL CHECKS PASSED ✅
```

---

## All API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/research/run` | **User-facing** — submit a topic, get a verified report |
| POST | `/demo/run` | Run 3 Strands agents, detect divergence |
| POST | `/demo/before-after` | Side-by-side comparison with vs without ContextFlow |
| POST | `/demo/story` | 5-step narrated flow — best for judges |
| GET | `/health` | System health + Strands availability |
| GET | `/metrics` | Live metrics including conflict resolution rate |
| GET | `/agents` | All tracked agents with state details |
| POST | `/ssv/generate` | Generate SHA-256 state fingerprint for any agent |
| POST | `/consensus/check` | Compare two agents — get divergence score |
| POST | `/consensus/multi-agent` | Compare all agent pairs at once |
| GET | `/journal/agent/{id}` | Full audit trail for one agent |
| GET | `/journal/export` | Export full journal as JSON |
| GET | `/agentcore/status` | Amazon Bedrock AgentCore deployment status |
| WS | `/ws/consensus/{id}` | Real-time consensus updates every 3 seconds |

```bash
# Try the narrated story endpoint
curl -X POST http://localhost:8000/demo/story | python -m json.tool

# Try the research assistant
curl -X POST http://localhost:8000/research/run \
  -H "Content-Type: application/json" \
  -d '{"topic": "AI safety techniques", "submitted_by": "researcher"}'
```

---

## Amazon Bedrock AgentCore

Deploy all 3 Strands agents to Amazon Bedrock AgentCore:

```bash
python agentcore_deploy.py --deploy --region us-east-1
python agentcore_deploy.py --status
python agentcore_deploy.py --invoke --prompt "Research AI safety techniques"
```

AgentCore gives: managed runtime, session persistence, AWS IAM security, CloudWatch observability.

---

## Technical Design

### SHA-256 State Fingerprint (SSV)
Each agent's state is hashed with SHA-256 for tamper detection. The hash is used only for integrity checking — not for semantic comparison.

```python
@dataclass
class SemanticStateVector:
    agent_id: str
    timestamp: float
    intent_vector: Dict[str, float]   # what the agent is trying to accomplish
    belief_state: Dict[str, Any]      # current facts the agent believes
    decision_history: List[str]       # last 5 decisions made
    confidence_score: float           # 0-1 overall confidence
    state_hash: str                   # SHA-256 integrity fingerprint only
    field_evidence: Dict[str, Any]    # per-field source metadata
```

### Dynamic Consensus Protocol (DCP)
Detects divergence. Does NOT determine truth. Truth is handled by the Evidence Verifier.

- Intent vector divergence: **40% weight**
- Belief state divergence: **40% weight**
- Temporal drift (>5 min gap): **10% weight**
- Decision history mismatch: **10% weight**
- GREEN (< 5%): proceed
- YELLOW (5–15%): log and monitor
- RED (> 15%): block, trigger Evidence Verifier
- UNRESOLVED: block sync — insufficient evidence to choose

### Evidence Verifier
When DCP returns RED, the Evidence Verifier checks:
1. Source recency — newer database wins
2. Source type reliability — live API > database > cache > inferred
3. Per-field confidence scores

Returns: `RESOLVED_A`, `RESOLVED_B`, or `UNRESOLVED`

### State Journal
Every agent action is recorded immutably with: original claim, source, divergence detected, verifier result, resolution reason, sync result.

Answers: *"Why did this agent change its answer?"*

---

## Project Structure

```
contextflow-hackathon/
├── ssv_core.py              # Core: SSV, DCP, Evidence types, Journal
├── strands_wrapper.py       # Strands SDK integration (real + simulation)
├── contextflow_api.py       # FastAPI server — 22 endpoints
├── user_agent.py            # ResearchAssistant — user-facing end-to-end flow
├── agentcore_deploy.py      # Amazon Bedrock AgentCore deployment CLI
├── _verify.py               # End-to-end verification (all checks pass)
├── dashboard/
│   └── src/
│       ├── App.tsx                       # Main app
│       ├── components/
│       │   ├── ResearchAssistant.tsx     # User-facing research panel
│       │   ├── ConsensusGraph.tsx        # Animated network graph
│       │   ├── AgentCard.tsx             # Agent status cards
│       │   ├── MetricsPanel.tsx          # Live metrics
│       │   └── SuperbDemoAlert.tsx       # 5-stage demo overlay
│       └── api.ts                        # API client
├── tests/                   # Test suite
├── Dockerfile               # Production container
├── render.yaml              # Render deployment config
├── docker-compose.yml       # Full stack local deployment
├── ARCHITECTURE.md          # Architecture diagram
├── AUDIT_REPORT.md          # Full codebase audit
├── BUILD_JOURNAL.md         # Every error hit and how it was fixed
└── requirements.txt         # Pinned Python dependencies
```

---

## Running Tests

```bash
python -m pytest tests/ -v --cov=.
```

---

## Docker

```bash
docker-compose up --build
```

---

## License

MIT — see [LICENSE](LICENSE)

---

## Built For

**Agents for Humans Hackathon** — August–September 2026  
Sponsored by Amazon Web Services · Powered by Strands Agents SDK  
Track: **Professional Agents**

**Who it is for:** AI researchers, data scientists, academics — anyone who runs multi-agent pipelines as part of their daily work.

**The problem:** Multi-agent systems silently develop conflicting beliefs about the same facts. Wrong information propagates downstream before anyone notices.

**The solution:** ContextFlow sits between agents, fingerprints every state change, detects conflicts in under 50ms without any extra LLM calls, verifies which agent has better evidence, and delivers a clean verified output to the user.

**Why it matters:** The same problem exists in healthcare (conflicting patient data), finance (conflicting trading signals), and legal (conflicting contract interpretations). ContextFlow is the consensus layer that any multi-agent Strands system can plug into.
