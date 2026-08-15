import { create } from 'zustand';
import type { Agent, ConsensusUpdate, Metrics, JournalEntry, Toast, ModalState } from './types';

interface DashboardState {
  agents: Record<string, Agent>;
  consensusUpdates: ConsensusUpdate[];
  metrics: Metrics | null;
  selectedAgent: string | null;
  agentHistory: Record<string, JournalEntry[]>;
  isConnected: boolean;
  wsError: string | null;
  toasts: Toast[];
  modal: ModalState;
  isDemoRunning: boolean;
  
  setAgent: (agentId: string, agent: Agent) => void;
  removeAgent: (agentId: string) => void;
  addConsensusUpdate: (update: ConsensusUpdate) => void;
  setMetrics: (metrics: Metrics) => void;
  setSelectedAgent: (agentId: string | null) => void;
  setAgentHistory: (agentId: string, history: JournalEntry[]) => void;
  setConnected: (connected: boolean) => void;
  setWsError: (error: string | null) => void;
  clearUpdates: () => void;
  addToast: (toast: Omit<Toast, 'id' | 'timestamp'>) => void;
  removeToast: (id: string) => void;
  setModal: (modal: ModalState) => void;
  setDemoRunning: (running: boolean) => void;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  agents: {},
  consensusUpdates: [],
  metrics: null,
  selectedAgent: null,
  agentHistory: {},
  isConnected: false,
  wsError: null,
  toasts: [],
  modal: { isOpen: false, type: null },
  isDemoRunning: false,

  setAgent: (agentId, agent) =>
    set((state) => ({
      agents: { ...state.agents, [agentId]: agent },
    })),

  removeAgent: (agentId) =>
    set((state) => {
      const newAgents = { ...state.agents };
      delete newAgents[agentId];
      return { agents: newAgents };
    }),

  addConsensusUpdate: (update) =>
    set((state) => ({
      consensusUpdates: [...state.consensusUpdates.slice(-49), update], // Keep last 50
    })),

  setMetrics: (metrics) => set({ metrics }),

  setSelectedAgent: (agentId) => set({ selectedAgent: agentId }),

  setAgentHistory: (agentId, history) =>
    set((state) => ({
      agentHistory: { ...state.agentHistory, [agentId]: history },
    })),

  setConnected: (connected) => set({ isConnected: connected }),

  setWsError: (error) => set({ wsError: error }),

  clearUpdates: () => set({ consensusUpdates: [] }),

  addToast: (toast) =>
    set((state) => ({
      toasts: [
        ...state.toasts,
        { ...toast, id: Math.random().toString(36).substr(2, 9), timestamp: Date.now() },
      ],
    })),

  removeToast: (id) =>
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    })),

  setModal: (modal) => set({ modal }),

  setDemoRunning: (running) => set({ isDemoRunning: running }),
}));
