/**
 * WebSocket Token Manager for Frontend
 * Real-time token monitoring without API calls
 */

import tokenManager from './tokenManager';

interface TokenMessage {
  call_refresh?: boolean;
  time_remaining_seconds?: number;
  message?: string;
}

interface TokenUpdateCallback {
  (message: TokenMessage): void;
}

interface ErrorCallback {
  (error: any): void;
}

class WebSocketTokenManager {
  private websocket: WebSocket | null = null;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectDelay: number = 1000; // Start with 1 second
  private isConnected: boolean = false;
  private tokenUpdateCallbacks: TokenUpdateCallback[] = [];
  private errorCallbacks: ErrorCallback[] = [];

  /**
   * Initialize WebSocket connection
   */
  async connect(token?: string): Promise<void> {
    try {
      // Use provided token or get from localStorage
      const accessToken = token || localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
      
      if (!accessToken) {
        console.error('❌ No token available for WebSocket connection');
        throw new Error('No access token available');
      }

      // Create WebSocket connection - connect directly to backend
      const wsUrl = `ws://localhost:8000/ws/token-monitor?token=${accessToken}`;
      console.log('🔌 Attempting to connect to WebSocket:', wsUrl);
      
      this.websocket = new WebSocket(wsUrl);

      // Set up event handlers
      this.websocket.onopen = () => {
        console.log('✅ WebSocket connected successfully for token monitoring');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000;
      };

      this.websocket.onmessage = (event) => {
        console.log('📨 Received WebSocket message:', event.data);
        try {
          const parsedMessage = JSON.parse(event.data);
          this.handleMessage(parsedMessage);
        } catch (error) {
          console.error('❌ Failed to parse WebSocket message:', error);
        }
      };

      this.websocket.onclose = (event) => {
        console.log('❌ WebSocket disconnected:', {
          code: event.code,
          reason: event.reason,
          wasClean: event.wasClean
        });
        this.isConnected = false;
        this.handleDisconnection();
      };

      this.websocket.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        this.handleError(error);
      };

    } catch (error) {
      console.error('❌ Failed to create WebSocket connection:', error);
      this.handleError(error);
    }
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleMessage(message: TokenMessage): void {
    console.log('📨 Processing WebSocket message:', message);

    // Handle token status messages with time remaining below 120 seconds
    if (message.time_remaining_seconds !== undefined && 
        message.time_remaining_seconds < 120) {
      
      console.log(`⏰ Token expires in ${message.time_remaining_seconds} seconds`);
      console.log(`📝 Message: ${message.message}`);
      
      // Check if we need to call refresh token endpoint
      if (message.call_refresh) {
        console.log('🔄 Auto-refreshing token via API call...');
        this.callRefreshTokenEndpoint();
      }
    }
  }

  /**
   * Call the refresh token endpoint directly
   */
  private async callRefreshTokenEndpoint(): Promise<void> {
    try {
      const refreshToken = this.getStoredRefreshToken();
      const accessToken = this.getStoredToken();
      
      if (!refreshToken) {
        console.error('❌ No refresh token available for API call');
        this.logoutUser();
        return;
      }

      if (!accessToken) {
        console.error('❌ No access token available for API call');
        this.logoutUser();
        return;
      }

      console.log('🔄 Calling refresh token endpoint...');
      const response = await fetch('http://localhost:8000/auth/refresh-token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify({
          refresh_token: refreshToken
        })
      });

      if (response.ok) {
        const data = await response.json();
        console.log('✅ Token refreshed successfully via API');
        
        // Store new tokens
        if (data.access_token) {
          localStorage.setItem('auth_token', data.access_token);
        }
        if (data.refresh_token) {
          localStorage.setItem('refresh_token', data.refresh_token);
        }

        // Notify callbacks about successful refresh
        this.tokenUpdateCallbacks.forEach(callback => {
          callback({
            call_refresh: false,
            time_remaining_seconds: 0,
            message: 'Token refreshed successfully'
          });
        });
      } else {
        console.error('❌ Failed to refresh token via API:', response.status, response.statusText);
        this.handleRefreshError('API refresh failed');
        this.logoutUser();
      }
    } catch (error) {
      console.error('❌ Error calling refresh token endpoint:', error);
      this.handleRefreshError(error instanceof Error ? error.message : 'Unknown error');
      this.logoutUser();
    }
  }

  /**
   * Handle refresh error
   */
  private handleRefreshError(message: string): void {
    console.error('Token refresh failed:', message);
    
    // Notify error callbacks
    this.errorCallbacks.forEach(callback => {
      callback({ call_refresh: false, time_remaining_seconds: 0, message });
    });
  }

  /**
   * Handle WebSocket errors
   */
  private handleError(error: any): void {
    console.error('WebSocket error:', error);
    
    // Notify error callbacks
    this.errorCallbacks.forEach(callback => {
      callback(error);
    });
  }

  /**
   * Handle WebSocket disconnection
   */
  private handleDisconnection(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      console.log(`Attempting to reconnect (${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`);
      
      setTimeout(() => {
        this.reconnectAttempts++;
        this.reconnectDelay *= 2; // Exponential backoff
        const token = this.getStoredToken();
        if (token) {
          this.connect(token);
        }
      }, this.reconnectDelay);
    } else {
      console.error('Max reconnection attempts reached');
      this.logoutUser();
    }
  }

  /**
   * Logout user when token is invalid
   */
  private logoutUser(): void {
    console.log('🚪 Token invalid, logging out user automatically...');
    tokenManager.clearAuth();
  }

  /**
   * Send message to WebSocket
   */
  private sendMessage(message: any): void {
    if (this.isConnected && this.websocket) {
      this.websocket.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected, cannot send message');
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
   * Disconnect WebSocket
   */
  disconnect(): void {
    if (this.websocket) {
      this.websocket.close();
      this.websocket = null;
    }
    this.isConnected = false;
    this.removeCallbacks();
  }

  /**
   * Get stored access token
   */
  getStoredToken(): string | null {
    return localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
  }

  /**
   * Get stored refresh token
   */
  getStoredRefreshToken(): string | null {
    return localStorage.getItem('refresh_token') || sessionStorage.getItem('refresh_token');
  }

  /**
   * Store tokens
   */
  storeTokens(accessToken: string, refreshToken: string): void {
    localStorage.setItem('auth_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
  }

  /**
   * Clear stored tokens
   */
  clearStoredTokens(): void {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('refresh_token');
    sessionStorage.removeItem('auth_token');
    sessionStorage.removeItem('refresh_token');
  }

  /**
   * Check if WebSocket is connected
   */
  getConnected(): boolean {
    return this.isConnected;
  }

  /**
   * Get connection status details
   */
  getConnectionStatus(): {
    isConnected: boolean;
    readyState: number;
    url: string | null;
    tokenAvailable: boolean;
    tokenLength: number;
  } {
    const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
    return {
      isConnected: this.isConnected,
      readyState: this.websocket?.readyState || 3, // 3 = CLOSED
      url: this.websocket?.url || null,
      tokenAvailable: !!token,
      tokenLength: token?.length || 0
    };
  }
}

// Create singleton instance
const wsTokenManager = new WebSocketTokenManager();

export default wsTokenManager; 