import React, { useState, useEffect } from 'react';
import tokenManager from '../utils/tokenManager';
import wsTokenManager from '../utils/websocketTokenManager';

interface TokenStatus {
  timeRemaining: number;
  shouldRefresh: boolean;
}

const WebSocketStatus: React.FC = () => {
  const [isWebSocketConnected, setIsWebSocketConnected] = useState(false);
  const [tokenStatus, setTokenStatus] = useState<TokenStatus | null>(null);
  const [showDetails, setShowDetails] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<any>(null);
  const [testing, setTesting] = useState(false);

  useEffect(() => {
    // Check WebSocket connection status
    const checkConnection = () => {
      setIsWebSocketConnected(tokenManager.isWebSocketConnected());
      
      // Get detailed connection status including token from localStorage
      const status = wsTokenManager.getConnectionStatus();
      const tokenFromStorage = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
      setConnectionStatus({
        ...status,
        tokenAvailable: !!tokenFromStorage,
        tokenLength: tokenFromStorage?.length || 0
      });
    };

    // Listen for token status updates
    const handleTokenStatusUpdate = (event: CustomEvent) => {
      setTokenStatus(event.detail);
    };

    // Initial check
    checkConnection();

    // Set up periodic checks
    const interval = setInterval(checkConnection, 5000);

    // Listen for token status events
    window.addEventListener('tokenStatusUpdate', handleTokenStatusUpdate as EventListener);

    return () => {
      clearInterval(interval);
      window.removeEventListener('tokenStatusUpdate', handleTokenStatusUpdate as EventListener);
    };
  }, []);

  const handleTestConnection = async () => {
    setTesting(true);
    try {
      const result = await wsTokenManager.testConnection();
      console.log('Connection test result:', result);
      alert(result.success ? '✅ Connection test successful!' : `❌ Connection test failed: ${result.error}`);
    } catch (error) {
      console.error('Test connection error:', error);
      alert('❌ Connection test error: ' + error);
    } finally {
      setTesting(false);
    }
  };

  const formatTime = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const getStatusColor = (): string => {
    if (!isWebSocketConnected) return '#ff6b6b'; // Red for disconnected
    if (tokenStatus?.shouldRefresh) return '#ffa726'; // Orange for needs refresh
    return '#66bb6a'; // Green for connected
  };

  const getStatusText = (): string => {
    if (!isWebSocketConnected) return 'WebSocket Disconnected';
    if (tokenStatus?.shouldRefresh) return 'Token Refresh Needed';
    return 'WebSocket Connected';
  };

  const getReadyStateText = (state: number): string => {
    switch (state) {
      case 0: return 'CONNECTING';
      case 1: return 'OPEN';
      case 2: return 'CLOSING';
      case 3: return 'CLOSED';
      default: return 'UNKNOWN';
    }
  };

  if (!showDetails) {
    return (
      <div 
        style={{
          position: 'fixed',
          bottom: '20px',
          right: '20px',
          backgroundColor: getStatusColor(),
          color: 'white',
          padding: '8px 12px',
          borderRadius: '20px',
          fontSize: '12px',
          cursor: 'pointer',
          zIndex: 1000,
          boxShadow: '0 2px 8px rgba(0,0,0,0.2)'
        }}
        onClick={() => setShowDetails(true)}
        title="Click to see details"
      >
        {getStatusText()}
      </div>
    );
  }

  return (
    <div 
      style={{
        position: 'fixed',
        bottom: '20px',
        right: '20px',
        backgroundColor: '#2c3e50',
        color: 'white',
        padding: '16px',
        borderRadius: '8px',
        fontSize: '14px',
        zIndex: 1000,
        boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
        minWidth: '280px',
        maxHeight: '400px',
        overflowY: 'auto'
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <h4 style={{ margin: 0 }}>Connection Status</h4>
        <button 
          onClick={() => setShowDetails(false)}
          style={{
            background: 'none',
            border: 'none',
            color: 'white',
            cursor: 'pointer',
            fontSize: '18px'
          }}
        >
          ×
        </button>
      </div>
      
      <div style={{ marginBottom: '8px' }}>
        <strong>WebSocket:</strong> 
        <span style={{ 
          color: isWebSocketConnected ? '#66bb6a' : '#ff6b6b',
          marginLeft: '8px'
        }}>
          {isWebSocketConnected ? 'Connected' : 'Disconnected'}
        </span>
      </div>

      {connectionStatus && (
        <div style={{ marginBottom: '8px', fontSize: '12px' }}>
          <div><strong>Ready State:</strong> {getReadyStateText(connectionStatus.readyState)}</div>
          <div><strong>Token Available:</strong> {connectionStatus.tokenAvailable ? 'Yes' : 'No'}</div>
          {connectionStatus.tokenAvailable && (
            <div><strong>Token Length:</strong> {connectionStatus.tokenLength} characters</div>
          )}
          {connectionStatus.url && (
            <div><strong>URL:</strong> {connectionStatus.url}</div>
          )}
        </div>
      )}

      {tokenStatus && (
        <div style={{ marginBottom: '8px' }}>
          <strong>Token Status:</strong>
          <div style={{ marginLeft: '12px', fontSize: '12px' }}>
            <div>Time Remaining: {formatTime(tokenStatus.timeRemaining)}</div>
            <div>Needs Refresh: {tokenStatus.shouldRefresh ? 'Yes' : 'No'}</div>
          </div>
        </div>
      )}

      <div style={{ marginTop: '12px', fontSize: '12px', opacity: 0.8 }}>
        <button 
          onClick={handleTestConnection}
          disabled={testing}
          style={{
            backgroundColor: '#e74c3c',
            color: 'white',
            border: 'none',
            padding: '6px 12px',
            borderRadius: '4px',
            cursor: testing ? 'not-allowed' : 'pointer',
            fontSize: '12px',
            marginRight: '8px',
            marginBottom: '8px',
            opacity: testing ? 0.6 : 1
          }}
        >
          {testing ? 'Testing...' : 'Test Connection'}
        </button>
        
        <button 
          onClick={async () => {
            try {
              await wsTokenManager.connect();
              console.log('Manual WebSocket connection attempt completed');
            } catch (error) {
              console.error('Manual connection error:', error);
            }
          }}
          style={{
            backgroundColor: '#9b59b6',
            color: 'white',
            border: 'none',
            padding: '6px 12px',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '12px',
            marginRight: '8px',
            marginBottom: '8px'
          }}
        >
          Connect WebSocket
        </button>
        
        <button 
          onClick={() => tokenManager.setWebSocketEnabled(!isWebSocketConnected)}
          style={{
            backgroundColor: isWebSocketConnected ? '#ff6b6b' : '#66bb6a',
            color: 'white',
            border: 'none',
            padding: '6px 12px',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '12px',
            marginRight: '8px',
            marginBottom: '8px'
          }}
        >
          {isWebSocketConnected ? 'Disable' : 'Enable'} WebSocket
        </button>
        
        <button 
          onClick={() => {
            const token = tokenManager.getToken();
            if (token) {
              console.log('Current token:', token.substring(0, 20) + '...');
              console.log('Token length:', token.length);
            } else {
              console.log('No token available');
            }
          }}
          style={{
            backgroundColor: '#3498db',
            color: 'white',
            border: 'none',
            padding: '6px 12px',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '12px',
            marginBottom: '8px'
          }}
        >
          Debug Token
        </button>

        <button 
          onClick={() => {
            wsTokenManager.testAllMessageTypes();
          }}
          style={{
            backgroundColor: '#f39c12',
            color: 'white',
            border: 'none',
            padding: '6px 12px',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '12px',
            marginBottom: '8px'
          }}
        >
          Test Messages
        </button>

        <button 
          onClick={() => {
            wsTokenManager.sendTestMessage('token_status', {
              time_remaining_seconds: 60,
              should_refresh: true
            });
          }}
          style={{
            backgroundColor: '#e67e22',
            color: 'white',
            border: 'none',
            padding: '6px 12px',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '12px',
            marginBottom: '8px'
          }}
        >
          Test Token Status
        </button>
      </div>
    </div>
  );
};

export default WebSocketStatus; 