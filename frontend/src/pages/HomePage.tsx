import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { getMappings, createMapping, deleteMapping, runLaunchUpdate } from '../api';
import AddMappingForm from '../components/AddMappingForm';
import MappingList from '../components/MappingList';
import LaunchRunner from '../components/LaunchRunner';
import axios from 'axios';

export interface Mappings {
  [key: string]: string;
}

const sidebarStyle: React.CSSProperties = {
  width: '200px',
  height: '100vh',
  position: 'fixed',
  top: 0,
  left: 0,
  background: '#f8f9fa',
  borderRight: '1px solid #dee2e6',
  display: 'flex',
  flexDirection: 'column',
  padding: '2rem 1rem',
  boxSizing: 'border-box',
  zIndex: 1000
};

const contentStyle: React.CSSProperties = {
  marginLeft: '220px',
  padding: '20px',
  fontFamily: 'Arial',
  minHeight: '100vh',
  position: 'relative'
};

const profileContainerStyle: React.CSSProperties = {
  position: 'absolute',
  top: 24,
  right: 10,
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  zIndex: 1100,
  cursor: 'pointer'
};

const avatarStyle: React.CSSProperties = {
  width: 48,
  height: 48,
  borderRadius: '50%',
  background: '#007bff',
  color: '#fff',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  fontSize: 24,
  fontWeight: 700,
  userSelect: 'none',
  boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
  transition: 'transform 0.2s ease'
};

const nameStyle: React.CSSProperties = {
  marginTop: 8,
  fontWeight: 600,
  color: '#343a40',
  fontSize: '1rem',
  textAlign: 'center',
  maxWidth: 120,
  wordBreak: 'break-all'
};

const emailStyle: React.CSSProperties = {
  marginTop: 2,
  color: '#555',
  fontSize: '0.95em',
  textAlign: 'center',
  maxWidth: 140,
  wordBreak: 'break-all'
};

const HomePage: React.FC = () => {
  const [mappings, setMappings] = useState<Mappings>({});
  const navigate = useNavigate();
  const [username, setUsername] = useState<string>('');
  const [email, setEmail] = useState<string>('');

  useEffect(() => {
    setUsername(localStorage.getItem('username') || '');
    setEmail(localStorage.getItem('userEmail') || '');
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
    try {
      await axios.post('http://localhost:8000/auth/logout', {}, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`
        }
      });
    } catch (err) {
      // Optionally handle error (e.g., token already invalid)
    }
    localStorage.clear();
    navigate('/login');
  };

  const handleProfileClick = () => {
    navigate('/admin-profile');
  };

  // Use username if available, otherwise use email for avatar initial
  const displayName = username || email;
  const initial = displayName ? displayName[0].toUpperCase() : '?';

  return (
    <div>
      <aside style={sidebarStyle}>
        <h2 style={{ marginBottom: '2rem', fontSize: '1.2rem', color: '#343a40' }}>Menu</h2>
        <Link to="/settings" style={{ marginBottom: '1rem', textDecoration: 'none', color: '#007bff', fontWeight: 500 }}>Settings</Link>
        <button onClick={handleLogout} style={{ background: '#dc3545', color: 'white', border: 'none', padding: '0.5rem 1rem', borderRadius: '5px', cursor: 'pointer', marginTop: 'auto' }}>
          Logout
        </button>
      </aside>
      <main style={contentStyle}>
        <div style={profileContainerStyle} onClick={handleProfileClick} onMouseEnter={(e) => {
          e.currentTarget.querySelector('div')!.style.transform = 'scale(1.05)';
        }} onMouseLeave={(e) => {
          e.currentTarget.querySelector('div')!.style.transform = 'scale(1)';
        }}>
          <div style={avatarStyle}>{initial}</div>
          {username && <div style={nameStyle}>{username}</div>}
          {email && <div style={emailStyle}>{email}</div>}
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