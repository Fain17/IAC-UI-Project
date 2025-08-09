import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import tokenManager from '../../utils/tokenManager';
import './ConfigurationsPage.css';

const ConfigurationsPage: React.FC = () => {
  const navigate = useNavigate();
  const [active, setActive] = useState<'docker' | 'custom' | 'vault'>('docker');

  const handleLogout = async () => {
    await tokenManager.logout();
  };

  return (
    <div>
      <aside className="sidebar">
        <h2>Navigation</h2>
        <Link to="/home" className="nav-link">Home</Link>
        <Link to="/workflows" className="nav-link">Workflows</Link>
        <Link to="/configurations" className="nav-link active">Configurations</Link>
        <Link to="/settings" className="nav-link">User Settings</Link>

        <div className="settings-submenu">
          <div className="submenu-header">Configurations</div>
          <div className="submenu-subheader">Mapping</div>
          <button className={`submenu-item ${active === 'docker' ? 'active' : ''}`} onClick={() => setActive('docker')}>
            🐳 Docker Execution Mapping
          </button>
          <button className={`submenu-item ${active === 'custom' ? 'active' : ''}`} onClick={() => setActive('custom')}>
            🧩 Custom Mapping
          </button>
          <div className="submenu-subheader">Vault</div>
          <button className={`submenu-item ${active === 'vault' ? 'active' : ''}`} onClick={() => setActive('vault')}>
            🔐 Vault Config (HashiCorp)
          </button>
        </div>

        <button onClick={handleLogout} className="logout-button">
          Logout
        </button>
      </aside>

      <main className="content">
        <div className="workflows-content">
          <div className="workflows-header">
            <h1>Configurations</h1>
          </div>
          <div className="workflows-body">
            {active === 'docker' && (
              <div>
                <h2>Docker Execution Mapping</h2>
                <ul>
                  <li>python → python:3.11-slim</li>
                  <li>nodejs → node:20-alpine</li>
                </ul>
              </div>
            )}
            {active === 'custom' && (
              <div>
                <h2>Custom Mapping</h2>
                <p>Define custom run commands and environments (dummy).</p>
              </div>
            )}
            {active === 'vault' && (
              <div>
                <h2>Vault Config (HashiCorp)</h2>
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

export default ConfigurationsPage; 