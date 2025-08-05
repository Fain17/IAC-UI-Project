import { useState, useEffect, useCallback } from 'react';
import multiUserWebSocketManager from '../utils/multiUserWebSocketManager';

interface UseMultiUserWebSocketOptions {
  userId: string;
  token: string;
  onTokenUpdate?: (message: any, userId: string) => void;
  onError?: (error: any, userId: string) => void;
  autoConnect?: boolean;
}

interface ConnectionStatus {
  isConnected: boolean;
  readyState: number;
  reconnectAttempts: number;
  lastPing: number;
}

export const useMultiUserWebSocket = ({
  userId,
  token,
  onTokenUpdate,
  onError,
  autoConnect = true
}: UseMultiUserWebSocketOptions) => {
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);

  // Connect user to WebSocket
  const connect = useCallback(async () => {
    if (!userId || !token) {
      console.warn('Cannot connect: missing userId or token');
      return false;
    }

    setIsConnecting(true);
    try {
      const success = await multiUserWebSocketManager.connectUser(userId, token);
      if (success) {
        console.log(`✅ Successfully initiated connection for user ${userId}`);
      } else {
        console.error(`❌ Failed to connect user ${userId}`);
      }
      return success;
    } catch (error) {
      console.error(`❌ Error connecting user ${userId}:`, error);
      return false;
    } finally {
      setIsConnecting(false);
    }
  }, [userId, token]);

  // Disconnect user from WebSocket
  const disconnect = useCallback(() => {
    multiUserWebSocketManager.disconnectUser(userId);
  }, [userId]);

  // Send message to user's WebSocket
  const sendMessage = useCallback((message: any) => {
    multiUserWebSocketManager.sendMessage(userId, message);
  }, [userId]);

  // Check connection status
  const checkStatus = useCallback(() => {
    const status = multiUserWebSocketManager.getUserConnectionStatus(userId);
    setConnectionStatus(status);
    return status;
  }, [userId]);

  // Auto-connect on mount if enabled
  useEffect(() => {
    if (autoConnect && userId && token) {
      connect();
    }
  }, [autoConnect, userId, token, connect]);

  // Set up status checking
  useEffect(() => {
    const interval = setInterval(checkStatus, 2000);
    return () => clearInterval(interval);
  }, [checkStatus]);

  // Set up callbacks
  useEffect(() => {
    if (onTokenUpdate) {
      multiUserWebSocketManager.onTokenUpdate(onTokenUpdate);
    }
    if (onError) {
      multiUserWebSocketManager.onError(onError);
    }

    return () => {
      // Note: We don't remove callbacks here as they might be used by other users
      // The manager handles cleanup when destroyed
    };
  }, [onTokenUpdate, onError]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      // Don't disconnect on unmount as other components might be using the same user
      // The manager will handle cleanup when the app is destroyed
    };
  }, []);

  return {
    connect,
    disconnect,
    sendMessage,
    connectionStatus,
    isConnecting,
    isConnected: connectionStatus?.isConnected || false,
    checkStatus
  };
};

// Hook for managing multiple users
export const useMultiUserWebSocketManager = () => {
  const [connectedUsers, setConnectedUsers] = useState<string[]>([]);

  useEffect(() => {
    const updateConnectedUsers = () => {
      setConnectedUsers(multiUserWebSocketManager.getConnectedUsers());
    };

    // Update immediately
    updateConnectedUsers();

    // Update every 5 seconds
    const interval = setInterval(updateConnectedUsers, 5000);

    return () => clearInterval(interval);
  }, []);

  const connectUser = useCallback(async (userId: string, token: string) => {
    return await multiUserWebSocketManager.connectUser(userId, token);
  }, []);

  const disconnectUser = useCallback((userId: string) => {
    multiUserWebSocketManager.disconnectUser(userId);
  }, []);

  const disconnectAll = useCallback(() => {
    multiUserWebSocketManager.disconnectAll();
  }, []);

  const isUserConnected = useCallback((userId: string) => {
    return multiUserWebSocketManager.isUserConnected(userId);
  }, []);

  const getUserStatus = useCallback((userId: string) => {
    return multiUserWebSocketManager.getUserConnectionStatus(userId);
  }, []);

  return {
    connectedUsers,
    connectUser,
    disconnectUser,
    disconnectAll,
    isUserConnected,
    getUserStatus
  };
}; 