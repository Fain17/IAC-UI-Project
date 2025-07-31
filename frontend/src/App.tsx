import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import HomePage from './pages/HomePage';
import SettingsPage from './pages/SettingsPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import AdminProfilePage from './pages/AdminProfilePage';
import ProtectedRoute from './components/ProtectedRoute';
import ForgotPasswordPage from './pages/ForgotPasswordPage';
import ResetPasswordPage from './pages/ResetPasswordPage';
import TokenExpiryNotification from './components/TokenExpiryNotification';
import tokenManager from './utils/tokenManager';

const App: React.FC = () => {
  useEffect(() => {
    // Initialize token checking on app startup
    tokenManager.initializeTokenChecking();
  }, []);

  return (
    <Router>
      <TokenExpiryNotification />
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
      </Routes>
    </Router>
  );
};

export default App; 