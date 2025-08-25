import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import tokenManager from '../../utils/tokenManager';

import './AdminProfilePage.css';

interface AdminInfo {
  username: string;
  email: string;
  role: string;
}

const AdminProfilePage: React.FC = () => {
  const [adminInfo, setAdminInfo] = useState<AdminInfo>({
    username: '',
    email: '',
    role: ''
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
  const [editingUsername, setEditingUsername] = useState(false);
  const [newUsername, setNewUsername] = useState('');
  const [usernameError, setUsernameError] = useState('');
  const navigate = useNavigate();





  useEffect(() => {
    const loadUserInfo = async () => {
      try {
        // Load user info from TokenManager
        const user = tokenManager.getUser();
        if (user) {
          // Fetch role from API
          const response = await axios.get('http://localhost:8000/workflow/debug/user-role', {
            headers: {
              Authorization: `Bearer ${tokenManager.getToken()}`
            }
          });
          
          if (response.data.success) {
            setAdminInfo({
              username: user.username || '',
              email: user.email || '',
              role: response.data.user_role
            });
            setNewUsername(user.username || '');
          }
        }
      } catch (error) {
        console.error('Failed to load user info:', error);
        // Set default role if API fails
        const user = tokenManager.getUser();
        if (user) {
          setAdminInfo({
            username: user.username || '',
            email: user.email || '',
            role: 'User'
          });
          setNewUsername(user.username || '');
        }
      }
    };

    loadUserInfo();
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
          Authorization: `Bearer ${tokenManager.getToken()}`
        }
      });
      setMessage('Password updated successfully. Please log in again.');
      setTimeout(() => {
        tokenManager.clearAuth();
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
          Authorization: `Bearer ${tokenManager.getToken()}`
        },
        data: {
            password: deleteData.password
        }
      });
      tokenManager.clearAuth();
    } catch (err: any) {
      setDeleteError(err.response?.data?.message || 'Failed to delete account');
    } finally {
      setDeleteLoading(false);
    }
  };

  const handleLogout = async () => {
    await tokenManager.logout();
  };

  const handleUsernameEdit = () => {
    setEditingUsername(true);
    setUsernameError('');
  };

  const handleUsernameSave = async () => {
    setUsernameError('');
    if (!newUsername.trim()) {
      setUsernameError('Username cannot be empty');
      return;
    }
    try {
      await axios.put('http://localhost:8000/auth/edit-username', {
        new_username: newUsername
      }, {
        headers: {
          Authorization: `Bearer ${tokenManager.getToken()}`
        }
      });
      setAdminInfo(info => ({ ...info, username: newUsername }));
      // Update user data in TokenManager
      const user = tokenManager.getUser();
      if (user) {
        tokenManager.setToken(tokenManager.getToken()!, {
          ...user,
          username: newUsername
        });
      }
      setEditingUsername(false);
    } catch (err: any) {
      setUsernameError(err.response?.data?.message || 'Failed to update username');
    }
  };

  return (
    <>
      <button
        onClick={() => navigate(-1)}
        className="back-button"
        aria-label="Back"
        title="Back"
      >
        ←
      </button>
      <div className="admin-profile-container">
        <div className="admin-profile-header">
          <h1>User Profile</h1>
          <button onClick={handleLogout} className="logout-button">
            Logout
          </button>
        </div>

        <div className="profile-section">
          <h2>Profile Information</h2>
          <div className="profile-info">
            <div className="info-row">
              <strong>Username:</strong>
              {editingUsername ? (
                <div className="username-edit">
                  <input
                    type="text"
                    value={newUsername}
                    onChange={e => setNewUsername(e.target.value)}
                    className="username-input"
                  />
                  <button onClick={handleUsernameSave} className="save-button">Save</button>
                  <button onClick={() => { setEditingUsername(false); setNewUsername(adminInfo.username); }} className="cancel-button">Cancel</button>
                </div>
              ) : (
                <>
                  <span>{adminInfo.username}</span>
                  <button onClick={handleUsernameEdit} className="edit-button">Edit</button>
                </>
              )}
            </div>
            {usernameError && <div className="error-message">{usernameError}</div>}
            <div className="info-row">
              <strong>Email:</strong> {adminInfo.email}
            </div>
            <div className="info-row">
              <strong>Role:</strong> <span style={{ 
                background: adminInfo.role === 'admin' ? '#007bff' : 
                           adminInfo.role === 'manager' ? '#28a745' : '#6c757d', 
                color: 'white', 
                padding: '0.2rem 0.5rem', 
                borderRadius: '3px', 
                fontSize: '0.9em' 
              }}>
                {adminInfo.role ? adminInfo.role.charAt(0).toUpperCase() + adminInfo.role.slice(1) : 'User'}
              </span>
            </div>

          </div>
        </div>

        <div className="action-section">
          <h3>Password Management</h3>
          {!showPasswordReset ? (
            <button 
              onClick={() => setShowPasswordReset(true)}
              className="submit-button"
            >
              Reset Password
            </button>
          ) : (
            <form onSubmit={handlePasswordReset} className="action-form">
              <div className="form-group">
                <label htmlFor="currentPassword">Current Password</label>
                <input
                  id="currentPassword"
                  type="password"
                  value={passwordData.currentPassword}
                  onChange={e => setPasswordData({...passwordData, currentPassword: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="newPassword">New Password</label>
                <input
                  id="newPassword"
                  type="password"
                  value={passwordData.newPassword}
                  onChange={e => setPasswordData({...passwordData, newPassword: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="confirmPassword">Confirm New Password</label>
                <input
                  id="confirmPassword"
                  type="password"
                  value={passwordData.confirmPassword}
                  onChange={e => setPasswordData({...passwordData, confirmPassword: e.target.value})}
                  required
                />
              </div>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <button 
                  type="submit" 
                  disabled={isLoading}
                  className="submit-button"
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
                  className="cancel-button"
                >
                  Cancel
                </button>
              </div>
            </form>
          )}
          {/* Delete Account Button */}
          <button
            onClick={() => setShowDeleteModal(true)}
            className="danger-button"
            style={{ marginTop: '1.5rem' }}
          >
            Delete Account
          </button>
        </div>

        {showDeleteModal && (
          <div className="modal-overlay">
            <form onSubmit={handleDeleteAccount} className="modal">
              <h3>Confirm Account Deletion</h3>
              <p>This action cannot be undone. Please enter your password to confirm.</p>
              <div className="form-group">
                <label htmlFor="delete-password">Password</label>
                <input
                  id="delete-password"
                  type="password"
                  value={deleteData.password}
                  onChange={e => setDeleteData({ password: e.target.value })}
                  required
                />
              </div>
              {deleteError && <div className="error-message">{deleteError}</div>}
              <div className="modal-buttons">
                <button
                  type="submit"
                  disabled={deleteLoading}
                  className="modal-button confirm"
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
                  className="modal-button cancel"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}
        {message && (
          <div className={`message ${message.includes('success') ? 'success-message' : 'error-message'}`}>
            {message}
          </div>
        )}
      </div>
    </>
  );
};

export default AdminProfilePage; 