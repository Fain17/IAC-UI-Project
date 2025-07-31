interface UserData {
    username?: string;
    email?: string;
    isAdmin?: boolean;
}

class TokenManager {
    private tokenKey: string;
    private refreshTokenKey: string;
    private userKey: string;
    private checkInterval: NodeJS.Timeout | null;
    private apiBaseUrl: string;

    constructor() {
        this.tokenKey = 'auth_token';
        this.refreshTokenKey = 'refresh_token';
        this.userKey = 'user_data';
        this.checkInterval = null;
        this.apiBaseUrl = 'http://localhost:8000';
    }

    // Store tokens and user data
    setTokens(accessToken: string, refreshToken: string, userData: UserData): void {
        localStorage.setItem(this.tokenKey, accessToken);
        localStorage.setItem(this.refreshTokenKey, refreshToken);
        localStorage.setItem(this.userKey, JSON.stringify(userData));
        this.startTokenCheck();
    }

    // Store token and user data (backward compatibility)
    setToken(token: string, userData: UserData): void {
        localStorage.setItem(this.tokenKey, token);
        localStorage.setItem(this.userKey, JSON.stringify(userData));
        this.startTokenCheck();
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
        this.stopTokenCheck();
        
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

    // Check token validity with backend and attempt refresh if needed
    async checkTokenValidity(): Promise<boolean> {
        const token = this.getToken();
        if (!token) {
            this.clearAuth();
            return false;
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}/auth/verify-token`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                
                console.log('Token check response:', {
                    valid: data.valid,
                    timeRemaining: data.time_remaining_seconds,
                    willExpireSoon: data.time_remaining_seconds <= 30
                });
                
                // Check if token is valid
                if (!data.valid) {
                    console.log('Token is invalid, attempting refresh...');
                    const refreshSuccess = await this.refreshAccessToken();
                    if (!refreshSuccess) {
                        console.log('Token refresh failed, redirecting to login...');
                        this.clearAuth();
                        return false;
                    }
                    return true;
                }
                
                // Auto-refresh when token is about to expire (below 60 seconds for 15-min tokens)
                if (data.time_remaining_seconds <= 60 && data.time_remaining_seconds > 0) {
                    console.log(`Token expiring soon (${data.time_remaining_seconds}s remaining), auto-refreshing...`);
                    const refreshSuccess = await this.refreshAccessToken();
                    if (!refreshSuccess) {
                        console.log('Auto-refresh failed, but token still valid, continuing...');
                        // Don't logout yet, let the user continue until token actually expires
                    } else {
                        console.log('Token auto-refreshed successfully - new token stored');
                    }
                    return true;
                }
                
                // Only logout if token has actually expired (0 or negative seconds)
                if (data.time_remaining_seconds <= 0) {
                    console.log('Token has expired, attempting refresh...');
                    const refreshSuccess = await this.refreshAccessToken();
                    if (!refreshSuccess) {
                        console.log('Token refresh failed, redirecting to login...');
                        this.clearAuth();
                        return false;
                    }
                    return true;
                }
                
                return true;
            } else if (response.status === 401) {
                // Token is invalid, try to refresh
                console.log('Token invalid (401), attempting refresh...');
                const refreshSuccess = await this.refreshAccessToken();
                if (!refreshSuccess) {
                    console.log('Token refresh failed, clearing auth...');
                    this.clearAuth();
                    return false;
                }
                return true;
            } else {
                // Other error - don't logout immediately, just log the error
                console.log('Token check failed, status:', response.status);
                console.log('Response headers:', response.headers);
                try {
                    const errorText = await response.text();
                    console.log('Error response body:', errorText);
                } catch (e) {
                    console.log('Could not read error response body');
                }
                // Don't logout on other errors, just return true to keep the session
                return true;
            }
        } catch (error) {
            console.error('Error checking token validity:', error);
            // On network error, keep the token but don't clear auth
            return true;
        }
    }

    // Start periodic token checking
    startTokenCheck(): void {
        // Don't start if already running
        if (this.checkInterval) {
            return;
        }
        
        // Only start if we have a token
        if (!this.getToken()) {
            return;
        }
        
        console.log('Starting token validity checks...');
        // Check every 30 seconds for efficient auto-refresh
        this.checkInterval = setInterval(async () => {
            await this.checkTokenValidity();
        }, 30000);
    }

    // Stop periodic token checking
    stopTokenCheck(): void {
        if (this.checkInterval) {
            clearInterval(this.checkInterval);
            this.checkInterval = null;
            console.log('Stopped token validity checks');
        }
    }

    // Initialize token checking for existing sessions (call on app startup)
    initializeTokenChecking(): void {
        const token = this.getToken();
        if (token) {
            console.log('Found existing token, starting validity checks...');
            this.startTokenCheck();
        } else {
            console.log('No token found, skipping validity checks');
        }
    }

    // Check if token needs auto-refresh (for external components)
    async checkIfAutoRefreshNeeded(): Promise<{ needsRefresh: boolean; timeRemaining: number }> {
        const token = this.getToken();
        if (!token) {
            return { needsRefresh: false, timeRemaining: 0 };
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}/auth/verify-token`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                return {
                    needsRefresh: data.time_remaining_seconds <= 60 && data.time_remaining_seconds > 0,
                    timeRemaining: data.time_remaining_seconds
                };
            }
        } catch (error) {
            console.error('Error checking auto-refresh status:', error);
        }

        return { needsRefresh: false, timeRemaining: 0 };
    }

    // Logout user and call backend logout endpoint
    async logout(): Promise<void> {
        try {
            const token = this.getToken();
            if (token) {
                await fetch(`${this.apiBaseUrl}/auth/logout`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                });
            }
        } catch (error) {
            console.error('Error calling logout endpoint:', error);
        } finally {
            this.clearAuth();
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