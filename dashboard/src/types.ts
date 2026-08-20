export interface Agent {
  id: string;
  task: string;
  confidence: number;
  state_hash: string;
  timestamp: number;
  using_strands?: boolean;
}

export interface ConsensusStatus {
  agent: string;
  level: 'aligned' | 'minor_drift' | 'critical';
  divergence: number;
}

export interface ConsensusUpdate {
  type: 'consensus_update';
  timestamp: string;
  agent: string;
  consensus_with_others: ConsensusStatus[];
}

export interface Metrics {
  timestamp: string;
  agents_tracked: number;
  journal_entries: number;
  critical_events: number;
  active_connections: number;
  hallucination_prevention_rate: string;
}

export interface JournalEntry {
  sequence: number;
  timestamp: number;
  action: string;
  state_delta: Record<string, unknown>;
  hash_change: string;
}

export interface Toast {
  id: string;
  type: 'success' | 'error' | 'warning';
  message: string;
  timestamp: number;
}

export interface ModalState {
  isOpen: boolean;
  type: 'addAgent' | null;
}

export interface DemoResult {
  success: boolean;
  strands_mode: string;
  message: string;
  agents_created: string[];
  agent_summaries: Record<string, string>;
  consensus_results: {
    scout_vs_critic: ConsensusDetail;
    scout_vs_synthesis: ConsensusDetail;
    critic_vs_synthesis: ConsensusDetail;
  };
}

export interface ConsensusDetail {
  level: string;
  divergence: number;
  divergence_percent: string;
  mismatches: string[];
}

export interface BeforeAfterResult {
  title: string;
  without_contextflow: {
    description: string;
    scout_says: { citations: number; source: string };
    critic_says: { citations: number; source: string };
    divergence_percent: string;
    consensus_level: string;
    outcome: string;
    cost_of_failure: string;
  };
  with_contextflow: {
    description: string;
    detection: {
      divergence_detected: boolean;
      divergence_score: number;
      divergence_percent: string;
      consensus_level_before_sync: string;
      mismatched_fields: string[];
      action_taken: string;
    };
    resolution: {
      strategy: string;
      scout_citations: number;
      critic_citations: number;
      consensus_citations: number;
      explanation: string;
    };
    post_sync_consensus: {
      divergence_score: number;
      consensus_level: string;
    };
    outcome: string;
    prevention_rate: string;
  };
  summary: {
    problem_solved: string;
    how: string;
    latency: string;
    llm_calls_for_sync: number;
    strands_agents_used: number;
  };
}

export interface StoryStep {
  step: number;
  emoji: string;
  title: string;
  narrative: string;
  data: Record<string, unknown>;
}

export interface StoryResult {
  title: string;
  subtitle: string;
  strands_mode: string;
  total_steps: number;
  steps: StoryStep[];
  final_verdict: {
    problem: string;
    solution: string;
    result: string;
  };
}

export interface ResearchAgentFinding {
  agent_id: string;
  role: string;
  summary: string;
  key_facts: string[];
  confidence: number;
  source: string;
}

export interface ResearchReport {
  request_id: string;
  topic: string;
  status: string;
  executive_summary: string;
  key_findings: string[];
  agent_findings: ResearchAgentFinding[];
  contextflow_summary: {
    conflicts_detected: number;
    conflicts_resolved: number;
    consensus_level: string;
    hallucination_prevented: boolean;
    audit_trail_entries: number;
  };
  user_alert?: string;
  generated_at: number;
}

export interface MultiAgentConsensus {  system_health: string;
  consensus_graph: Record<string, { level: string; divergence: number }>;
  pairwise_results: Array<{
    pair: string;
    level: string;
    divergence: number;
    divergence_percent: string;
  }>;
  total_pairs_checked: number;
}
