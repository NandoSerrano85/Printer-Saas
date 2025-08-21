import { useState, useEffect } from 'react';
import { WebSocketMessage, TenantContextValue } from '@/types';

type EventCallback = (payload: any) => void;
type UnsubscribeFunction = () => void;

interface LiveAnalyticsData {
  type: 'analytics_update';
  data: {
    orders: number;
    revenue: number;
    activeUsers: number;
    timestamp: number;
  };
}

class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts: number = 0;
  private readonly maxReconnectAttempts: number = 5;
  private listeners: Map<string, EventCallback[]> = new Map();
  private reconnectTimer: NodeJS.Timeout | null = null;
  private tenantId: string | null = null;

  connect(tenantId: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }

    this.tenantId = tenantId;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws?tenant=${tenantId}`;
    
    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('WebSocket connected for tenant:', tenantId);
        this.reconnectAttempts = 0;
        
        // Send authentication if available
        const token = localStorage.getItem('auth_token');
        if (token) {
          this.send({
            type: 'authenticate',
            payload: { token },
            timestamp: Date.now(),
          });
        }
      };

      this.ws.onmessage = (event: MessageEvent) => {
        try {
          const data: WebSocketMessage = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.ws.onclose = (event: CloseEvent) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        this.ws = null;
        
        if (event.code !== 1000) { // Not a normal closure
          this.attemptReconnect();
        }
      };

      this.ws.onerror = (error: Event) => {
        console.error('WebSocket error:', error);
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      this.attemptReconnect();
    }
  }

  private handleMessage(message: WebSocketMessage): void {
    const { type, payload } = message;
    const listeners = this.listeners.get(type) || [];
    
    listeners.forEach(callback => {
      try {
        callback(payload);
      } catch (error) {
        console.error(`Error in WebSocket listener for ${type}:`, error);
      }
    });
  }

  subscribe(eventType: string, callback: EventCallback): UnsubscribeFunction {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, []);
    }
    
    const listeners = this.listeners.get(eventType)!;
    listeners.push(callback);

    return () => {
      const index = listeners.indexOf(callback);
      if (index > -1) {
        listeners.splice(index, 1);
      }
      
      // Clean up empty listener arrays
      if (listeners.length === 0) {
        this.listeners.delete(eventType);
      }
    };
  }

  send(message: WebSocketMessage): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify(message));
      } catch (error) {
        console.error('Error sending WebSocket message:', error);
      }
    } else {
      console.warn('WebSocket not connected, unable to send message');
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max WebSocket reconnection attempts reached');
      return;
    }

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }

    this.reconnectAttempts++;
    const delay = Math.min(2000 * this.reconnectAttempts, 30000); // Max 30 second delay

    console.log(`Attempting WebSocket reconnection ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${delay}ms`);
    
    this.reconnectTimer = setTimeout(() => {
      if (this.tenantId) {
        this.connect(this.tenantId);
      }
    }, delay);
  }

  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }

    this.listeners.clear();
    this.reconnectAttempts = 0;
    this.tenantId = null;
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  getConnectionState(): string {
    if (!this.ws) return 'DISCONNECTED';
    
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING:
        return 'CONNECTING';
      case WebSocket.OPEN:
        return 'CONNECTED';
      case WebSocket.CLOSING:
        return 'CLOSING';
      case WebSocket.CLOSED:
        return 'CLOSED';
      default:
        return 'UNKNOWN';
    }
  }
}

export const wsService = new WebSocketService();

// Real-time Analytics Hook
export const useRealTimeAnalytics = (tenantData: TenantContextValue) => {
  const [liveData, setLiveData] = useState<LiveAnalyticsData | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<string>('DISCONNECTED');

  useEffect(() => {
    if (!tenantData?.tenantId) {
      console.log('No tenant ID available for WebSocket connection');
      return;
    }

    console.log('Connecting WebSocket for tenant:', tenantData.tenantId);
    wsService.connect(tenantData.tenantId);

    // Monitor connection status
    const statusInterval = setInterval(() => {
      setConnectionStatus(wsService.getConnectionState());
    }, 1000);

    const unsubscribe = wsService.subscribe('analytics_update', (data: any) => {
      console.log('Received analytics update:', data);
      setLiveData({
        type: 'analytics_update',
        data,
      });
    });

    return () => {
      clearInterval(statusInterval);
      unsubscribe();
    };
  }, [tenantData?.tenantId]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      wsService.disconnect();
    };
  }, []);

  return {
    liveData,
    connectionStatus,
    isConnected: connectionStatus === 'CONNECTED',
  };
};

export default WebSocketService;