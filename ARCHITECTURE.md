# ContextFlow Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     ContextFlow System                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Strands    │    │   Strands    │    │   Strands    │      │
│  │   Agent 1    │    │   Agent 2    │    │   Agent 3    │      │
│  │  (Scout)     │    │  (Critic)    │    │ (Synthesis)  │      │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘      │
│         │                   │                   │               │
│         └───────────────────┼───────────────────┘               │
│                             │                                   │
│                    ┌────────▼────────┐                          │
│                    │  Strands Agent  │                          │
│                    │     Wrapper     │                          │
│                    └────────┬────────┘                          │
│                             │                                   │
│                    ┌────────▼────────┐                          │
│                    │ Semantic State  │                          │
│                    │    Vector (SSV) │                          │
│                    │  (SHA-256 Hash) │                          │
│                    └────────┬────────┘                          │
│                             │                                   │
│                    ┌────────▼────────┐                          │
│                    │ Dynamic         │                          │
│                    │ Consensus       │                          │
│                    │    Protocol     │                          │
│                    └────────┬────────┘                          │
│                             │                                   │
│         ┌───────────────────┼───────────────────┐               │
│         │                   │                   │               │
│  ┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐        │
│  │   State     │    │   State     │    │   State     │        │
│  │   Journal   │    │   Sync      │    │   Audit     │        │
│  │   (History) │    │   Engine    │    │   Trail     │        │
│  └─────────────┘    └─────────────┘    └─────────────┘        │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                     API Layer (FastAPI)                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  • /health  • /metrics  • /agents  • /consensus          │  │
│  │  • /ssv     • /journal  • /demo    • WebSocket           │  │
│  └──────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                  Frontend Dashboard (React)                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  • Metrics Panel  • Consensus Graph  • Agent Cards       │  │
│  │  • Real-time Updates  • Demo Controls  • History View    │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Agent State Generation
```
Strands Agent → Observations → SSV Generation → SHA-256 Hash → State Cache
```

### 2. Consensus Detection
```
Agent A SSV + Agent B SSV → Compare States → Divergence Score → Consensus Level
```

### 3. Consensus Resolution
```
Divergence Detected → Calculate Consensus → Sync Agents → Update Journal
```

## Key Components

### Strands Agents SDK Integration
- **Purpose**: Provides individual AI agent capabilities
- **Integration**: Wrapped via `StrandsAgentWrapper` class
- **Features**: Task execution, observation processing, decision making

### Semantic State Vector (SSV)
- **Purpose**: Cryptographic representation of agent state
- **Algorithm**: SHA-256 hashing of agent beliefs, observations, decisions
- **Benefit**: Tamper-proof state tracking

### Dynamic Consensus Protocol
- **Purpose**: Detect and resolve agent disagreements
- **Algorithm**: Pairwise comparison with divergence scoring
- **Levels**: GREEN (aligned), YELLOW (partial), RED (critical)

### State Journal
- **Purpose**: Complete audit trail of all state changes
- **Features**: Sequence tracking, hash verification, divergence detection
- **Benefit**: Debugging and compliance

## Technology Stack

### Backend
- **Python 3.11+**: Core language
- **FastAPI**: REST API framework
- **WebSockets**: Real-time updates
- **Strands SDK**: Agent framework (required for hackathon)

### Frontend
- **React 18**: UI framework
- **TypeScript**: Type safety
- **TailwindCSS**: Styling
- **Vite**: Build tool

### Infrastructure
- **Docker**: Containerization
- **Render/Railway**: Cloud deployment (optional)
- **Vercel**: Frontend hosting (optional)

## Security Features

1. **Cryptographic State Verification**: SHA-256 hashing prevents tampering
2. **Audit Trail**: Complete history of all state changes
3. **Real-time Monitoring**: WebSocket updates for immediate detection
4. **Consensus Validation**: Multi-agent agreement required for critical decisions

## Scalability

- **Horizontal Scaling**: Multiple API instances supported
- **Agent Pool**: Supports 100+ concurrent agents
- **State Caching**: Redis integration available (optional)
- **Database**: PostgreSQL support for production (optional)
