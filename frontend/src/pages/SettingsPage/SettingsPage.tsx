import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import tokenManager from '../../utils/tokenManager';
import { getAdminUsers, createAdminUser, getAdminUser, AdminUser, CreateUserRequest, AdminUsersResponse, updateUserPermissions as updateUserPermissionsAPI, UpdateUserPermissionsRequest, deleteUser, updateUserActiveStatus, getAllUsersPermissionsNew } from '../../api';
import './SettingsPage.css';

interface User {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
  updated_at: string;
  permission_level: string;
  groups: string[];
}

interface UserPermission {
  user_id: number;
  username: string;
  email: string;
  is_active: boolean;
  is_admin: boolean;
  permission_level: string;
  permission_created_at: string;
  permission_updated_at: string;
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
  const [showEditUserForm, setShowEditUserForm] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);

  const navigate = useNavigate();

  // Load users function with useCallback to prevent infinite re-renders
  const loadUsers = useCallback(async () => {
    setLoading(true);
    setMessage(null);
    try {
      console.log('🔄 Loading users from /admin/users...');
      const usersResponse = await getAdminUsers();
      console.log('✅ Users response:', usersResponse);
      
      // Handle the actual API response structure
      const usersData = usersResponse.data.users || usersResponse.data || [];
      console.log('📋 Users data:', usersData);
      
      // Get all users' permissions in a single call
      console.log('🔄 Loading all users permissions from /admin/users/permissions/all...');
      const permissionsResponse = await getAllUsersPermissionsNew();
      console.log('✅ Permissions response:', permissionsResponse);
      
      const allPermissions = permissionsResponse.data.user_permissions || [];
      console.log('📋 All permissions data:', allPermissions);
      
      // Create a map of user ID to permissions for quick lookup
      const permissionsMap = new Map(
        allPermissions.map((perm: UserPermission) => [perm.user_id, perm])
      );
      
      // Merge users with their permissions
      const usersWithPermissions = usersData.map((user: User) => {
        const userPermissions = permissionsMap.get(user.id);
        if (userPermissions) {
          return {
            ...user,
            permission_level: userPermissions.permission_level || 'viewer',
            is_active: userPermissions.is_active !== undefined ? userPermissions.is_active : user.is_active,
            is_admin: userPermissions.is_admin !== undefined ? userPermissions.is_admin : user.is_admin
          };
        }
        return user;
      });
      
      console.log('👥 Users with permissions:', usersWithPermissions);
      setUsers(usersWithPermissions);
    } catch (error: any) {
      console.error('❌ Error loading users:', error);
      console.error('❌ Error response:', error.response);
      console.error('❌ Error message:', error.message);
      
      const errorMessage = error.response?.data?.detail || 
                          error.response?.data?.message || 
                          error.message || 
                          'Failed to load users';
      
      setMessage({ type: 'error', text: 'Failed to load users: ' + errorMessage });
    } finally {
      setLoading(false);
    }
  }, []);

  // Load user groups function
  const loadUserGroups = useCallback(async () => {
    setLoading(true);
    try {
      // Mock data for now
      setUserGroups([
        { id: 1, name: 'Administrators', description: 'System administrators', member_count: 2, created_at: '2024-01-01' },
        { id: 2, name: 'Users', description: 'Regular users', member_count: 5, created_at: '2024-01-01' }
      ]);
    } catch (error: any) {
      setMessage({ type: 'error', text: 'Failed to load user groups: ' + error.message });
    } finally {
      setLoading(false);
    }
  }, []);

  // Load roles function
  const loadRoles = useCallback(async () => {
    setLoading(true);
    try {
      // Mock data for now
      setRoles([
        { id: 1, name: 'Admin', description: 'Full system access', permissions: ['read', 'write', 'delete'], user_count: 2, created_at: '2024-01-01' },
        { id: 2, name: 'User', description: 'Limited access', permissions: ['read'], user_count: 5, created_at: '2024-01-01' }
      ]);
    } catch (error: any) {
      setMessage({ type: 'error', text: 'Failed to load roles: ' + error.message });
    } finally {
      setLoading(false);
    }
  }, []);

  // Load permissions function
  const loadPermissions = useCallback(async () => {
    setLoading(true);
    try {
      // Mock data for now
      setPermissions([
        { id: 1, name: 'read', description: 'Read access', category: 'basic', is_active: true },
        { id: 2, name: 'write', description: 'Write access', category: 'basic', is_active: true },
        { id: 3, name: 'delete', description: 'Delete access', category: 'admin', is_active: true }
      ]);
    } catch (error: any) {
      setMessage({ type: 'error', text: 'Failed to load permissions: ' + error.message });
    } finally {
      setLoading(false);
    }
  }, []);

  // Initialize user data and load content based on active submenu
  useEffect(() => {
    const user = tokenManager.getUser();
    if (user) {
      setUserUsername(user.username || '');
      setUserEmail(user.email || '');
      setUserIsAdmin(user.isAdmin || false);
    }
  }, []);

  // Load data based on active submenu
  useEffect(() => {
    if (activeSubMenu === 'users') {
      loadUsers();
    } else if (activeSubMenu === 'groups') {
      loadUserGroups();
    } else if (activeSubMenu === 'roles') {
      loadRoles();
    } else if (activeSubMenu === 'permissions') {
      loadPermissions();
    }
  }, [activeSubMenu, loadUsers, loadUserGroups, loadRoles, loadPermissions]);

  const createUser = async (userData: CreateUserRequest) => {
    setLoading(true);
    try {
      await createAdminUser(userData);
      setMessage({ type: 'success', text: 'User created successfully!' });
      setShowUserForm(false);
      loadUsers(); // Refresh the user list
    } catch (error: any) {
      setMessage({ type: 'error', text: 'Failed to create user: ' + (error.response?.data?.detail || error.message) });
    } finally {
      setLoading(false);
    }
  };

  const handleEditUser = (user: User) => {
    setEditingUser(user);
    setShowEditUserForm(true);
  };

  const handleUpdateUserPermissions = async (userData: UpdateUserPermissionsRequest) => {
    if (!editingUser) return;
    
    setLoading(true);
    try {
      await updateUserPermissionsAPI(editingUser.id, userData);
      setMessage({ type: 'success', text: 'User permissions updated successfully!' });
      setShowEditUserForm(false);
      setEditingUser(null);
      loadUsers(); // Refresh the user list
    } catch (error: any) {
      setMessage({ type: 'error', text: 'Failed to update user permissions: ' + (error.response?.data?.detail || error.message) });
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteUser = async (user: User) => {
    // Confirm deletion
    if (!window.confirm(`Are you sure you want to delete user "${user.username}"? This action cannot be undone.`)) {
      return;
    }

    setLoading(true);
    try {
      await deleteUser(user.id);
      setMessage({ type: 'success', text: `User "${user.username}" deleted successfully!` });
      loadUsers(); // Refresh the user list
    } catch (error: any) {
      setMessage({ type: 'error', text: 'Failed to delete user: ' + (error.response?.data?.detail || error.message) });
    } finally {
      setLoading(false);
    }
  };

  const CreateUserForm: React.FC = () => {
    const [formData, setFormData] = useState<CreateUserRequest>({
      username: '',
      email: '',
      password: '',
      role: 'viewer',
      group: '',
      is_active: true
    });

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
      e.preventDefault();
      createUser(formData);
    };

    return (
      <div className="create-form-overlay">
        <div className="create-form">
          <div className="form-header">
            <h3>Create New User</h3>
            <button 
              onClick={() => setShowUserForm(false)}
              className="close-button"
            >
              ✕
            </button>
          </div>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="username">Username *</label>
              <input
                id="username"
                type="text"
                value={formData.username}
                onChange={(e) => setFormData({...formData, username: e.target.value})}
                placeholder="Enter username"
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="email">Email *</label>
              <input
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                placeholder="Enter email"
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="password">Password *</label>
              <input
                id="password"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
                placeholder="Enter password"
                required
              />
            </div>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="permission_level">Permission Level</label>
                <select
                  id="permission_level"
                  value={formData.role}
                  onChange={(e) => setFormData({...formData, role: e.target.value})}
                >
                  <option value="viewer">Viewer</option>
                  <option value="manager">Manager</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <div className="form-group">
                <label htmlFor="group">Group</label>
                <input
                  id="group"
                  type="text"
                  value={formData.group}
                  onChange={(e) => setFormData({...formData, group: e.target.value})}
                  placeholder="Enter group"
                />
              </div>
            </div>
            <div className="form-group">
              <label>
                <input
                  type="checkbox"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({...formData, is_active: e.target.checked})}
                />
                Active
              </label>
            </div>
            <div className="form-actions">
              <button type="submit" className="submit-button" disabled={loading}>
                {loading ? 'Creating...' : 'Create User'}
              </button>
              <button 
                type="button" 
                onClick={() => setShowUserForm(false)}
                className="cancel-button"
                disabled={loading}
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  const EditUserForm: React.FC = () => {
    const [formData, setFormData] = useState({
      permission_level: editingUser?.permission_level || 'viewer',
      is_active: editingUser?.is_active ?? true
    });

    const handleSubmit = async (e: React.FormEvent) => {
      e.preventDefault();
      if (!editingUser) return;

      setLoading(true);
      try {
        // Update permissions using PUT /admin/users/{user_id}/permissions
        await updateUserPermissionsAPI(editingUser.id, {
          permission_level: formData.permission_level
        });

        // Update active status using PATCH /admin/users/{user_id}/active-status
        await updateUserActiveStatus(editingUser.id, formData.is_active);

        setMessage({ type: 'success', text: 'User updated successfully!' });
        setShowEditUserForm(false);
        setEditingUser(null);
        loadUsers(); // Refresh the user list
      } catch (error: any) {
        setMessage({ type: 'error', text: 'Failed to update user: ' + (error.response?.data?.detail || error.message) });
      } finally {
        setLoading(false);
      }
    };

    return (
      <div className="create-form-overlay">
        <div className="create-form">
          <div className="form-header">
            <h3>Edit User: {editingUser?.username}</h3>
            <button 
              onClick={() => {
                setShowEditUserForm(false);
                setEditingUser(null);
              }}
              className="close-button"
            >
              ✕
            </button>
          </div>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="permission_level">Permission Level</label>
              <select
                id="permission_level"
                value={formData.permission_level}
                onChange={(e) => setFormData({...formData, permission_level: e.target.value})}
              >
                <option value="viewer">Viewer</option>
                <option value="manager">Manager</option>
                <option value="admin">Admin</option>
              </select>
            </div>
            <div className="form-group">
              <label>
                <input
                  type="checkbox"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({...formData, is_active: e.target.checked})}
                />
                Active
              </label>
            </div>
            <div className="form-actions">
              <button type="submit" className="submit-button" disabled={loading}>
                {loading ? 'Updating...' : 'Update User'}
              </button>
              <button 
                type="button" 
                onClick={() => {
                  setShowEditUserForm(false);
                  setEditingUser(null);
                }}
                className="cancel-button"
                disabled={loading}
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    );
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
    try {
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
                    {users && users.length > 0 ? (
                      users.map((user) => (
                        <tr key={user.id}>
                          <td>{user.username}</td>
                          <td>{user.email}</td>
                          <td><span className={`permission-badge ${user.is_admin ? 'admin' : (user.permission_level || 'viewer').toLowerCase()}`}>
                            {user.is_admin ? 'Admin' : 
                             user.permission_level === 'manager' ? 'Manager' : 
                             user.permission_level === 'viewer' ? 'Viewer' : 
                             user.permission_level || 'User'}
                          </span></td>
                          <td>{user.groups && user.groups.length > 0 ? user.groups.join(', ') : 'No groups'}</td>
                          <td>
                            <span className={`status-badge ${user.is_active ? 'active' : 'inactive'}`}>
                              {user.is_active ? 'Active' : 'Inactive'}
                            </span>
                          </td>
                          <td>{new Date(user.created_at).toLocaleDateString()}</td>
                          {userIsAdmin && (
                            <td>
                              <button className="action-button edit" onClick={() => handleEditUser(user)}>Edit</button>
                              {!user.is_admin && <button className="action-button delete" onClick={() => handleDeleteUser(user)}>Delete</button>}
                            </td>
                          )}
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={userIsAdmin ? 7 : 6}>No users found</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}
              
              {showUserForm && <CreateUserForm />}
              {showEditUserForm && editingUser && <EditUserForm />}
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
    } catch (error) {
      console.error('Error rendering content:', error);
      return <div className="error-message">Error loading settings.</div>;
    }
  };

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
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
      <main className="content" style={{ flex: 1, padding: '20px' }}>
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