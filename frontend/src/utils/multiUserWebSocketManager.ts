/**
 * Multi-User WebSocket Token Manager
 * Handles WebSocket connections for multiple users
 */

interface UserWebSocketConnection {
  userId: string;
  websocket: WebSocket;
  isConnected: boolean;
  reconnectAttempts: number;
  lastPing: number;
  token: string;
}

interface TokenMessage {
  type: string;
  access_token?: string;
  refresh_token?: string;
  user?: any;
  should_refresh?: boolean;
  time_remaining_seconds?: number;
  message?: string;
  user_id?: string; // Backend should include user_id in messages
}

interface TokenUpdateCallback {
  (message: TokenMessage, userId: string): void;
}

interface ErrorCallback {
  (error: any, userId: string): void;
}

class MultiUserWebSocketManager {
  private connections: Map<string, UserWebSocketConnection> = new Map();
  private tokenUpdateCallbacks: TokenUpdateCallback[] = [];
  private errorCallbacks: ErrorCallback[] = [];
  private reconnectDelay = 1000;
  private maxReconnectAttempts = 5;

  constructor() {
    // Removed ping interval initialization since this manager is not being used
  }

  /**
   * Connect a specific user to WebSocket
   */
  async connectUser(userId: string, token: string): Promise<boolean> {
    try {
      // Disconnect existing connection for this user
      this.disconnectUser(userId);

      console.log(`🔌 Connecting user ${userId} to WebSocket...`);
      
      const wsUrl = `ws://localhost:8000/ws/token-monitor?token=${token}&user_id=${userId}`;
      const websocket = new WebSocket(wsUrl);

      const connection: UserWebSocketConnection = {
        userId,
        websocket,
        isConnected: false,
        reconnectAttempts: 0,
        lastPing: Date.now(),
        token
      };

      websocket.onopen = () => {
        console.log(`✅ WebSocket connected for user ${userId}`);
        connection.isConnected = true;
        connection.reconnectAttempts = 0;
        this.connections.set(userId, connection);
      };

      websocket.onmessage = (event) => {
        console.log(`📨 Received message for user ${userId}:`, event.data);
        try {
          const message: TokenMessage = JSON.parse(event.data);
          this.handleMessage(message, userId);
        } catch (error) {
          console.error(`❌ Failed to parse message for user ${userId}:`, error);
        }
      };

      websocket.onclose = (event) => {
        console.log(`❌ WebSocket disconnected for user ${userId}:`, {
          code: event.code,
          reason: event.reason,
          wasClean: event.wasClean
        });
        connection.isConnected = false;
        this.handleDisconnection(userId, event);
      };

      websocket.onerror = (error) => {
        console.error(`❌ WebSocket error for user ${userId}:`, error);
        this.handleError(error, userId);
      };

      return true;
    } catch (error) {
      console.error(`❌ Failed to connect user ${userId}:`, error);
      return false;
    }
  }

  /**
   * Disconnect a specific user
   */
  disconnectUser(userId: string): void {
    const connection = this.connections.get(userId);
    if (connection) {
      console.log(`🔌 Disconnecting user ${userId}`);
      connection.websocket.close();
      this.connections.delete(userId);
    }
  }

  /**
   * Disconnect all users
   */
  disconnectAll(): void {
    console.log('🔌 Disconnecting all users');
    this.connections.forEach((connection, userId) => {
      connection.websocket.close();
    });
    this.connections.clear();
  }

  /**
   * Handle incoming messages
   */
  private handleMessage(message: TokenMessage, userId: string): void {
    // Add user_id to message if not present
    if (!message.user_id) {
      message.user_id = userId;
    }

    switch (message.type) {
      case 'connected':
        console.log(`✅ User ${userId} connected successfully`);
        break;

      case 'token_status':
        this.handleTokenStatus(message, userId);
        break;

      case 'token_refreshed':
        this.handleTokenRefreshed(message, userId);
        break;

      case 'token_expired':
        this.handleTokenExpired(message, userId);
        break;

      case 'token_invalid':
        this.handleTokenInvalid(message, userId);
        break;

      case 'refresh_error':
        this.handleRefreshError(message, userId);
        break;

      default:
        console.warn(`⚠️ Unknown message type for user ${userId}:`, message.type);
    }
  }

  /**
   * Handle token status updates
   */
  private handleTokenStatus(message: TokenMessage, userId: string): void {
    // Update last ping time
    const connection = this.connections.get(userId);
    if (connection) {
      connection.lastPing = Date.now();
    }

    // Notify callbacks about token status
    this.tokenUpdateCallbacks.forEach(callback => {
      callback(message, userId);
    });
  }

  /**
   * Handle successful token refresh
   */
  private handleTokenRefreshed(message: TokenMessage, userId: string): void {
    if (message.access_token && message.refresh_token) {
      // Store new tokens for this user
      this.storeUserTokens(userId, message.access_token, message.refresh_token);
      
      // Notify callbacks
      this.tokenUpdateCallbacks.forEach(callback => {
        callback(message, userId);
      });

      console.log(`Token refreshed successfully for user ${userId}`);
    }
  }

