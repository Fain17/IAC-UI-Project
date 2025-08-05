import wsTokenManager from './websocketTokenManager';

interface UserData {
    username?: string;
    email?: string;
    isAdmin?: boolean;
}

class TokenManager {
    private tokenKey: string;
    private refreshTokenKey: string;
    private userKey: string;
    private apiBaseUrl: string;

    constructor() {
        this.tokenKey = 'auth_token';
        this.refreshTokenKey = 'refresh_token';
        this.userKey = 'user_data';
        this.apiBaseUrl = 'http://localhost:8000';
    }

    // Store tokens and user data
    setTokens(accessToken: string, refreshToken: string, userData: UserData): void {
        localStorage.setItem(this.tokenKey, accessToken);
        localStorage.setItem(this.refreshTokenKey, refreshToken);
        localStorage.setItem(this.userKey, JSON.stringify(userData));
        
        // Connect WebSocket for token monitoring
        wsTokenManager.connect(accessToken);
    }

    // Store token and user data (backward compatibility)
    setToken(token: string, userData: UserData): void {
        localStorage.setItem(this.tokenKey, token);
        localStorage.setItem(this.userKey, JSON.stringify(userData));
        
        // Connect WebSocket for token monitoring
        wsTokenManager.connect(token);
    }

    // Get stored access token
    getToken(): string | null {
        return localStorage.getItem(this.tokenKey);
    }

    // Get stored refresh token
    getRefreshToken(): string | null {
        return localStorage.getItem(this.refreshTokenKey);
    }

    // Get stored user data
    getUser(): UserData | null {
        const userData = localStorage.getItem(this.userKey);
        return userData ? JSON.parse(userData) : null;
    }

    // Clear all auth data
    clearAuth(): void {
        localStorage.removeItem(this.tokenKey);
        localStorage.removeItem(this.refreshTokenKey);
        localStorage.removeItem(this.userKey);
        
        // Disconnect WebSocket
        wsTokenManager.disconnect();
        
        // Redirect to login page
        if (window.location.pathname !== '/login') {
            window.location.href = '/login';
        }
    }

    // Refresh access token using refresh token
    async refreshAccessToken(): Promise<boolean> {
        const token = this.getToken();
        if (!token) {
            this.clearAuth();
            return false;
        }
        
        const refreshToken = this.getRefreshToken();
        if (!refreshToken) {
            console.log('No refresh token available');
            return false;
        }

        try {
            console.log('Sending refresh token request...');
            const response = await fetch(`${this.apiBaseUrl}/auth/refresh-token`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    refresh_token: refreshToken
                })
            });

            if (response.ok) {
                const data = await response.json();
                const user = this.getUser();
                
                console.log('Refresh response received:', { 
                    hasAccessToken: !!data.access_token, 
                    hasRefreshToken: !!data.refresh_token 
                });
                
                // Update access token
                localStorage.setItem(this.tokenKey, data.access_token);
                
                // Update refresh token if new one provided
                if (data.refresh_token) {
                    localStorage.setItem(this.refreshTokenKey, data.refresh_token);
                }
                
                console.log('Access token refreshed successfully');
                return true;
            } else {
                console.log('Failed to refresh token, status:', response.status);
                try {
                    const errorText = await response.text();
                    console.log('Refresh error response:', errorText);
                } catch (e) {
                    console.log('Could not read refresh error response');
                }
                return false;
            }
        } catch (error) {
            console.error('Error refreshing token:', error);
            return false;
        }
    }

    // Initialize token checking on app startup
    initializeTokenChecking(): void {
        console.log('🚀 Initializing token checking...');
        
        const token = this.getToken();
        if (!token) {
            console.log('❌ No token found, skipping token checking initialization');
            return;
        }

        console.log('🔌 Attempting WebSocket connection for token monitoring...');
        wsTokenManager.connect(token).catch(error => {
            console.warn('⚠️ WebSocket connection failed:', error);
        });
    }

    // Check if WebSocket is connected
    isWebSocketConnected(): boolean {
        return wsTokenManager.getConnected();
    }

    // Logout user and call backend logout endpoint
    async logout(): Promise<void> {
        console.log('🚪 Starting logout process...');
        try {
            const token = this.getToken();
            if (token) {
                console.log('📡 Calling backend logout endpoint...');
                await fetch(`${this.apiBaseUrl}/auth/logout`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                });
                console.log('✅ Backend logout successful');
            }
        } catch (error) {
            console.error('❌ Error calling logout endpoint:', error);
        } finally {
            console.log('🔌 Disconnecting WebSocket and clearing auth data...');
            this.clearAuth();
            console.log('✅ Logout process complete');
        }
    }

    // Make authenticated requests with automatic token handling
    async authenticatedRequest(url: string, options: RequestInit = {}): Promise<Response> {
        const token = this.getToken();
        if (!token) {
            throw new Error('No authentication token available');
        }

        const response = await fetch(url, {
            ...options,
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
                ...options.headers
            }
        });

        if (response.status === 401) {
            // Token expired, try to refresh
            const refreshSuccess = await this.refreshAccessToken();
            if (!refreshSuccess) {
                this.clearAuth();
                throw new Error('Authentication failed');
            }

            // Retry request with new token
            const newToken = this.getToken();
            return fetch(url, {
                ...options,
                headers: {
                    'Authorization': `Bearer ${newToken}`,
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });
        }

        return response;
    }
}

// Global instance
const tokenManager = new TokenManager();

// Export for use in other modules
export default tokenManager; 