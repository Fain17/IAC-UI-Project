import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import tokenManager from '../utils/tokenManager';

const Sidebar: React.FC = () => {
  const location = useLocation();
  const isActive = (path: string) => location.pathname === path || location.pathname.startsWith(path + '/');

  const [openWorkflows, setOpenWorkflows] = useState<boolean>(location.pathname.startsWith('/workflows'));
  const [openConfigurations, setOpenConfigurations] = useState<boolean>(location.pathname.startsWith('/configurations'));
  const [openSettings, setOpenSettings] = useState<boolean>(location.pathname.startsWith('/settings'));

  const handleLogout = async () => {
    await tokenManager.logout();
  };

  return (
    <aside className="sidebar scrollable">
      <h2>Navigation</h2>
      <Link to="/home" className={`nav-link ${isActive('/home') ? 'active' : ''}`}>Home</Link>

      <button className={`nav-link dropdown ${isActive('/workflows') ? 'active' : ''}`} onClick={() => setOpenWorkflows(!openWorkflows)}>
        Workflows {openWorkflows ? '▾' : '▸'}
      </button>
      {openWorkflows && (
        <div className="settings-submenu">
          <div className="submenu-header">Workflows</div>
          <Link to="/workflows/list" className={`submenu-item ${location.pathname.startsWith('/workflows/list') ? 'active' : ''}`}>📋 List Workflows</Link>
          <Link to="/workflows/create" className={`submenu-item ${location.pathname.startsWith('/workflows/create') ? 'active' : ''}`}>➕ Create Workflow</Link>
          <Link to="/workflows/assign" className={`submenu-item ${location.pathname.startsWith('/workflows/assign') ? 'active' : ''}`}>🔗 Assign Workflows</Link>
          <Link to="/workflows/history" className={`submenu-item ${location.pathname.startsWith('/workflows/history') ? 'active' : ''}`}>🕘 Workflow History</Link>
          <Link to="/workflows/automate" className={`submenu-item ${location.pathname.startsWith('/workflows/automate') ? 'active' : ''}`}>🤖 Automate Workflows</Link>
        </div>
      )}

      <button className={`nav-link dropdown ${isActive('/configurations') ? 'active' : ''}`} onClick={() => setOpenConfigurations(!openConfigurations)}>
        Configurations {openConfigurations ? '▾' : '▸'}
      </button>
      {openConfigurations && (
        <div className="settings-submenu">
          <div className="submenu-header">Configurations</div>
          <div className="submenu-subheader">Mapping</div>
          <Link to="/configurations/docker" className={`submenu-item ${location.pathname.startsWith('/configurations/docker') ? 'active' : ''}`}>🐳 Docker Execution Mapping</Link>
          <Link to="/configurations/custom" className={`submenu-item ${location.pathname.startsWith('/configurations/custom') ? 'active' : ''}`}>🧩 Custom Mapping</Link>
          <div className="submenu-subheader">Vault</div>
          <Link to="/configurations/vault" className={`submenu-item ${location.pathname.startsWith('/configurations/vault') ? 'active' : ''}`}>🔐 Vault Config</Link>
        </div>
      )}

      <button className={`nav-link dropdown ${isActive('/settings') ? 'active' : ''}`} onClick={() => setOpenSettings(!openSettings)}>
        User Settings {openSettings ? '▾' : '▸'}
      </button>
      {openSettings && (
        <div className="settings-submenu">
          <div className="submenu-header">User Settings</div>
          <Link to="/settings/general" className={`submenu-item ${location.pathname.startsWith('/settings/general') ? 'active' : ''}`}>⚙️ General</Link>
          <Link to="/settings/users" className={`submenu-item ${location.pathname.startsWith('/settings/users') ? 'active' : ''}`}>👥 Users</Link>
          <Link to="/settings/groups" className={`submenu-item ${location.pathname.startsWith('/settings/groups') ? 'active' : ''}`}>🏷️ User Groups</Link>
          <Link to="/settings/roles" className={`submenu-item ${location.pathname.startsWith('/settings/roles') ? 'active' : ''}`}>🔐 Roles</Link>
        </div>
      )}

      <button onClick={handleLogout} className="logout-button">Logout</button>
    </aside>
  );
};

export default Sidebar; 