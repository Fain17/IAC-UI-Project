import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import tokenManager from '../../utils/tokenManager';
import WorkflowList from './components/WorkflowList';
import CreateWorkflow from './components/CreateWorkflow';
import './WorkflowsPage.css';

const WorkflowsPage: React.FC = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState<string>('');
  const [email, setEmail] = useState<string>('');
  const [activeSubMenu, setActiveSubMenu] = useState<'list' | 'create' | 'history' | 'automate' | 'config_docker_mapping' | 'config_custom_mapping' | 'config_vault'>('list');

  useEffect(() => {
    const user = tokenManager.getUser();
    if (user) {
      setUsername(user.username || '');
      setEmail(user.email || '');
    }
  }, []);

  const handleLogout = async () => {
    await tokenManager.logout();
  };

  const handleProfileClick = () => {
    navigate('/admin-profile');
  };

  // Use username if available, otherwise use email for avatar initial
  const displayName = username || email;
  const initial = displayName ? displayName[0].toUpperCase() : '?';

  return (
    <div>
      <aside className="sidebar">
        <h2>Navigation</h2>
        <Link to="/home" className="nav-link">Home</Link>
        <Link to="/workflows" className="nav-link active">Workflows</Link>
        <Link to="/configurations" className="nav-link">Configurations</Link>
        <Link to="/settings" className="nav-link">User Settings</Link>
        
        <div className="settings-submenu">
          <div className="submenu-header">Workflows</div>
          <button 
            className={`submenu-item ${activeSubMenu === 'list' ? 'active' : ''}`}
            onClick={() => setActiveSubMenu('list')}
          >
            📋 List Workflows
          </button>
          <button 
            className={`submenu-item ${activeSubMenu === 'create' ? 'active' : ''}`}
            onClick={() => setActiveSubMenu('create')}
          >
            ➕ Create Workflow
          </button>
          <button 
            className={`submenu-item ${activeSubMenu === 'history' ? 'active' : ''}`}
            onClick={() => setActiveSubMenu('history')}
          >
            🕘 Workflow History
          </button>
          <button 
            className={`submenu-item ${activeSubMenu === 'automate' ? 'active' : ''}`}
            onClick={() => setActiveSubMenu('automate')}
          >
            🤖 Automate Workflows
          </button>
        </div>
        
        <button onClick={handleLogout} className="logout-button">
          Logout
        </button>
      </aside>
      <main className="content">
        <div className="profile-container" onClick={handleProfileClick}>
          <div className="avatar">{initial}</div>
          {username && <div className="name">{username}</div>}
          {email && <div className="email">{email}</div>}
        </div>
        <div className="workflows-content">
          <div className="workflows-header">
            <h1>Workflows</h1>
          </div>
          <div className="workflows-body">
            {activeSubMenu === 'list' && <WorkflowList />}
            {activeSubMenu === 'create' && <CreateWorkflow />}
            {activeSubMenu === 'history' && (
              <div>
                <h2>Workflow History</h2>
                <p>Showing recent workflow executions (dummy data).</p>
                <ul>
                  <li>2025-08-09 12:00 — Deployment Workflow — completed_with_skips</li>
                  <li>2025-08-08 16:20 — Data Pipeline — failed</li>
                  <li>2025-08-07 09:45 — Nightly Backup — completed</li>
                </ul>
              </div>
            )}
            {activeSubMenu === 'automate' && (
              <div>
                <h2>Automate Workflows</h2>
                <p>Create schedules and triggers (dummy UI).</p>
                <ul>
                  <li>Cron: 0 2 * * * — Nightly Backup</li>
                  <li>On Git push — Build and Deploy</li>
                </ul>
              </div>
            )}
            {activeSubMenu === 'config_docker_mapping' && (
              <div>
                <h2>Docker Execution Mapping</h2>
                <p>Configure container images per script type (dummy).</p>
                <ul>
                  <li>python → python:3.11-slim</li>
                  <li>nodejs → node:20-alpine</li>
                </ul>
              </div>
            )}
            {activeSubMenu === 'config_custom_mapping' && (
              <div>
                <h2>Custom Mapping</h2>
                <p>Define custom run commands and environments (dummy).</p>
              </div>
            )}
            {activeSubMenu === 'config_vault' && (
              <div>
                <h2>Vault Config (HashiCorp)</h2>
                <p>Set Vault address, token, and KV paths (dummy).</p>
                <ul>
                  <li>Address: https://vault.example.com</li>
                  <li>KV Mount: secret/</li>
                </ul>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default WorkflowsPage; 