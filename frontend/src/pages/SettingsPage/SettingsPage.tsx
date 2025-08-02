import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import tokenManager from '../../utils/tokenManager';
import './SettingsPage.css';

interface User {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  role: string;
  group: string;
  created_at: string;
}

interface UserGroup {
  id: number;
  name: string;
  description: string;
  member_count: number;
  created_at: string;
}

interface Role {
  id: number;
  name: string;
  description: string;
  permissions: string[];
  user_count: number;
  created_at: string;
}

interface Permission {
  id: number;
  name: string;
  description: string;
  category: string;
  is_active: boolean;
}

const SettingsPage: React.FC = () => {
  // State for current user
  const [userUsername, setUserUsername] = useState<string>('');
  const [userEmail, setUserEmail] = useState<string>('');
  const [userIsAdmin, setUserIsAdmin] = useState<boolean>(false);

  // State for active submenu
  const [activeSubMenu, setActiveSubMenu] = useState<string>('general');

  // State for general settings
  const [notifications, setNotifications] = useState(true);
  const [saved, setSaved] = useState(false);

  // State for user management
  const [users, setUsers] = useState<User[]>([]);
  const [userGroups, setUserGroups] = useState<UserGroup[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // State for forms
  const [showUserForm, setShowUserForm] = useState(false);
  const [showGroupForm, setShowGroupForm] = useState(false);
  const [showRoleForm, setShowRoleForm] = useState(false);

  const navigate = useNavigate();

  useEffect(() => {
    const user = tokenManager.getUser();
    if (user) {
      setUserUsername(user.username || '');
      setUserEmail(user.email || '');
      setUserIsAdmin(user.isAdmin || false);
    }
    
    // Load data based on active submenu
    if (activeSubMenu === 'users') {
      loadUsers();
    } else if (activeSubMenu === 'groups') {
      loadUserGroups();
    } else if (activeSubMenu === 'roles') {
      loadRoles();
    } else if (activeSubMenu === 'permissions') {
      loadPermissions();
    }
  }, [activeSubMenu]);

  // Mock data loading functions (replace with actual API calls)
  const loadUsers = async () => {
    setLoading(true);
    try {
      // Mock data - replace with actual API call
      const mockUsers: User[] = [
        { id: 1, username: 'admin', email: 'admin@example.com', is_active: true, role: 'Admin', group: 'Administrators', created_at: '2024-01-01' },
        { id: 2, username: 'user1', email: 'user1@example.com', is_active: true, role: 'User', group: 'Developers', created_at: '2024-01-15' },
        { id: 3, username: 'user2', email: 'user2@example.com', is_active: false, role: 'User', group: 'Testers', created_at: '2024-02-01' },
      ];
      setUsers(mockUsers);
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to load users' });
    } finally {
      setLoading(false);
    }
  };

  const loadUserGroups = async () => {
    setLoading(true);
    try {
      // Mock data - replace with actual API call
      const mockGroups: UserGroup[] = [
        { id: 1, name: 'Administrators', description: 'System administrators', member_count: 2, created_at: '2024-01-01' },
        { id: 2, name: 'Developers', description: 'Development team', member_count: 5, created_at: '2024-01-15' },
        { id: 3, name: 'Testers', description: 'QA and testing team', member_count: 3, created_at: '2024-02-01' },
      ];
      setUserGroups(mockGroups);
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to load user groups' });
    } finally {
      setLoading(false);
    }
  };

  const loadRoles = async () => {
    setLoading(true);
    try {
      // Mock data - replace with actual API call
      const mockRoles: Role[] = [
        { id: 1, name: 'Admin', description: 'Full system access', permissions: ['read', 'write', 'delete', 'admin'], user_count: 2, created_at: '2024-01-01' },
        { id: 2, name: 'User', description: 'Standard user access', permissions: ['read', 'write'], user_count: 8, created_at: '2024-01-15' },
        { id: 3, name: 'Viewer', description: 'Read-only access', permissions: ['read'], user_count: 3, created_at: '2024-02-01' },
      ];
      setRoles(mockRoles);
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to load roles' });
    } finally {
      setLoading(false);
    }
  };

  const loadPermissions = async () => {
    setLoading(true);
    try {
      // Mock data - replace with actual API call
      const mockPermissions: Permission[] = [
        { id: 1, name: 'read', description: 'Read access to resources', category: 'Access Control', is_active: true },
        { id: 2, name: 'write', description: 'Write access to resources', category: 'Access Control', is_active: true },
        { id: 3, name: 'delete', description: 'Delete access to resources', category: 'Access Control', is_active: true },
        { id: 4, name: 'admin', description: 'Administrative access', category: 'System', is_active: true },
        { id: 5, name: 'workflow_manage', description: 'Manage workflows', category: 'Workflows', is_active: true },
        { id: 6, name: 'user_manage', description: 'Manage users', category: 'Users', is_active: true },
      ];
      setPermissions(mockPermissions);
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to load permissions' });
    } finally {
      setLoading(false);
    }
  };

  const handleGeneralSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleLogout = async () => {
    await tokenManager.logout();
  };

  const displayName = userUsername || userEmail;
  const initial = displayName ? displayName[0].toUpperCase() : '?';

  const renderContent = () => {
    switch (activeSubMenu) {
      case 'general':
        return (
          <div className="settings-section">
            <h2>General Settings</h2>
            <form onSubmit={handleGeneralSubmit} className="settings-form">
              <div className="form-group">
                <label htmlFor="notifications">Notifications</label>
                <div className="checkbox-group">
                  <input
                    id="notifications"
                    type="checkbox"
                    checked={notifications}
                    onChange={e => setNotifications(e.target.checked)}
                  />
                  <label htmlFor="notifications">Enable email notifications</label>
                </div>
              </div>
              <button type="submit" className="submit-button">Save Settings</button>
              {saved && <div className="success-message">Settings saved!</div>}
            </form>
          </div>
        );

      case 'users':
        return (
          <div className="settings-section">
            <div className="section-header">
              <h2>User Management</h2>
              {userIsAdmin && (
                <button 
                  onClick={() => setShowUserForm(true)}
                  className="create-button"
                >
                  ➕ Add User
                </button>
              )}
            </div>
            
            {loading ? (
              <div className="loading">Loading users...</div>
            ) : (
              <div className="data-table">
                <table>
                  <thead>
                    <tr>
                      <th>Username</th>
                      <th>Email</th>
                      <th>Role</th>
                      <th>Group</th>
                      <th>Status</th>
                      <th>Created</th>
                      {userIsAdmin && <th>Actions</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((user) => (
                      <tr key={user.id}>
                        <td>{user.username}</td>
                        <td>{user.email}</td>
                        <td><span className={`role-badge ${user.role.toLowerCase()}`}>{user.role}</span></td>
                        <td>{user.group}</td>
                        <td>
                          <span className={`status-badge ${user.is_active ? 'active' : 'inactive'}`}>
                            {user.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                        <td>{new Date(user.created_at).toLocaleDateString()}</td>
                        {userIsAdmin && (
                          <td>
                            <button className="action-button edit">Edit</button>
                            <button className="action-button delete">Delete</button>
                          </td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        );

      case 'groups':
        return (
          <div className="settings-section">
            <div className="section-header">
              <h2>User Groups</h2>
              {userIsAdmin && (
                <button 
                  onClick={() => setShowGroupForm(true)}
                  className="create-button"
                >
                  ➕ Add Group
                </button>
              )}
            </div>
            
            {loading ? (
              <div className="loading">Loading groups...</div>
            ) : (
              <div className="data-table">
                <table>
                  <thead>
                    <tr>
                      <th>Group Name</th>
                      <th>Description</th>
                      <th>Members</th>
                      <th>Created</th>
                      {userIsAdmin && <th>Actions</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {userGroups.map((group) => (
                      <tr key={group.id}>
                        <td>{group.name}</td>
                        <td>{group.description}</td>
                        <td>{group.member_count}</td>
                        <td>{new Date(group.created_at).toLocaleDateString()}</td>
                        {userIsAdmin && (
                          <td>
                            <button className="action-button edit">Edit</button>
                            <button className="action-button delete">Delete</button>
                          </td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        );

      case 'roles':
        return (
          <div className="settings-section">
            <div className="section-header">
              <h2>Roles & Permissions</h2>
              {userIsAdmin && (
                <button 
                  onClick={() => setShowRoleForm(true)}
                  className="create-button"
                >
                  ➕ Add Role
                </button>
              )}
            </div>
            
            {loading ? (
              <div className="loading">Loading roles...</div>
            ) : (
              <div className="data-table">
                <table>
                  <thead>
                    <tr>
                      <th>Role Name</th>
                      <th>Description</th>
                      <th>Permissions</th>
                      <th>Users</th>
                      <th>Created</th>
                      {userIsAdmin && <th>Actions</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {roles.map((role) => (
                      <tr key={role.id}>
                        <td>{role.name}</td>
                        <td>{role.description}</td>
                        <td>
                          <div className="permissions-list">
                            {role.permissions.map((permission, index) => (
                              <span key={index} className="permission-badge">{permission}</span>
                            ))}
                          </div>
                        </td>
                        <td>{role.user_count}</td>
                        <td>{new Date(role.created_at).toLocaleDateString()}</td>
                        {userIsAdmin && (
                          <td>
                            <button className="action-button edit">Edit</button>
                            <button className="action-button delete">Delete</button>
                          </td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        );

      case 'permissions':
        return (
          <div className="settings-section">
            <div className="section-header">
              <h2>System Permissions</h2>
            </div>
            
            {loading ? (
              <div className="loading">Loading permissions...</div>
            ) : (
              <div className="data-table">
                <table>
                  <thead>
                    <tr>
                      <th>Permission</th>
                      <th>Description</th>
                      <th>Category</th>
                      <th>Status</th>
                      {userIsAdmin && <th>Actions</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {permissions.map((permission) => (
                      <tr key={permission.id}>
                        <td>{permission.name}</td>
                        <td>{permission.description}</td>
                        <td><span className="category-badge">{permission.category}</span></td>
                        <td>
                          <span className={`status-badge ${permission.is_active ? 'active' : 'inactive'}`}>
                            {permission.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                        {userIsAdmin && (
                          <td>
                            <button className="action-button edit">Edit</button>
                          </td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div>
      {/* Sidebar */}
      <aside className="sidebar">
        <h2>Navigation</h2>
        <Link to="/home" className="nav-link">Home</Link>
        <Link to="/settings" className="nav-link active">Settings</Link>
        <Link to="/workflows" className="nav-link">Workflows</Link>
        
        <div className="settings-submenu">
          <div className="submenu-header">Settings</div>
          <button 
            className={`submenu-item ${activeSubMenu === 'general' ? 'active' : ''}`}
            onClick={() => setActiveSubMenu('general')}
          >
            ⚙️ General
          </button>
          <button 
            className={`submenu-item ${activeSubMenu === 'users' ? 'active' : ''}`}
            onClick={() => setActiveSubMenu('users')}
          >
            👥 Users
          </button>
          <button 
            className={`submenu-item ${activeSubMenu === 'groups' ? 'active' : ''}`}
            onClick={() => setActiveSubMenu('groups')}
          >
            🏷️ User Groups
          </button>
          <button 
            className={`submenu-item ${activeSubMenu === 'roles' ? 'active' : ''}`}
            onClick={() => setActiveSubMenu('roles')}
          >
            🔐 Roles
          </button>
          <button 
            className={`submenu-item ${activeSubMenu === 'permissions' ? 'active' : ''}`}
            onClick={() => setActiveSubMenu('permissions')}
          >
            🛡️ Permissions
          </button>
        </div>
        
        <button onClick={handleLogout} className="logout-button">
          Logout
        </button>
      </aside>

      {/* Main Content */}
      <main className="content">
        {/* Profile Container */}
        <div className="profile-container" onClick={() => navigate('/admin-profile')}>
          <div className="avatar">{initial}</div>
          {userUsername && <div className="name">{userUsername}</div>}
          {userEmail && <div className="email">{userEmail}</div>}
        </div>

        <div className="settings-content">
          <h1>Settings</h1>
          
          {/* Message Display */}
          {message && (
            <div className={`message ${message.type}-message`}>
              {message.text}
            </div>
          )}
          
          {renderContent()}
        </div>
      </main>
    </div>
  );
};

export default SettingsPage; 