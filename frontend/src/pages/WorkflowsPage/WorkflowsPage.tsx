import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import tokenManager from '../../utils/tokenManager';
import WorkflowList from './components/WorkflowList';
import CreateWorkflow from './components/CreateWorkflow';
import './WorkflowsPage.css';

type SubTab = 'list' | 'create' | 'history' | 'automate';

const WorkflowsPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [username, setUsername] = useState<string>('');
  const [email, setEmail] = useState<string>('');

  useEffect(() => {
    const user = tokenManager.getUser();
    if (user) {
      setUsername(user.username || '');
      setEmail(user.email || '');
    }
  }, []);

  const handleProfileClick = () => {
    navigate('/admin-profile');
  };

  const activeSubMenu: SubTab = useMemo(() => {
    if (location.pathname.startsWith('/workflows/create')) return 'create';
    if (location.pathname.startsWith('/workflows/history')) return 'history';
    if (location.pathname.startsWith('/workflows/automate')) return 'automate';
    return 'list';
  }, [location.pathname]);

  const displayName = username || email;
  const initial = displayName ? displayName[0].toUpperCase() : '?';

  return (
    <div>
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
        </div>
      </div>
    </div>
  );
};

export default WorkflowsPage; 