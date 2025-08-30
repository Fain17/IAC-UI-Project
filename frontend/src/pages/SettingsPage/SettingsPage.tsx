import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import tokenManager from '../../utils/tokenManager';
import { getAdminUsers, createAdminUser, getAdminUser, AdminUser, CreateUserRequest, AdminUsersResponse, updateUserPermissionsNew as updateUserPermissionsAPI, UpdateUserPermissionsRequest, deleteUser, updateUserActiveStatus, getAllUsersPermissionsNew, getAdminGroups, createAdminGroup, addUserToGroup, removeUserFromGroup, getUserGroups, AdminGroup, AdminGroupUser, getGroupUsers, deleteAdminGroup, updateAdminGroup, getRolePermissions, getRolePermissionsByRole, resetRolePermissions, addRolePermission, removeRolePermission, removeMultipleRolePermissions, AddRolePermissionRequest, RemoveRolePermissionRequest, RemoveMultipleRolePermissionsRequest, RolePermission } from '../../api';
import './SettingsPage.css';

interface User {
  id: string;
  username: string;
  email: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
  updated_at: string;
  role: string;
  groups: string[];
}

interface UserPermission {
  id: string;
  username: string;
  email: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
  updated_at: string;
  role: string;
  groups: string[];
  role_permissions: string[];
  description: string;
}

interface UserGroup {
  id: string;
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
  const [userRole, setUserRole] = useState<string>('');
  const [userPermissions, setUserPermissions] = useState<any>(null);

  // State for active submenu
  const location = useLocation();
  const [activeSubMenu, setActiveSubMenu] = useState<string>('general');
  const derivedSubMenu = useMemo<string>(() => {
    if (location.pathname.startsWith('/settings/users')) return 'users';
    if (location.pathname.startsWith('/settings/groups')) return 'groups';
    if (location.pathname.startsWith('/settings/roles')) return 'roles';
    if (location.pathname.startsWith('/settings/permissions')) return 'permissions';
    return 'general';
  }, [location.pathname]);
  useEffect(() => { setActiveSubMenu(derivedSubMenu); }, [derivedSubMenu]);

  // Load user role and permissions
  useEffect(() => {
    const loadUserInfo = async () => {
      try {
        const user = tokenManager.getUser();
        if (user) {
          setUserUsername(user.username || '');
          setUserEmail(user.email || '');
          
          // Get role from JWT claims instead of API call
          const token = tokenManager.getToken();
          if (token) {
            try {
              // Decode JWT token to get role and permissions from claims
              const payload = JSON.parse(atob(token.split('.')[1]));
              const role = payload.role || payload.user_role || 'viewer';
              const permissions = payload.permissions || payload.user_permissions || {};
              
              setUserRole(role);
              setUserPermissions(permissions);
            } catch (jwtError) {
              console.error('Failed to decode JWT token:', jwtError);
              setUserRole('viewer');
              setUserPermissions({});
            }
          } else {
            setUserRole('viewer');
            setUserPermissions({});
          }
        }
      } catch (error) {
        console.error('Failed to load user info:', error);
        setUserRole('viewer');
        setUserPermissions({});
      }
    };

    loadUserInfo();
  }, []);

  // State for general settings
  const [notifications, setNotifications] = useState(true);
  const [saved, setSaved] = useState(false);

