import type { ConsensusUpdate } from './types';
import { useDashboardStore } from './store';

// Derive WebSocket URL from the API URL — works in both local and production
function getWsBaseUrl(): string {
  const apiUrl = import.meta.env.VITE_API_URL || '';

  // If VITE_API_URL is a full URL (production: https://contextflow-agent-1.onrender.com)
  if (apiUrl.startsWith('http')) {
    return apiUrl.replace(/^http/, 'ws').replace(/\/api$/, '');
  }

  // Local dev — use current host
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  return `${protocol}://${window.location.hostname}:8000`;
}

class WebSocketManager {
  private ws: WebSocket | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 3;
  private reconnectDelay = 5000;

  connect(agentId: string) {
    const wsBase = getWsBaseUrl();
    const wsUrl = `${wsBase}/ws/consensus/${agentId}`;

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log(`WebSocket connected for agent ${agentId}`);
        useDashboardStore.getState().setConnected(true);
        useDashboardStore.getState().setWsError(null);
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const data: ConsensusUpdate = JSON.parse(event.data);
          useDashboardStore.getState().addConsensusUpdate(data);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onerror = () => {
        useDashboardStore.getState().setWsError('WebSocket unavailable in deployment — using polling');
      };

      this.ws.onclose = () => {
        useDashboardStore.getState().setConnected(false);
        this.scheduleReconnect(agentId);
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      useDashboardStore.getState().setWsError('WebSocket unavailable — using polling');
    }
  }

  private scheduleReconnect(agentId: string) {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) return;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectAttempts++;
      this.connect(agentId);
    }, this.reconnectDelay);
  }

  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    useDashboardStore.getState().setConnected(false);
  }
}

export const wsManager = new WebSocketManager();
