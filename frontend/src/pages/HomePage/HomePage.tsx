import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import tokenManager from '../../utils/tokenManager';
import './HomePage.css';

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState<string>('');
  const [email, setEmail] = useState<string>('');

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
        <Link to="/home" className="nav-link active">Home</Link>
        <Link to="/workflows" className="nav-link">Workflows</Link>
        <Link to="/settings" className="nav-link">Settings</Link>
        <button onClick={handleLogout} className="logout-button">
          Logout
        </button>
      </aside>
      <main className="content">
        <div className="profile-container" onClick={handleProfileClick} onMouseEnter={(e) => {
          e.currentTarget.querySelector('div')!.style.transform = 'scale(1.05)';
        }} onMouseLeave={(e) => {
          e.currentTarget.querySelector('div')!.style.transform = 'scale(1)';
        }}>
          <div className="avatar">{initial}</div>
          {username && <div className="name">{username}</div>}
          {email && <div className="email">{email}</div>}
        </div>
        <div className="dashboard-content">
          <h1>Welcome to the Dashboard</h1>
          <div className="dashboard-cards">
            <div className="dashboard-card">
              <h3>🔄 Workflows</h3>
              <p>Create and manage automated workflows</p>
              <Link to="/workflows" className="card-link">Go to Workflows</Link>
            </div>
            <div className="dashboard-card">
              <h3>👥 User Management</h3>
              <p>Manage users, roles, and permissions</p>
              <Link to="/settings" className="card-link">Go to Settings</Link>
            </div>
            <div className="dashboard-card">
              <h3>👤 Profile</h3>
              <p>View and edit your profile information</p>
              <Link to="/admin-profile" className="card-link">View Profile</Link>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default HomePage;
