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
  private reconnectDelay: number = 1000;
  private isConnected: boolean = false;
  private tokenUpdateCallbacks: TokenUpdateCallback[] = [];
  private errorCallbacks: ErrorCallback[] = [];

  /**
   * Initialize WebSocket connection
   */
  async connect(token?: string): Promise<void> {
    try {
      // Check if already connected
      if (this.isConnected && this.websocket && this.websocket.readyState === WebSocket.OPEN) {
        console.log('WebSocket already connected, skipping new connection');
        return;
      }

      // Disconnect any existing connection first
      if (this.websocket) {
        this.disconnect();
      }

      const accessToken = token || localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
      
      if (!accessToken) {
        throw new Error('No access token available');
      }

      const wsUrl = `ws://localhost:8000/ws/token-monitor?token=${accessToken}`;
      this.websocket = new WebSocket(wsUrl);

      this.websocket.onopen = () => {
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000;
      };

      this.websocket.onmessage = (event) => {
        try {
          const parsedMessage = JSON.parse(event.data);
          this.handleMessage(parsedMessage);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.websocket.onclose = (event) => {
        this.isConnected = false;
        this.handleDisconnection();
      };

      this.websocket.onerror = (error) => {
        this.handleError(error);
      };

    } catch (error) {
      this.handleError(error);
    }
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleMessage(message: TokenMessage): void {
    if (message.time_remaining_seconds !== undefined && 
        message.time_remaining_seconds < 120) {
      
      if (message.call_refresh) {
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
      
      if (!refreshToken || !accessToken) {
        this.logoutUser();
        return;
      }

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
        
        if (data.access_token) {
          localStorage.setItem('auth_token', data.access_token);
        }
        if (data.refresh_token) {
          localStorage.setItem('refresh_token', data.refresh_token);
        }

        this.tokenUpdateCallbacks.forEach(callback => {
          callback({
            call_refresh: false,
            time_remaining_seconds: 0,
            message: 'Token refreshed successfully'
          });
        });
      } else {
        this.handleRefreshError('API refresh failed');
        this.logoutUser();
      }
    } catch (error) {
      this.handleRefreshError(error instanceof Error ? error.message : 'Unknown error');
      this.logoutUser();
    }
  }

  /**
   * Handle refresh error
   */
  private handleRefreshError(message: string): void {
    this.errorCallbacks.forEach(callback => {
      callback({ call_refresh: false, time_remaining_seconds: 0, message });
    });
  }

  /**
   * Handle WebSocket errors
   */
  private handleError(error: any): void {
    this.errorCallbacks.forEach(callback => {
      callback(error);
    });
  }

  /**
   * Handle WebSocket disconnection
   */
  private handleDisconnection(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      setTimeout(() => {
        this.reconnectAttempts++;
        this.reconnectDelay *= 2;
        const token = this.getStoredToken();
        if (token && !this.isConnected) {
          this.connect(token);
        }
      }, this.reconnectDelay);
    } else {
      this.logoutUser();
    }
  }

  /**
   * Logout user when token is invalid
   */
  private logoutUser(): void {
    tokenManager.clearAuth();
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
      // Remove event listeners to prevent memory leaks
      this.websocket.onopen = null;
      this.websocket.onmessage = null;
      this.websocket.onclose = null;
      this.websocket.onerror = null;
      
      // Close the connection
      this.websocket.close();
      this.websocket = null;
    }
    this.isConnected = false;
    this.reconnectAttempts = 0;
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
   * Check if WebSocket is connected
   */
  getConnected(): boolean {
    return this.isConnected && this.websocket !== null && this.websocket.readyState === WebSocket.OPEN;
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
      readyState: this.websocket?.readyState || 3,
      url: this.websocket?.url || null,
      tokenAvailable: !!token,
      tokenLength: token?.length || 0
    };
  }
}

// Create singleton instance
const wsTokenManager = new WebSocketTokenManager();

export default wsTokenManager; 