export interface Agent {
  id: string;
  task: string;
  confidence: number;
  state_hash: string;
  timestamp: number;
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
  message: string;
  agents_created: string[];
  consensus_results: {
    scout_vs_critic: {
      level: string;
      divergence: number;
      mismatches: string[];
    };
    scout_vs_synthesis: {
      level: string;
      divergence: number;
      mismatches: string[];
    };
    critic_vs_synthesis: {
      level: string;
      divergence: number;
      mismatches: string[];
    };
  };
}