  // State for user management
  const [users, setUsers] = useState<User[]>([]);
  const [userGroups, setUserGroups] = useState<UserGroup[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [rolePermissions, setRolePermissions] = useState<RolePermission[]>([]);
  const [filteredRolePermissions, setFilteredRolePermissions] = useState<RolePermission[]>([]);
  const [selectedRoleFilter, setSelectedRoleFilter] = useState<string>('');
  const [showAddPermissionModal, setShowAddPermissionModal] = useState(false);
  const [addPermissionForm, setAddPermissionForm] = useState<AddRolePermissionRequest>({
    role: '',
    permission: '',
    resource_type: ''
  });
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
      
      const allPermissions = permissionsResponse.data.permissions || [];
      console.log('📋 All permissions data:', allPermissions);
      
      // Create a map of username to permissions for quick lookup
      const permissionsMap = new Map(
        allPermissions.map((perm: UserPermission) => [perm.username, perm])
      );
      
      // Merge users with their permissions from the new API
      const usersWithData = usersData.map((user: any) => {
        const userPermissions = permissionsMap.get(user.username);
        const role = userPermissions?.role || 'viewer';
        const is_active = userPermissions?.is_active !== undefined ? userPermissions.is_active : user.is_active;
        const is_admin = userPermissions?.is_admin !== undefined ? userPermissions.is_admin : user.is_admin;
        const groups = userPermissions?.groups || [];
        return { ...user, role, is_active, is_admin, groups } as User;
      });
      
      console.log('👥 Users with permissions:', usersWithData);
      setUsers(usersWithData);
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
      const resp = await getAdminGroups();
      const groupsResp = (resp.data as any)?.groups || (resp.data as any) || [];

      const baseGroups: UserGroup[] = groupsResp.map((g: any) => ({
        id: g.id,
        name: g.name,
        description: g.description || '',
        member_count: 0,
        created_at: g.created_at || new Date().toISOString(),
      }));

      // Fetch member counts per group
      const groupsWithCounts = await Promise.all(
        baseGroups.map(async (g) => {
          try {
            const usersResp = await getGroupUsers(g.id);
            const data: any = usersResp.data;
            const count = typeof data?.count === 'number'
              ? data.count
              : Array.isArray((data && data.users))
                ? data.users.length
                : Array.isArray(data)
                  ? data.length
                  : 0;
            return { ...g, member_count: count } as UserGroup;
          } catch (e) {
            return g;
          }
        })
      );

      setUserGroups(groupsWithCounts);
    } catch (error: any) {
      setMessage({ type: 'error', text: 'Failed to load user groups: ' + (error.response?.data?.detail || error.message) });
    } finally {
      setLoading(false);
    }
  }, []);

  // Group management state and handlers
  const [showCreateGroup, setShowCreateGroup] = useState(false);
  const [newGroup, setNewGroup] = useState<{ name: string; description: string }>({ name: '', description: '' });
  
  // Edit group state and handlers
  const [showEditGroup, setShowEditGroup] = useState(false);
  const [editingGroup, setEditingGroup] = useState<UserGroup | null>(null);
  const [editGroupData, setEditGroupData] = useState<{ name: string; description: string }>({ name: '', description: '' });

  const handleCreateGroup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newGroup.name.trim()) {
      setMessage({ type: 'error', text: 'Group name is required' });
      return;
    }
    setLoading(true);
    try {
      await createAdminGroup({ name: newGroup.name.trim(), description: newGroup.description.trim() });
      setMessage({ type: 'success', text: 'Group created successfully!' });
      setShowCreateGroup(false);
      setNewGroup({ name: '', description: '' });
      await loadUserGroups();
    } catch (error: any) {
      setMessage({ type: 'error', text: 'Failed to create group: ' + (error.response?.data?.detail || error.message) });
    } finally {
      setLoading(false);
    }
  };

  const [selectedUserForGroups, setSelectedUserForGroups] = useState<User | null>(null);
  const [userGroupsForSelected, setUserGroupsForSelected] = useState<AdminGroup[]>([]);
  const [assignGroupId, setAssignGroupId] = useState<string>('');

  const openUserGroups = async (user: User) => {
    setSelectedUserForGroups(user);
    try {
      const resp = await getUserGroups(user.id);
      const groupsResp = (resp.data as any)?.groups || (resp.data as any) || [];
      setUserGroupsForSelected(groupsResp);
    } catch (error: any) {
      setMessage({ type: 'error', text: 'Failed to load user groups: ' + (error.response?.data?.detail || error.message) });
    }
  };

  const handleAssignGroup = async () => {
    if (!selectedUserForGroups || assignGroupId === '') return;
    setLoading(true);
    try {
      await addUserToGroup(selectedUserForGroups.id, assignGroupId);
      await openUserGroups(selectedUserForGroups);
      setAssignGroupId('');
      setMessage({ type: 'success', text: 'User added to group' });
      await loadUsers();
    } catch (error: any) {
      setMessage({ type: 'error', text: 'Failed to add user to group: ' + (error.response?.data?.detail || error.message) });
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveUserGroup = async (groupId: string) => {
    if (!selectedUserForGroups) return;
    setLoading(true);
    try {
      await removeUserFromGroup(selectedUserForGroups.id, groupId);
      await openUserGroups(selectedUserForGroups);
      setMessage({ type: 'success', text: 'User removed from group' });
      await loadUsers();
    } catch (error: any) {
      setMessage({ type: 'error', text: 'Failed to remove user from group: ' + (error.response?.data?.detail || error.message) });
    } finally {
      setLoading(false);
    }
  };

  // Load roles function
  const loadRoles = useCallback(async () => {
    setLoading(true);
    try {
      const response = await getRolePermissions();
      const rolePermissionsData = response.data.permissions || [];
      setRolePermissions(rolePermissionsData);
      
      // Group permissions by role
      const rolesMap = new Map<string, { permissions: string[], resourceTypes: string[] }>();
      
      rolePermissionsData.forEach((rp: RolePermission) => {
        if (!rolesMap.has(rp.role)) {
          rolesMap.set(rp.role, { permissions: [], resourceTypes: [] });
        }
        const roleData = rolesMap.get(rp.role)!;
        roleData.permissions.push(...rp.permissions);
        roleData.resourceTypes.push(rp.resource_type);
      });
      
      // Convert to Role format for display
      const rolesData: Role[] = Array.from(rolesMap.entries()).map(([roleName, data]) => ({
        id: roleName === 'admin' ? 1 : roleName === 'manager' ? 2 : 3,
        name: roleName.charAt(0).toUpperCase() + roleName.slice(1),
        description: `${roleName.charAt(0).toUpperCase() + roleName.slice(1)} role with access to ${data.resourceTypes.join(', ')} resources`,
        permissions: [...new Set(data.permissions)], // Remove duplicates
        user_count: 0, // Will be calculated separately
        created_at: new Date().toISOString()
      }));
      
      setRoles(rolesData);
      
      // Initialize filtered permissions with all data
      setFilteredRolePermissions(rolePermissionsData);
    } catch (error: any) {
      setMessage({ type: 'error', text: 'Failed to load roles: ' + (error.response?.data?.detail || error.message) });
    } finally {
      setLoading(false);
    }
  }, []);

  // Filter role permissions by role
  const filterRolePermissions = useCallback(async (role?: string) => {
    try {
      setLoading(true);
      let response;
      
      if (role) {
        // Filter by role
        response = await getRolePermissionsByRole(role);
        if (response.data.success) {
          setFilteredRolePermissions(response.data.permissions);
        }
      } else {
        // No filters - show all
        setFilteredRolePermissions(rolePermissions);
      }
    } catch (error: any) {
      setMessage({ type: 'error', text: 'Failed to filter permissions: ' + (error.response?.data?.detail || error.message) });
    } finally {
      setLoading(false);
    }
  }, [rolePermissions]);

  // Handle role filter change
  const handleRoleFilterChange = (role: string) => {
    setSelectedRoleFilter(role);
    filterRolePermissions(role || undefined);
  };

  // Clear all filters
  const clearFilters = () => {
    setSelectedRoleFilter('');
    setFilteredRolePermissions(rolePermissions);
  };

  // Reset role permissions for a specific role
  const handleResetRolePermissions = async (role: string) => {
    if (!window.confirm(`Are you sure you want to reset permissions for role "${role}"? This will restore default permissions and cannot be undone.`)) {
      return;
    }

    try {
      setLoading(true);
      await resetRolePermissions(role);
      setMessage({ type: 'success', text: `Role permissions for "${role}" have been reset successfully!` });
      
      // Refresh the data
      await loadRoles();
    } catch (error: any) {
      setMessage({ type: 'error', text: 'Failed to reset role permissions: ' + (error.response?.data?.detail || error.message) });
    } finally {
      setLoading(false);
    }
  };

  // Add role permission
  const handleAddRolePermission = async () => {
    if (!addPermissionForm.role || !addPermissionForm.permission || !addPermissionForm.resource_type) {
      setMessage({ type: 'error', text: 'Please fill in all fields' });
      return;
    }

    try {
      setLoading(true);
      await addRolePermission(addPermissionForm);
      setMessage({ type: 'success', text: 'Role permission added successfully!' });
      
      // Close modal and reset form
      setShowAddPermissionModal(false);
      setAddPermissionForm({ role: '', permission: '', resource_type: '' });
      
      // Refresh the data
      await loadRoles();
    } catch (error: any) {
      setMessage({ type: 'error', text: 'Failed to add role permission: ' + (error.response?.data?.detail || error.message) });
    } finally {
      setLoading(false);
    }
  };

  // Remove role permission
  const handleRemoveRolePermission = async (role: string, permission: string, resourceType: string) => {
    if (!window.confirm(`Are you sure you want to remove "${permission}" permission for "${role}" role on "${resourceType}" resource?`)) {
      return;
    }

    try {
      setLoading(true);
      await removeRolePermission({ role, permission, resource_type: resourceType });
      setMessage({ type: 'success', text: 'Role permission removed successfully!' });
      
      // Refresh the data
      await loadRoles();
    } catch (error: any) {
      setMessage({ type: 'error', text: 'Failed to remove role permission: ' + (error.response?.data?.detail || error.message) });
    } finally {
      setLoading(false);
    }
  };

  // Remove all role permissions for a specific role and resource type
  const handleRemoveAllRolePermissions = async (role: string, resourceType: string) => {
    if (!window.confirm(`Are you sure you want to remove all permissions for "${role}" role on "${resourceType}" resource?`)) {
      return;
    }

    try {
      setLoading(true);
      
      // Find the role permission entry to get all permissions
      const rolePermissionEntry = rolePermissions.find(rp => rp.role === role && rp.resource_type === resourceType);
      
      if (!rolePermissionEntry) {
        setMessage({ type: 'error', text: 'No permissions found for this role and resource type' });
        return;
      }

      // Use the new API to remove all permissions at once
      await removeMultipleRolePermissions({
        role,
        permissions: rolePermissionEntry.permissions,
        resource_type: resourceType
      });
      
      setMessage({ type: 'success', text: 'All role permissions removed successfully!' });
      
      // Refresh the data
      await loadRoles();
    } catch (error: any) {
      setMessage({ type: 'error', text: 'Failed to remove role permissions: ' + (error.response?.data?.detail || error.message) });
    } finally {
      setLoading(false);
    }
  };

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
                <label htmlFor="role">Role</label>
                <select
                  id="role"
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
      role: editingUser?.role || 'viewer',
      is_active: editingUser?.is_active ?? true
    });

    const handleSubmit = async (e: React.FormEvent) => {
      e.preventDefault();
      if (!editingUser) return;

      setLoading(true);
      try {
        // Update permissions using PUT /admin/users/{user_id}/permissions
        await updateUserPermissionsAPI(editingUser.id, {
          role: formData.role as 'admin' | 'manager' | 'viewer',
          is_active: formData.is_active
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
              <label htmlFor="role">Role</label>
              <select
                id="role"
                value={formData.role}
                onChange={(e) => setFormData({...formData, role: e.target.value})}
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
                {userRole === 'admin' && (
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
                      {userRole === 'admin' && <th>Actions</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {users && users.length > 0 ? (
                      users.map((user) => (
                        <tr key={user.id}>
                          <td>{user.username}</td>
                          <td>{user.email}</td>
                          <td><span className={`permission-badge ${user.is_admin ? 'admin' : (user.role || 'viewer').toLowerCase()}`}>
                            {user.is_admin ? 'Admin' : 
                             user.role === 'manager' ? 'Manager' : 
                             user.role === 'viewer' ? 'Viewer' : 
                             user.role || 'User'}
                          </span></td>
                          <td>{user.groups && user.groups.length > 0 ? user.groups.join(', ') : 'No groups'}</td>
                          <td>
                            <span className={`status-badge ${user.is_active ? 'active' : 'inactive'}`}>
                              {user.is_active ? 'Active' : 'Inactive'}
                            </span>
                          </td>
                          <td>{new Date(user.created_at).toLocaleDateString()}</td>
                          {userRole === 'admin' && (
                            <td>
                              <button className="action-button edit" onClick={() => handleEditUser(user)}>Edit</button>
                              {/* Removed per request: Manage Groups moved to Groups page */}
                              {!user.is_admin && <button className="action-button delete" onClick={() => handleDeleteUser(user)}>Delete</button>}
                            </td>
                          )}
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={userRole === 'admin' ? 7 : 6}>No users found</td>
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
                {userRole === 'admin' && (
                  <button 
                    onClick={() => setShowCreateGroup(true)}
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
                        {userRole === 'admin' && <th>Actions</th>}
                      </tr>
                    </thead>
                    <tbody>
                      {userGroups.map((group) => (
                        <tr key={group.id}>
                          <td>{group.name}</td>
                          <td>{group.description}</td>
                          <td>{group.member_count}</td>
                          <td>{new Date(group.created_at).toLocaleDateString()}</td>
                          {userRole === 'admin' && (
                            <td>
                              <button className="action-button" onClick={() => openGroupUsersForGroup(group)}>Manage Users</button>
                              <button className="action-button edit" onClick={() => handleEditGroup(group)}>Edit</button>
                              <button className="action-button delete" onClick={() => handleDeleteGroup(group)}>Delete</button>
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
                <p>Detailed view of role permissions across different resource types</p>
              </div>
              
              {/* Filter Controls */}
              <div className="filter-controls" style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
                <div style={{ display: 'flex', gap: '15px', alignItems: 'center', flexWrap: 'wrap', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', gap: '15px', alignItems: 'center' }}>
                    <div>
                      <label htmlFor="role-filter" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Filter by Role:</label>
                      <select 
                        id="role-filter"
                        value={selectedRoleFilter} 
                        onChange={(e) => handleRoleFilterChange(e.target.value)}
                        style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ddd' }}
                      >
                        <option value="">All Roles</option>
                        <option value="admin">Admin</option>
                        <option value="manager">Manager</option>
                        <option value="viewer">Viewer</option>
                      </select>
                    </div>
                    
                    <button 
                      onClick={clearFilters}
                      style={{ 
                        padding: '8px 16px', 
                        backgroundColor: '#6c757d', 
                        color: 'white', 
                        border: 'none', 
                        borderRadius: '4px', 
                        cursor: 'pointer' 
                      }}
                    >
                      Clear Filters
                    </button>
                  </div>
                  
                  {userRole === 'admin' && (
                    <div style={{ display: 'flex', gap: '10px' }}>
                      <button 
                        onClick={() => setShowAddPermissionModal(true)}
                        disabled={loading}
                        style={{ 
                          padding: '8px 16px', 
                          backgroundColor: '#28a745', 
                          color: 'white', 
                          border: 'none', 
                          borderRadius: '4px', 
                          cursor: 'pointer' 
                        }}
                        title="Add new role permission"
                      >
                        ➕ Add Permission
                      </button>
                      <button 
                        onClick={() => handleResetRolePermissions(selectedRoleFilter || 'all')}
                        disabled={loading}
                        style={{ 
                          padding: '8px 16px', 
                          backgroundColor: '#dc3545', 
                          color: 'white', 
                          border: 'none', 
                          borderRadius: '4px', 
                          cursor: 'pointer' 
                        }}
                        title={selectedRoleFilter ? `Reset permissions for ${selectedRoleFilter} role` : 'Reset all role permissions'}
                      >
                        🔄 Reset Role Permissions
                      </button>
                    </div>
                  )}
                </div>
              </div>
              
              {loading ? (
                <div className="loading">Loading roles...</div>
              ) : (
                <div className="data-table">
                  <table>
                    <thead>
                      <tr>
                        <th>Role</th>
                        <th>Resource Type</th>
                        <th>Permissions</th>
                        <th>Last Updated</th>
                        {userRole === 'admin' && <th>Actions</th>}
                      </tr>
                    </thead>
                    <tbody>
                      {filteredRolePermissions.map((rolePerm, index) => (
                        <tr key={`${rolePerm.role}-${rolePerm.resource_type}-${index}`}>
                          <td>
                            <span className={`role-badge ${rolePerm.role}`}>
                              {rolePerm.role.charAt(0).toUpperCase() + rolePerm.role.slice(1)}
                            </span>
                          </td>
                          <td>
                            <span className="resource-badge">
                              {rolePerm.resource_type.charAt(0).toUpperCase() + rolePerm.resource_type.slice(1)}
                            </span>
                          </td>
                          <td>
                            <div className="permissions-list">
                              {rolePerm.permissions.map((permission, permIndex) => (
                                <span key={permIndex} className={`permission-badge ${permission}`}>
                                  {permission}
                                  {userRole === 'admin' && rolePerm.role !== 'admin' && (
                                    <button
                                      onClick={() => handleRemoveRolePermission(rolePerm.role, permission, rolePerm.resource_type)}
                                      disabled={loading}
                                      style={{
                                        marginLeft: '5px',
                                        padding: '2px 6px',
                                        fontSize: '10px',
                                        backgroundColor: '#dc3545',
                                        color: 'white',
                                        border: 'none',
                                        borderRadius: '3px',
                                        cursor: 'pointer'
                                      }}
                                      title={`Remove ${permission} permission`}
                                    >
                                      ×
                                    </button>
                                  )}
                                </span>
                              ))}
                            </div>
                          </td>
                          <td>{new Date(rolePerm.updated_at).toLocaleDateString()}</td>
                          {userRole === 'admin' && rolePerm.role !== 'admin' && (
                            <td>
                              <button
                                onClick={() => handleRemoveAllRolePermissions(rolePerm.role, rolePerm.resource_type)}
                                disabled={loading}
                                style={{
                                  padding: '4px 8px',
                                  fontSize: '12px',
                                  backgroundColor: '#ffc107',
                                  color: '#212529',
                                  border: 'none',
                                  borderRadius: '4px',
                                  cursor: 'pointer'
                                }}
                                title={`Remove all permissions for ${rolePerm.role} on ${rolePerm.resource_type}`}
                              >
                                Remove All
                              </button>
                            </td>
                          )}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  
                  <div className="summary-stats" style={{ marginTop: '20px', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
                    <h4>Summary</h4>
                    <p><strong>Total Roles:</strong> {new Set(filteredRolePermissions.map(rp => rp.role)).size}</p>
                    <p><strong>Total Resource Types:</strong> {new Set(filteredRolePermissions.map(rp => rp.resource_type)).size}</p>
                    <p><strong>Total Permissions:</strong> {filteredRolePermissions.reduce((sum, rp) => sum + rp.permissions.length, 0)}</p>
                    <p><strong>Filtered Results:</strong> {filteredRolePermissions.length} of {rolePermissions.length} entries</p>
                    {selectedRoleFilter && (
                      <p><strong>Current Filter:</strong> Role = "{selectedRoleFilter}"</p>
                    )}
                  </div>
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
                        {userRole === 'admin' && <th>Actions</th>}
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
                          {userRole === 'admin' && (
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

  // Group Users management (under Groups tab)
  const [selectedGroupForUsers, setSelectedGroupForUsers] = useState<UserGroup | null>(null);
  const [groupUsers, setGroupUsers] = useState<AdminGroupUser[]>([]);
  const [selectedUserIdToAdd, setSelectedUserIdToAdd] = useState<string>('');

  const openGroupUsersForGroup = async (group: UserGroup) => {
    setSelectedGroupForUsers(group);
    try {
      const resp = await getGroupUsers(group.id);
      const list: AdminGroupUser[] = (resp.data as any)?.users || (resp.data as any) || [];
      setGroupUsers(list);
      // Ensure we have full users list for add dropdown
      if (!users || users.length === 0) {
        await loadUsers();
      }
    } catch (error: any) {
      setMessage({ type: 'error', text: 'Failed to load group users: ' + (error.response?.data?.detail || error.message) });
    }
  };

  const handleAddUserToSelectedGroup = async () => {
    if (!selectedGroupForUsers || selectedUserIdToAdd === '') return;
    setLoading(true);
    try {
      await addUserToGroup(selectedUserIdToAdd, selectedGroupForUsers.id);
      await openGroupUsersForGroup(selectedGroupForUsers);
      await loadUserGroups();
      setSelectedUserIdToAdd('');
      setMessage({ type: 'success', text: 'User added to group' });
    } catch (error: any) {
      setMessage({ type: 'error', text: 'Failed to add user: ' + (error.response?.data?.detail || error.message) });
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveUserFromSelectedGroup = async (userId: string) => {
    if (!selectedGroupForUsers) return;
    setLoading(true);
    try {
      await removeUserFromGroup(userId, selectedGroupForUsers.id);
      await openGroupUsersForGroup(selectedGroupForUsers);
      await loadUserGroups();
      setMessage({ type: 'success', text: 'User removed from group' });
    } catch (error: any) {
      setMessage({ type: 'error', text: 'Failed to remove user: ' + (error.response?.data?.detail || error.message) });
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteGroup = async (group: UserGroup) => {
    // Confirm deletion
    if (!window.confirm(`Are you sure you want to delete group "${group.name}"? This action cannot be undone.`)) {
      return;
    }

    setLoading(true);
    try {
      await deleteAdminGroup(group.id);
      setMessage({ type: 'success', text: `Group "${group.name}" deleted successfully!` });
      await loadUserGroups(); // Refresh the groups list
    } catch (error: any) {
      setMessage({ type: 'error', text: 'Failed to delete group: ' + (error.response?.data?.detail || error.message) });
    } finally {
      setLoading(false);
    }
  };

  const handleEditGroup = (group: UserGroup) => {
    setEditingGroup(group);
    setEditGroupData({ name: group.name, description: group.description });
    setShowEditGroup(true);
  };

  const handleUpdateGroup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingGroup || !editGroupData.name.trim()) {
      setMessage({ type: 'error', text: 'Group name is required' });
      return;
    }

    setLoading(true);
    try {
      await updateAdminGroup(editingGroup.id, { 
        name: editGroupData.name.trim(), 
        description: editGroupData.description.trim() 
      });
      setMessage({ type: 'success', text: 'Group updated successfully!' });
      setShowEditGroup(false);
      setEditingGroup(null);
      setEditGroupData({ name: '', description: '' });
      await loadUserGroups(); // Refresh the groups list
    } catch (error: any) {
      setMessage({ type: 'error', text: 'Failed to update group: ' + (error.response?.data?.detail || error.message) });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
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

      {/* Modal for Create Group */}
      {showCreateGroup && (
        <div className="create-form-overlay">
          <div className="create-form">
            <div className="form-header">
              <h3>Create Group</h3>
              <button onClick={() => setShowCreateGroup(false)} className="close-button">✕</button>
            </div>
            <form onSubmit={handleCreateGroup}>
              <div className="form-group">
                <label htmlFor="groupName">Group Name *</label>
                <input id="groupName" type="text" value={newGroup.name} onChange={(e) => setNewGroup({ ...newGroup, name: e.target.value })} required />
              </div>
              <div className="form-group">
                <label htmlFor="groupDescription">Description</label>
                <textarea id="groupDescription" value={newGroup.description} onChange={(e) => setNewGroup({ ...newGroup, description: e.target.value })} rows={3} />
              </div>
              <div className="form-actions">
                <button type="submit" className="submit-button" disabled={loading}>{loading ? 'Creating...' : 'Create Group'}</button>
                <button type="button" className="cancel-button" onClick={() => setShowCreateGroup(false)} disabled={loading}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal for Edit Group */}
      {showEditGroup && editingGroup && (
        <div className="create-form-overlay">
          <div className="create-form">
            <div className="form-header">
              <h3>Edit Group: {editingGroup.name}</h3>
              <button onClick={() => setShowEditGroup(false)} className="close-button">✕</button>
            </div>
            <form onSubmit={handleUpdateGroup}>
              <div className="form-group">
                <label htmlFor="editGroupName">Group Name *</label>
                <input 
                  id="editGroupName" 
                  type="text" 
                  value={editGroupData.name} 
                  onChange={(e) => setEditGroupData({ ...editGroupData, name: e.target.value })} 
                  required 
                />
              </div>
              <div className="form-group">
                <label htmlFor="editGroupDescription">Description</label>
                <textarea 
                  id="editGroupDescription" 
                  value={editGroupData.description} 
                  onChange={(e) => setEditGroupData({ ...editGroupData, description: e.target.value })} 
                  rows={3} 
                />
              </div>
              <div className="form-actions">
                <button type="submit" className="submit-button" disabled={loading}>{loading ? 'Updating...' : 'Update Group'}</button>
                <button type="button" className="cancel-button" onClick={() => setShowEditGroup(false)} disabled={loading}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal for Manage Group Users */}
      {selectedGroupForUsers && (
        <div className="create-form-overlay">
          <div className="create-form">
            <div className="form-header">
              <h3>Manage Users: {selectedGroupForUsers.name}</h3>
              <button onClick={() => setSelectedGroupForUsers(null)} className="close-button">✕</button>
            </div>
            <div>
              <div className="form-group">
                <label>Current Users</label>
                <div className="data-table">
                  <table>
                    <thead>
                      <tr><th>Username</th><th>Email</th><th>Status</th><th>Actions</th></tr>
                    </thead>
                    <tbody>
                      {groupUsers.length === 0 ? (
                        <tr><td colSpan={4}>No users</td></tr>
                      ) : groupUsers.map((u) => (
                        <tr key={u.id}>
                          <td>{u.username}</td>
                          <td>{u.email}</td>
                          <td><span className={`status-badge ${u.is_active ? 'active' : 'inactive'}`}>{u.is_active ? 'Active' : 'Inactive'}</span></td>
                          <td><button className="action-button delete" onClick={() => handleRemoveUserFromSelectedGroup(u.id)}>Remove</button></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
              <div className="form-group">
                <label>Add User to Group</label>
                <div style={{ display: 'flex', gap: 8 }}>
                  <select value={selectedUserIdToAdd} onChange={(e) => setSelectedUserIdToAdd(e.target.value)}>
                    <option value="">Select user</option>
                    {users
                      .filter((u) => !groupUsers.some((gu) => gu.id === u.id))
                      .map((u) => (
                        <option key={u.id} value={u.id}>{u.username} ({u.email})</option>
                      ))}
                  </select>
                  <button className="action-button" onClick={handleAddUserToSelectedGroup} disabled={selectedUserIdToAdd === '' || loading}>Add</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Add Role Permission Modal */}
      {showAddPermissionModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>Add Role Permission</h3>
              <button className="modal-close" onClick={() => setShowAddPermissionModal(false)}>×</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label>Role *</label>
                <select 
                  value={addPermissionForm.role} 
                  onChange={(e) => setAddPermissionForm(prev => ({ ...prev, role: e.target.value }))}
                  required
                >
                  <option value="">Select Role</option>
                  <option value="admin">Admin</option>
                  <option value="manager">Manager</option>
                  <option value="viewer">Viewer</option>
                </select>
              </div>
              
              <div className="form-group">
                <label>Resource Type *</label>
                <select 
                  value={addPermissionForm.resource_type} 
                  onChange={(e) => setAddPermissionForm(prev => ({ ...prev, resource_type: e.target.value }))}
                  required
                >
                  <option value="">Select Resource Type</option>
                  <option value="group">Group</option>
                  <option value="config">Config</option>
                  <option value="workflow">Workflow</option>
                </select>
              </div>
              
              <div className="form-group">
                <label>Permission *</label>
                <select 
                  value={addPermissionForm.permission} 
                  onChange={(e) => setAddPermissionForm(prev => ({ ...prev, permission: e.target.value }))}
                  required
                >
                  <option value="">Select Permission</option>
                  <option value="read">Read</option>
                  <option value="write">Write</option>
                  <option value="delete">Delete</option>
                  {addPermissionForm.resource_type === 'workflow' && (
                    <>
                      <option value="execute">Execute</option>
                      <option value="create">Create</option>
                    </>
                  )}
                </select>
              </div>
            </div>
            <div className="modal-footer">
              <button className="cancel-button" onClick={() => setShowAddPermissionModal(false)}>Cancel</button>
              <button className="add-button" onClick={handleAddRolePermission} disabled={loading}>
                {loading ? 'Adding...' : 'Add Permission'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SettingsPage; 