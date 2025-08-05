import React, { useState } from 'react';
import { useMultiUserWebSocketManager } from '../hooks/useMultiUserWebSocket';

const MultiUserWebSocketStatus: React.FC = () => {
  const [showDetails, setShowDetails] = useState(false);
  const { connectedUsers, disconnectAll, getUserStatus } = useMultiUserWebSocketManager();

  const getReadyStateText = (state: number): string => {
    switch (state) {
      case 0: return 'CONNECTING';
      case 1: return 'OPEN';
      case 2: return 'CLOSING';
      case 3: return 'CLOSED';
      default: return 'UNKNOWN';
    }
  };

  const getStatusColor = (): string => {
    if (connectedUsers.length === 0) return '#ff6b6b'; // Red for no connections
    if (connectedUsers.length === 1) return '#66bb6a'; // Green for single connection
    return '#ffa726'; // Orange for multiple connections
  };

  const getStatusText = (): string => {
    if (connectedUsers.length === 0) return 'No Users Connected';
    if (connectedUsers.length === 1) return '1 User Connected';
    return `${connectedUsers.length} Users Connected`;
  };

  if (!showDetails) {
    return (
      <div 
        style={{
          position: 'fixed',
          bottom: '20px',
          left: '20px',
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
        title="Click to see multi-user details"
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
        left: '20px',
        backgroundColor: '#2c3e50',
        color: 'white',
        padding: '16px',
        borderRadius: '8px',
        fontSize: '14px',
        zIndex: 1000,
        boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
        minWidth: '300px',
        maxHeight: '400px',
        overflowY: 'auto'
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <h4 style={{ margin: 0 }}>Multi-User WebSocket Status</h4>
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
      
      <div style={{ marginBottom: '12px' }}>
        <strong>Connected Users:</strong> {connectedUsers.length}
      </div>

      {connectedUsers.length > 0 && (
        <div style={{ marginBottom: '12px' }}>
          <strong>User Details:</strong>
          {connectedUsers.map((userId) => {
            const status = getUserStatus(userId);
            return (
              <div key={userId} style={{ 
                marginLeft: '12px', 
                fontSize: '12px', 
                marginTop: '8px',
                padding: '8px',
                backgroundColor: 'rgba(255,255,255,0.1)',
                borderRadius: '4px'
              }}>
                <div><strong>User ID:</strong> {userId}</div>
                <div><strong>Status:</strong> {status?.isConnected ? 'Connected' : 'Disconnected'}</div>
                <div><strong>Ready State:</strong> {getReadyStateText(status?.readyState || 3)}</div>
                <div><strong>Reconnect Attempts:</strong> {status?.reconnectAttempts || 0}</div>
                <div><strong>Last Ping:</strong> {status?.lastPing ? new Date(status.lastPing).toLocaleTimeString() : 'Never'}</div>
              </div>
            );
          })}
        </div>
      )}

      <div style={{ marginTop: '12px', fontSize: '12px', opacity: 0.8 }}>
        <button 
          onClick={() => {
            disconnectAll();
            console.log('Disconnected all users');
          }}
          style={{
            backgroundColor: '#e74c3c',
            color: 'white',
            border: 'none',
            padding: '8px 16px',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '12px',
            marginRight: '8px'
          }}
        >
          Disconnect All Users
        </button>
        
        <button 
          onClick={() => {
            console.log('Connected users:', connectedUsers);
            connectedUsers.forEach(userId => {
              const status = getUserStatus(userId);
              console.log(`User ${userId}:`, status);
            });
          }}
          style={{
            backgroundColor: '#3498db',
            color: 'white',
            border: 'none',
            padding: '8px 16px',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '12px'
          }}
        >
          Debug All Users
        </button>
      </div>
    </div>
  );
};

export default MultiUserWebSocketStatus; 