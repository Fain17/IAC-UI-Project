import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import HomePage from './pages/HomePage';
import SettingsPage from './pages/SettingsPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import AdminProfilePage from './pages/AdminProfilePage';
import WorkflowsPage from './pages/WorkflowsPage';
import ProtectedRoute from './components/ProtectedRoute';
import ForgotPasswordPage from './pages/ForgotPasswordPage';
import ResetPasswordPage from './pages/ResetPasswordPage';
import TokenExpiryNotification from './components/TokenExpiryNotification';
import WebSocketStatus from './components/WebSocketStatus';
import tokenManager from './utils/tokenManager';

const App: React.FC = () => {
  useEffect(() => {
    console.log('🚀 Initializing application...');
    
    // Check if user is already logged in
    const existingToken = tokenManager.getToken();
    if (existingToken) {
      console.log('🔍 Found existing token, initializing WebSocket connection...');
    } else {
      console.log('🔍 No existing token found, user needs to login');
    }
    
    // Initialize token checking on app startup
    tokenManager.initializeTokenChecking();
    
    console.log('✅ Application initialization complete');
  }, []);

  return (
    <Router>
      <TokenExpiryNotification />
      <WebSocketStatus />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route 
          path="/home" 
          element={
            <ProtectedRoute>
              <HomePage />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/settings" 
          element={
            <ProtectedRoute>
              <SettingsPage />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/admin-profile" 
          element={
            <ProtectedRoute>
              <AdminProfilePage />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/workflows" 
          element={
            <ProtectedRoute>
              <WorkflowsPage />
            </ProtectedRoute>
          } 
        />
      </Routes>
    </Router>
  );
};

export default App; 