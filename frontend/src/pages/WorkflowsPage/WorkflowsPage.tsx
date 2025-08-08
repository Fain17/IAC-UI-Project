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
  const [activeSubMenu, setActiveSubMenu] = useState<'list' | 'create'>('list');

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
        <Link to="/settings" className="nav-link">Settings</Link>
        
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
          </div>
        </div>
      </main>
    </div>
  );
};

export default WorkflowsPage; 