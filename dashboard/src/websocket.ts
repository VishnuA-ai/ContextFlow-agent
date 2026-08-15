import type { ConsensusUpdate } from './types';
import { useDashboardStore } from './store';

class WebSocketManager {
  private ws: WebSocket | null = null;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 3000;

  connect(agentId: string) {
    const wsUrl = `ws://localhost:8000/ws/consensus/${agentId}`;
    
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

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        useDashboardStore.getState().setWsError('Connection error');
      };

      this.ws.onclose = () => {
        console.log(`WebSocket disconnected for agent ${agentId}`);
        useDashboardStore.getState().setConnected(false);
        this.scheduleReconnect(agentId);
      };

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      useDashboardStore.getState().setWsError('Failed to connect');
    }
  }

  private scheduleReconnect(agentId: string) {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('Max reconnection attempts reached');
      return;
    }

    this.reconnectTimer = setTimeout(() => {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
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
