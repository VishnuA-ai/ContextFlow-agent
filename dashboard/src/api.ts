import axios from 'axios';
import type { Metrics, JournalEntry, DemoResult, BeforeAfterResult, StoryResult } from './types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    throw error;
  }
);

export const apiClient = {
  async getHealth() {
    const response = await api.get('/health');
    return response.data;
  },

  async getMetrics(): Promise<Metrics> {
    const response = await api.get('/metrics');
    return response.data;
  },

  async getAgentHistory(agentId: string): Promise<{ agent_id: string; entries: number; history: JournalEntry[] }> {
    const response = await api.get(`/journal/agent/${agentId}`);
    return response.data;
  },

  async exportJournal() {
    const response = await api.get('/journal/export');
    return response.data;
  },

  async generateSSV(data: {
    agent_id: string;
    current_task: string;
    observations: Record<string, unknown>;
    decisions_made: string[];
    constraints: Record<string, unknown>;
    confidence?: number;
  }) {
    const response = await api.post('/ssv/generate', data);
    return response.data;
  },

  async checkConsensus(agentAId: string, agentBId: string) {
    const response = await api.post('/consensus/check', {
      agent_a_id: agentAId,
      agent_b_id: agentBId,
    });
    return response.data;
  },

  async checkMultiAgentConsensus(agentIds: string[]) {
    const response = await api.post('/consensus/multi-agent', agentIds);
    return response.data;
  },

  async getAgents(): Promise<{ agents: string[]; count: number; details: Record<string, AgentDetail> }> {
    const response = await api.get('/agents');
    return response.data;
  },

  async runDemo(): Promise<DemoResult> {
    const response = await api.post('/demo/run');
    return response.data;
  },

  async getBeforeAfter(): Promise<BeforeAfterResult> {
    const response = await api.post('/demo/before-after');
    return response.data;
  },

  async getStory(): Promise<StoryResult> {
    const response = await api.post('/demo/story');
    return response.data;
  },
};

export interface AgentDetail {
  id: string;
  task: string;
  state_hash: string;
  confidence: number;
  timestamp: number;
  using_strands: boolean;
}

export default api;
