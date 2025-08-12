import React, { useMemo, useState } from 'react';
import { useLocation } from 'react-router-dom';
import './ConfigurationsPage.css';

const ConfigurationsPage: React.FC = () => {
  const location = useLocation();

  const active = useMemo<'docker' | 'custom' | 'vault'>(() => {
    if (location.pathname.startsWith('/configurations/custom')) return 'custom';
    if (location.pathname.startsWith('/configurations/vault')) return 'vault';
    return 'docker';
  }, [location.pathname]);

  return (
    <div>
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
    </div>
  );
};

export default ConfigurationsPage; 