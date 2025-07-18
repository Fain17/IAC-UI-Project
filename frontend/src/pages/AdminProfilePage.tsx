import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

interface AdminInfo {
  username: string;
  email: string;
  isAdmin: boolean;
}

const AdminProfilePage: React.FC = () => {
  const [adminInfo, setAdminInfo] = useState<AdminInfo>({
    username: '',
    email: '',
    isAdmin: false
  });
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [showPasswordReset, setShowPasswordReset] = useState(false);
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteData, setDeleteData] = useState({ password: '' });
  const [deleteError, setDeleteError] = useState('');
  const [deleteLoading, setDeleteLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    // Load admin info from localStorage
    const username = localStorage.getItem('username') || '';
    const email = localStorage.getItem('userEmail') || '';
    const isAdmin = localStorage.getItem('isAdmin') === 'true';
    setAdminInfo({
      username,
      email,
      isAdmin
    });
  }, []);

  const handlePasswordReset = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsLoading(true);
    setMessage('');

    if (passwordData.newPassword !== passwordData.confirmPassword) {
      setMessage('New passwords do not match');
      setIsLoading(false);
      return;
    }

    try {
      await axios.post('http://localhost:8000/auth/change-password', {
        current_password: passwordData.currentPassword,
        new_password: passwordData.newPassword,
        confirm_password: passwordData.confirmPassword
      }, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`
        }
      });
      setMessage('Password updated successfully. Please log in again.');
      setTimeout(() => {
        localStorage.clear();
        navigate('/login');
      }, 1500);
    } catch (err: any) {
      setMessage(err.response?.data?.message || 'Failed to update password');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteAccount = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setDeleteLoading(true);
    setDeleteError('');
    try {
      await axios.delete('http://localhost:8000/auth/delete-account', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`
        },
        data: {
            password: deleteData.password
        }
      });
      localStorage.clear();
      navigate('/login');
    } catch (err: any) {
      setDeleteError(err.response?.data?.message || 'Failed to delete account');
    } finally {
      setDeleteLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await axios.post('http://localhost:8000/auth/logout', {}, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`
        }
      });
    } catch (err) {
      // Optionally handle error
    }
    localStorage.clear();
    navigate('/login');
  };

  return (
    <>
      <button
        onClick={() => navigate(-1)}
        style={{
          position: 'fixed',
          top: 24,
          left: 24,
          background: '#f8f9fa',
          border: '1px solid #dee2e6',
          borderRadius: '50%',
          width: 36,
          height: 36,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          fontSize: 18,
          boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
          zIndex: 2000
        }}
        aria-label="Back"
        title="Back"
      >
        ←
      </button>
      <div style={{ maxWidth: 600, margin: '50px auto', background: '#fff', padding: '2rem', borderRadius: 8, boxShadow: '0 0 10px rgba(0,0,0,0.05)', position: 'relative' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
          <h1>Admin Profile</h1>
          <button onClick={handleLogout} style={{ background: '#dc3545', color: 'white', border: 'none', padding: '0.5rem 1rem', borderRadius: '5px', cursor: 'pointer' }}>
            Logout
          </button>
        </div>

        <div style={{ marginBottom: '2rem' }}>
          <h2>Profile Information</h2>
          <div style={{ background: '#f8f9fa', padding: '1rem', borderRadius: '5px', marginTop: '1rem' }}>
            <div style={{ marginBottom: '1rem' }}>
              <strong>Username:</strong> {adminInfo.username}
            </div>
            <div style={{ marginBottom: '1rem' }}>
              <strong>Email:</strong> {adminInfo.email}
            </div>
            <div>
              <strong>Role:</strong> <span style={{ background: adminInfo.isAdmin ? '#007bff' : '#6c757d', color: 'white', padding: '0.2rem 0.5rem', borderRadius: '3px', fontSize: '0.9em' }}>
                {adminInfo.isAdmin ? 'Admin' : 'User'}
              </span>
            </div>
          </div>
        </div>

        <div style={{ marginBottom: '2rem' }}>
          <h2>Password Management</h2>
          {!showPasswordReset ? (
            <button 
              onClick={() => setShowPasswordReset(true)}
              style={{ background: '#007bff', color: 'white', border: 'none', padding: '0.6rem 1.2rem', borderRadius: '5px', cursor: 'pointer', marginRight: '1rem' }}
            >
              Reset Password
            </button>
          ) : (
            <form onSubmit={handlePasswordReset} style={{ background: '#f8f9fa', padding: '1rem', borderRadius: '5px', marginTop: '1rem' }}>
              <div style={{ marginBottom: '1rem' }}>
                <label htmlFor="currentPassword">Current Password</label>
                <input
                  id="currentPassword"
                  type="password"
                  value={passwordData.currentPassword}
                  onChange={e => setPasswordData({...passwordData, currentPassword: e.target.value})}
                  required
                  style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem', border: '1px solid #ced4da', borderRadius: '5px' }}
                />
              </div>
              <div style={{ marginBottom: '1rem' }}>
                <label htmlFor="newPassword">New Password</label>
                <input
                  id="newPassword"
                  type="password"
                  value={passwordData.newPassword}
                  onChange={e => setPasswordData({...passwordData, newPassword: e.target.value})}
                  required
                  style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem', border: '1px solid #ced4da', borderRadius: '5px' }}
                />
              </div>
              <div style={{ marginBottom: '1rem' }}>
                <label htmlFor="confirmPassword">Confirm New Password</label>
                <input
                  id="confirmPassword"
                  type="password"
                  value={passwordData.confirmPassword}
                  onChange={e => setPasswordData({...passwordData, confirmPassword: e.target.value})}
                  required
                  style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem', border: '1px solid #ced4da', borderRadius: '5px' }}
                />
              </div>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <button 
                  type="submit" 
                  disabled={isLoading}
                  style={{ background: '#28a745', color: 'white', border: 'none', padding: '0.6rem 1.2rem', borderRadius: '5px', cursor: 'pointer' }}
                >
                  {isLoading ? 'Updating...' : 'Update Password'}
                </button>
                <button 
                  type="button"
                  onClick={() => {
                    setShowPasswordReset(false);
                    setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' });
                    setMessage('');
                  }}
                  style={{ background: '#6c757d', color: 'white', border: 'none', padding: '0.6rem 1.2rem', borderRadius: '5px', cursor: 'pointer' }}
                >
                  Cancel
                </button>
              </div>
            </form>
          )}
          {/* Delete Account Button */}
          <button
            onClick={() => setShowDeleteModal(true)}
            style={{ background: '#dc3545', color: 'white', border: 'none', padding: '0.6rem 1.2rem', borderRadius: '5px', cursor: 'pointer', marginTop: '1.5rem' }}
          >
            Delete Account
          </button>
        </div>

        {showDeleteModal && (
          <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            width: '100vw',
            height: '100vh',
            background: 'rgba(0,0,0,0.25)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 3000
          }}>
            <form onSubmit={handleDeleteAccount} style={{ background: '#fff', padding: '2rem', borderRadius: 8, boxShadow: '0 0 10px rgba(0,0,0,0.15)', minWidth: 320 }}>
              <h3 style={{ marginBottom: '1rem' }}>Confirm Account Deletion</h3>
              <div style={{ marginBottom: '1rem' }}>
                <label htmlFor="delete-password">Password</label>
                <input
                  id="delete-password"
                  type="password"
                  value={deleteData.password}
                  onChange={e => setDeleteData({ password: e.target.value })}
                  required
                  style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem', border: '1px solid #ced4da', borderRadius: '5px' }}
                />
              </div>
              {deleteError && <div style={{ color: 'red', marginBottom: '1rem' }}>{deleteError}</div>}
              <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                <button
                  type="submit"
                  disabled={deleteLoading}
                  style={{ background: '#dc3545', color: 'white', border: 'none', padding: '0.6rem 1.2rem', borderRadius: '5px', cursor: 'pointer' }}
                >
                  {deleteLoading ? 'Deleting...' : 'Delete'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowDeleteModal(false);
                    setDeleteData({ password: '' });
                    setDeleteError('');
                  }}
                  style={{ background: '#6c757d', color: 'white', border: 'none', padding: '0.6rem 1.2rem', borderRadius: '5px', cursor: 'pointer' }}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}
        {message && (
          <div style={{ 
            padding: '1rem', 
            borderRadius: '5px', 
            marginTop: '1rem',
            background: message.includes('success') ? '#d4edda' : '#f8d7da',
            color: message.includes('success') ? '#155724' : '#721c24',
            border: `1px solid ${message.includes('success') ? '#c3e6cb' : '#f5c6cb'}`
          }}>
            {message}
          </div>
        )}
      </div>
    </>
  );
};

export default AdminProfilePage; 