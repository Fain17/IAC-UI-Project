import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { getMappings, createMapping, deleteMapping, runLaunchUpdate } from '../../api';
import AddMappingForm from '../../components/AddMappingForm';
import MappingList from '../../components/MappingList';
import LaunchRunner from '../../components/LaunchRunner';
import tokenManager from '../../utils/tokenManager';
import './HomePage.css';

export interface Mappings {
  [key: string]: string;
}

const HomePage: React.FC = () => {
  const [mappings, setMappings] = useState<Mappings>({});
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

  const fetchMappings = async () => {
    const res = await getMappings();
    setMappings(res.data.mappings);
  };

  useEffect(() => {
    fetchMappings();
  }, []);

  const handleCreate = async (instance: string, lt: string) => {
    await createMapping(instance, lt);
    fetchMappings();
  };

  const handleDelete = async (instance: string) => {
    await deleteMapping(instance);
    fetchMappings();
  };

  const handleRun = async (instance: string, launch_template: string) => {
    const res = await runLaunchUpdate(instance, launch_template);
    return res.data;
  };

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
        <Link to="/settings" className="nav-link">Settings</Link>
        <Link to="/workflows" className="nav-link">Workflows</Link>
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
        <h1>EC2 Launch Manager</h1>
        <AddMappingForm onCreate={handleCreate} />
        <MappingList mappings={mappings} onDelete={handleDelete} />
        <hr />
        <LaunchRunner mappings={mappings} onRun={handleRun} />
      </main>
    </div>
  );
};

export default HomePage; 