  /**
   * Handle token expiration
   */
  private handleTokenExpired(message: TokenMessage, userId: string): void {
    console.log(`Token expired for user ${userId}, disconnecting...`);
    this.clearUserTokens(userId);
    this.disconnectUser(userId);
    
    // Notify callbacks
    this.tokenUpdateCallbacks.forEach(callback => {
      callback(message, userId);
    });
  }

  /**
   * Handle invalid token
   */
  private handleTokenInvalid(message: TokenMessage, userId: string): void {
    console.log(`Token invalid for user ${userId}, disconnecting...`);
    this.clearUserTokens(userId);
    this.disconnectUser(userId);
    
    // Notify callbacks
    this.tokenUpdateCallbacks.forEach(callback => {
      callback(message, userId);
    });
  }

  /**
   * Handle refresh error
   */
  private handleRefreshError(message: TokenMessage, userId: string): void {
    console.error(`Token refresh failed for user ${userId}:`, message.message);
    
    // Notify error callbacks
    this.errorCallbacks.forEach(callback => {
      callback(message, userId);
    });
  }

  /**
   * Handle WebSocket errors
   */
  private handleError(error: any, userId: string): void {
    console.error(`❌ WebSocket error for user ${userId}:`, error);
    
    // Notify error callbacks
    this.errorCallbacks.forEach(callback => {
      callback(error, userId);
    });
  }

  /**
   * Handle WebSocket disconnection
   */
  private handleDisconnection(userId: string, event: CloseEvent): void {
    const connection = this.connections.get(userId);
    if (!connection) return;

    if (connection.reconnectAttempts < this.maxReconnectAttempts) {
      console.log(`Attempting to reconnect user ${userId} (${connection.reconnectAttempts + 1}/${this.maxReconnectAttempts})`);
      
      setTimeout(() => {
        connection.reconnectAttempts++;
        this.reconnectDelay *= 2; // Exponential backoff
        this.connectUser(userId, connection.token);
      }, this.reconnectDelay);
    } else {
      console.error(`Max reconnection attempts reached for user ${userId}`);
      this.connections.delete(userId);
    }
  }

  /**
   * Request token refresh from server
   */
  private requestTokenRefresh(userId: string): void {
    const connection = this.connections.get(userId);
    if (!connection || !connection.isConnected) {
      console.warn(`WebSocket not connected for user ${userId}, cannot request token refresh`);
      return;
    }

    const refreshToken = this.getUserRefreshToken(userId);
    if (!refreshToken) {
      console.error(`No refresh token available for user ${userId}`);
      return;
    }

    this.sendMessage(userId, {
      type: 'refresh_token',
      refresh_token: refreshToken
    });
  }

  /**
   * Send message to a specific user's WebSocket
   */
  sendMessage(userId: string, message: any): void {
    const connection = this.connections.get(userId);
    if (connection && connection.isConnected) {
      connection.websocket.send(JSON.stringify(message));
    } else {
      console.warn(`WebSocket not connected for user ${userId}, cannot send message`);
    }
  }

  /**
   * Add token update callback
   */
  onTokenUpdate(callback: TokenUpdateCallback): void {
    this.tokenUpdateCallbacks.push(callback);
  }

  /**
   * Add error callback
   */
  onError(callback: ErrorCallback): void {
    this.errorCallbacks.push(callback);
  }

  /**
   * Remove callbacks
   */
  removeCallbacks(): void {
    this.tokenUpdateCallbacks = [];
    this.errorCallbacks = [];
  }

  /**
   * Get connection status for a specific user
   */
  getUserConnectionStatus(userId: string): {
    isConnected: boolean;
    readyState: number;
    reconnectAttempts: number;
    lastPing: number;
  } | null {
    const connection = this.connections.get(userId);
    if (!connection) return null;

    return {
      isConnected: connection.isConnected,
      readyState: connection.websocket.readyState,
      reconnectAttempts: connection.reconnectAttempts,
      lastPing: connection.lastPing
    };
  }

  /**
   * Get all connected user IDs
   */
  getConnectedUsers(): string[] {
    return Array.from(this.connections.keys());
  }

  /**
   * Check if a specific user is connected
   */
  isUserConnected(userId: string): boolean {
    const connection = this.connections.get(userId);
    return connection ? connection.isConnected : false;
  }

  /**
   * Store tokens for a specific user
   */
  private storeUserTokens(userId: string, accessToken: string, refreshToken: string): void {
    localStorage.setItem(`auth_token_${userId}`, accessToken);
    localStorage.setItem(`refresh_token_${userId}`, refreshToken);
  }

  /**
   * Get token for a specific user
   */
  getUserToken(userId: string): string | null {
    return localStorage.getItem(`auth_token_${userId}`);
  }

  /**
   * Get refresh token for a specific user
   */
  getUserRefreshToken(userId: string): string | null {
    return localStorage.getItem(`refresh_token_${userId}`);
  }

  /**
   * Clear tokens for a specific user
   */
  private clearUserTokens(userId: string): void {
    localStorage.removeItem(`auth_token_${userId}`);
    localStorage.removeItem(`refresh_token_${userId}`);
  }

  /**
   * Clean up resources
   */
  destroy(): void {
    this.disconnectAll();
    this.removeCallbacks();
  }
}

// Create singleton instance
const multiUserWebSocketManager = new MultiUserWebSocketManager();

export default multiUserWebSocketManager; 