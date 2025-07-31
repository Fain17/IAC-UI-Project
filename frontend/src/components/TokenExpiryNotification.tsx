import React, { useState, useEffect } from 'react';
import tokenManager from '../utils/tokenManager';

const TokenExpiryNotification: React.FC = () => {
  const [showNotification, setShowNotification] = useState(false);
  const [timeRemaining, setTimeRemaining] = useState(0);

  useEffect(() => {
    const checkTokenExpiry = async () => {
      // Only check if user is logged in
      const token = tokenManager.getToken();
      if (!token) {
        setShowNotification(false);
        return;
      }

      try {
        // Use TokenManager's method to check auto-refresh status
        const { needsRefresh, timeRemaining } = await tokenManager.checkIfAutoRefreshNeeded();
        
        // Only show notification if auto-refresh is needed and we're very close to expiry
        // This means the auto-refresh might have failed
        if (needsRefresh && timeRemaining <= 30) {
          setTimeRemaining(timeRemaining);
          setShowNotification(true);
        } else {
          setShowNotification(false);
        }
      } catch (error) {
        // Network error, hide notification and let TokenManager handle it
        setShowNotification(false);
      }
    };

    // Only start checking if user is logged in
    const token = tokenManager.getToken();
    if (!token) {
      return;
    }

    // Check every 30 seconds for notification display only
    const interval = setInterval(checkTokenExpiry, 30000);
    
    // Initial check
    checkTokenExpiry();

    return () => clearInterval(interval);
  }, []);

  const handleLogout = () => {
    tokenManager.logout();
  };

  if (!showNotification) {
    return null;
  }

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      zIndex: 1000
    }}>
      <div style={{
        backgroundColor: 'white',
        padding: '2rem',
        borderRadius: '8px',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
        maxWidth: '400px',
        textAlign: 'center'
      }}>
        <h3 style={{ margin: '0 0 1rem 0', color: '#e74c3c' }}>
          Auto-Refresh Failed
        </h3>
        <p style={{ margin: '0 0 1.5rem 0', color: '#666' }}>
          Automatic session refresh failed. Your session will expire in <strong>{timeRemaining}</strong> seconds.
        </p>
        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
          <button
            onClick={handleLogout}
            style={{
              padding: '0.75rem 1.5rem',
              backgroundColor: '#e74c3c',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            Logout Now
          </button>
        </div>
      </div>
    </div>
  );
};

export default TokenExpiryNotification; 