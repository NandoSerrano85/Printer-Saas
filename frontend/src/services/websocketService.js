// services/websocketService.js
class WebSocketService {
  constructor() {
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.listeners = new Map();
  }

  connect(tenantId) {
    const wsUrl = `ws://${window.location.host}/ws?tenant=${tenantId}`;
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleMessage(data);
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.attemptReconnect(tenantId);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  handleMessage(data) {
    const { type, payload } = data;
    const listeners = this.listeners.get(type) || [];
    listeners.forEach(callback => callback(payload));
  }

  subscribe(eventType, callback) {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, []);
    }
    this.listeners.get(eventType).push(callback);

    return () => {
      const listeners = this.listeners.get(eventType);
      const index = listeners.indexOf(callback);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    };
  }

  attemptReconnect(tenantId) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      setTimeout(() => {
        console.log(`Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        this.connect(tenantId);
      }, 2000 * this.reconnectAttempts);
    }
  }
}

export const wsService = new WebSocketService();

// Real-time Analytics Hook
export const useRealTimeAnalytics = () => {
  const [liveData, setLiveData] = useState(null);
  const { tenant } = useTenant();

  useEffect(() => {
    if (!tenant?.id) return;

    wsService.connect(tenant.id);

    const unsubscribe = wsService.subscribe('analytics_update', (data) => {
      setLiveData(data);
    });

    return () => {
      unsubscribe();
    };
  }, [tenant?.id]);

  return liveData;
};