/**
 * WebSocket Client for Real-time Chat Messaging
 * Handles WebSocket connections, message sending, and event listeners
 */

type MessageHandler = (message: any) => void;

export class ChatWebSocket {
  private ws: WebSocket | null = null;
  private url: string;
  private employeeId: number;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 3000; // 3 seconds
  private messageHandlers: Set<MessageHandler> = new Set();
  private isIntentionalClose = false;

  constructor(employeeId: number, baseUrl?: string) {
    this.employeeId = employeeId;
    // Use WebSocket protocol (ws:// or wss://)
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = baseUrl || window.location.host.replace('3000', '8000'); // Frontend on 3000, backend on 8000
    this.url = `${wsProtocol}//${wsHost}/ws/chat?employee_id=${employeeId}`;
  }

  /**
   * Connect to WebSocket server
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        console.log('🔌 Connecting to WebSocket:', this.url.replace(String(this.employeeId), '***'));
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          console.log('✅ WebSocket connected');
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            console.log('📨 WebSocket message received:', message.type);

            // Notify all registered handlers
            this.messageHandlers.forEach(handler => {
              try {
                handler(message);
              } catch (error) {
                console.error('Error in message handler:', error);
              }
            });
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        this.ws.onerror = (error) => {
          console.error('❌ WebSocket error:', error);
          reject(error);
        };

        this.ws.onclose = (event) => {
          console.log('🔌 WebSocket closed:', event.code, event.reason);
          this.ws = null;

          // Attempt reconnection if not intentionally closed
          if (!this.isIntentionalClose && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`🔄 Reconnecting... (Attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

            setTimeout(() => {
              this.connect().catch(err => {
                console.error('Reconnection failed:', err);
              });
            }, this.reconnectDelay);
          }
        };
      } catch (error) {
        console.error('Failed to create WebSocket:', error);
        reject(error);
      }
    });
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    this.isIntentionalClose = true;
    if (this.ws) {
      this.ws.close(1000, 'Client disconnecting');
      this.ws = null;
    }
    this.messageHandlers.clear();
    console.log('👋 WebSocket disconnected');
  }

  /**
   * Check if WebSocket is connected
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  /**
   * Send a message through WebSocket
   */
  send(message: any): void {
    if (!this.isConnected()) {
      console.error('WebSocket not connected');
      return;
    }

    try {
      this.ws!.send(JSON.stringify(message));
      console.log('📤 WebSocket message sent:', message.type);
    } catch (error) {
      console.error('Failed to send WebSocket message:', error);
    }
  }

  /**
   * Register a message handler
   */
  onMessage(handler: MessageHandler): () => void {
    this.messageHandlers.add(handler);

    // Return unsubscribe function
    return () => {
      this.messageHandlers.delete(handler);
    };
  }

  /**
   * Send a new chat message
   */
  sendMessage(leadId: number, message: string, exhibitionId?: number): void {
    this.send({
      type: 'new_message',
      lead_id: leadId,
      message,
      exhibition_id: exhibitionId,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Send typing indicator
   */
  sendTypingIndicator(leadId: number, isTyping: boolean, exhibitionId?: number): void {
    this.send({
      type: 'typing_indicator',
      lead_id: leadId,
      is_typing: isTyping,
      exhibition_id: exhibitionId,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Send lead status update
   */
  sendLeadUpdate(leadId: number, status: string, exhibitionId?: number): void {
    this.send({
      type: 'lead_update',
      lead_id: leadId,
      status,
      exhibition_id: exhibitionId,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Send ping to keep connection alive
   */
  sendPing(): void {
    this.send({
      type: 'ping',
      timestamp: new Date().toISOString()
    });
  }
}

/**
 * Global WebSocket instance (singleton)
 */
let globalWebSocket: ChatWebSocket | null = null;

/**
 * Get or create global WebSocket instance
 */
export function getWebSocket(employeeId?: number): ChatWebSocket | null {
  if (!globalWebSocket && employeeId) {
    globalWebSocket = new ChatWebSocket(employeeId);
  }
  return globalWebSocket;
}

/**
 * Close and cleanup global WebSocket instance
 */
export function closeWebSocket(): void {
  if (globalWebSocket) {
    globalWebSocket.disconnect();
    globalWebSocket = null;
  }
}
