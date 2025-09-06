import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import HomePage from './pages/HomePage';
import WorkflowsPage from './pages/WorkflowsPage/WorkflowsPage';
import WorkflowDetailsPage from './pages/WorkflowDetailsPage';
import SettingsPage from './pages/SettingsPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import AdminProfilePage from './pages/AdminProfilePage';
import ConfigurationsPage from './pages/ConfigurationsPage';
import DockerMappingsPage from './pages/DockerMappingsPage';
import ProtectedRoute from './components/ProtectedRoute';
import AppLayout from './components/AppLayout';
import ForgotPasswordPage from './pages/ForgotPasswordPage';
import ResetPasswordPage from './pages/ResetPasswordPage';
import TokenExpiryNotification from './components/TokenExpiryNotification';
import WebSocketStatus from './components/WebSocketStatus';
import tokenManager from './utils/tokenManager';
import AssignWorkflowsPage from './pages/AssignWorkflowsPage';

const App: React.FC = () => {
  useEffect(() => {
    console.log('🚀 Initializing application...');
    const existingToken = tokenManager.getToken();
    if (existingToken) {
      console.log('🔍 Found existing token, initializing WebSocket connection...');
    } else {
      console.log('🔍 No existing token found, user needs to login');
    }
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
              <AppLayout>
                <HomePage />
              </AppLayout>
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/workflows" 
          element={
            <ProtectedRoute>
              <AppLayout>
                <WorkflowsPage />
              </AppLayout>
            </ProtectedRoute>
          } 
        />
        <Route path="/workflows/list" element={<ProtectedRoute><AppLayout><WorkflowsPage /></AppLayout></ProtectedRoute>} />
        <Route path="/workflows/create" element={<ProtectedRoute><AppLayout><WorkflowsPage /></AppLayout></ProtectedRoute>} />
        <Route path="/workflows/history" element={<ProtectedRoute><AppLayout><WorkflowsPage /></AppLayout></ProtectedRoute>} />
        <Route path="/workflows/automate" element={<ProtectedRoute><AppLayout><WorkflowsPage /></AppLayout></ProtectedRoute>} />
        <Route 
          path="/workflows/:workflowId" 
          element={
            <ProtectedRoute>
              <AppLayout>
                <WorkflowDetailsPage />
              </AppLayout>
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/configurations" 
          element={
            <ProtectedRoute>
              <AppLayout>
                <ConfigurationsPage />
              </AppLayout>
            </ProtectedRoute>
          } 
        />
        <Route path="/configurations/custom" element={<ProtectedRoute><AppLayout><ConfigurationsPage /></AppLayout></ProtectedRoute>} />
        <Route path="/configurations/vault" element={<ProtectedRoute><AppLayout><ConfigurationsPage /></AppLayout></ProtectedRoute>} />
        <Route 
          path="/docker-mappings" 
          element={
            <ProtectedRoute>
              <AppLayout>
                <DockerMappingsPage />
              </AppLayout>
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/settings" 
          element={
            <ProtectedRoute>
              <AppLayout>
                <SettingsPage />
              </AppLayout>
            </ProtectedRoute>
          } 
        />
        <Route path="/settings/general" element={<ProtectedRoute><AppLayout><SettingsPage /></AppLayout></ProtectedRoute>} />
        <Route path="/settings/users" element={<ProtectedRoute><AppLayout><SettingsPage /></AppLayout></ProtectedRoute>} />
        <Route path="/settings/groups" element={<ProtectedRoute><AppLayout><SettingsPage /></AppLayout></ProtectedRoute>} />
        <Route path="/settings/roles" element={<ProtectedRoute><AppLayout><SettingsPage /></AppLayout></ProtectedRoute>} />
        <Route 
          path="/admin-profile" 
          element={
            <ProtectedRoute>
              <AppLayout>
                <AdminProfilePage />
              </AppLayout>
            </ProtectedRoute>
          } 
        />
        <Route
          path="/workflows/assign"
          element={
            <ProtectedRoute>
              <AppLayout>
                <AssignWorkflowsPage />
              </AppLayout>
            </ProtectedRoute>
          }
        />
      </Routes>
    </Router>
  );
};

export default App; 