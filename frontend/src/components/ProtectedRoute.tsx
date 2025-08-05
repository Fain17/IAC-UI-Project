import React from 'react';
import { Navigate } from 'react-router-dom';
import tokenManager from '../utils/tokenManager';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  // Check for JWT token using TokenManager
  const token = tokenManager.getToken();

  if (!token) {
    // Redirect to login if not authenticated
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

export default ProtectedRoute; 