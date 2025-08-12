import React, { useState, useEffect } from 'react';
import { getWorkflows, getAdminGroups, shareWorkflowWithGroup, unshareWorkflowWithGroup, getWorkflowPermissions, getAllWorkflowsWithPermissions, getGroupUsers, updateUserPermissionsNew } from '../../api';
import type { Workflow, AdminGroup, WorkflowGroupShare, WorkflowPermission, WorkflowAssignmentData } from '../../api';
import tokenManager from '../../utils/tokenManager';
import './AssignWorkflowsPage.css';

const AssignWorkflowsPage: React.FC = () => {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [groups, setGroups] = useState<AdminGroup[]>([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState<Workflow | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'warning'; text: string } | null>(null);
  const [showUserPermissionsModal, setShowUserPermissionsModal] = useState(false);
  const [editingUser, setEditingUser] = useState<WorkflowPermission | null>(null);
  const [editForm, setEditForm] = useState<{ role: 'admin' | 'manager' | 'viewer'; is_active: boolean }>({ role: 'viewer', is_active: true });
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);
  const [hasForcedAdmin, setHasForcedAdmin] = useState<boolean>(false);

  // Real workflow permissions and sharing data
  const [workflowAssignments, setWorkflowAssignments] = useState<Map<string, WorkflowAssignmentData>>(new Map());

  useEffect(() => {
    loadWorkflows();
    loadGroups();
    getCurrentUserId();
  }, []);

  useEffect(() => {
    if (selectedWorkflow) {
      loadWorkflowPermissions(selectedWorkflow.id);
    }
  }, [selectedWorkflow]);

  const getCurrentUserId = () => {
    const userData = tokenManager.getUser();
    if (userData && userData.id && !hasForcedAdmin) {
      setCurrentUserId(userData.id);
      
      // Check if user is already admin before making API call
      if (userData.isAdmin) {
        console.log('🔐 Current user is already admin, skipping force update');
        setHasForcedAdmin(true);
      } else {
        console.log('🔐 Current user is not admin, forcing admin privileges');
        // Force set current user to admin if not already (only once)
        forceSetCurrentUserToAdmin(userData.id);
      }
    }
  };

  const forceSetCurrentUserToAdmin = async (userId: string) => {
    try {
      console.log('🔐 Force setting current user to admin:', userId);
      setHasForcedAdmin(true); // Prevent repeated calls
      
      await updateUserPermissionsNew(userId, {
        role: 'admin',
        is_active: true
      });
      console.log('✅ Current user successfully set to admin');
      
      // Update local user data to reflect admin status
      const userData = tokenManager.getUser();
      if (userData) {
        const updatedUserData = { ...userData, isAdmin: true };
        localStorage.setItem('user_data', JSON.stringify(updatedUserData));
      }
    } catch (error) {
      console.error('❌ Failed to force set current user to admin:', error);
      setHasForcedAdmin(false); // Reset flag on error to allow retry
    }
  };

  const loadWorkflows = async () => {
    try {
      setLoading(true);
      const response = await getWorkflows();
      let workflowsData: Workflow[] = [];
      
      if (response.data && typeof response.data === 'object') {
        if ('workflows' in response.data && Array.isArray(response.data.workflows)) {
          workflowsData = response.data.workflows;
        } else if (Array.isArray(response.data)) {
          workflowsData = response.data;
        }
      }
      
      setWorkflows(workflowsData);
    } catch (error: any) {
      setMessage({ type: 'error', text: 'Failed to load workflows: ' + (error.response?.data?.detail || error.message) });
    } finally {
      setLoading(false);
    }
  };

  const loadGroups = async () => {
    try {
      const response = await getAdminGroups();
      let groupsData: AdminGroup[] = [];
      
      if (response.data && typeof response.data === 'object') {
        if ('groups' in response.data && Array.isArray(response.data.groups)) {
          groupsData = response.data.groups;
        } else if (Array.isArray(response.data)) {
          groupsData = response.data;
        }
      }
      
      setGroups(groupsData);
      
      // Load member counts for each group
      await loadGroupMemberCounts(groupsData);
    } catch (error: any) {
      console.error('Failed to load groups:', error);
    }
  };

  const loadGroupMemberCounts = async (groupsData: AdminGroup[]) => {
    try {
      const memberCounts = new Map<string, number>();
      
      // Fetch member counts for each group
      const memberCountPromises = groupsData.map(async (group) => {
        try {
          const response = await getGroupUsers(group.id);
          let users: any[] = [];
          
          if (response.data && typeof response.data === 'object') {
            if ('users' in response.data && Array.isArray(response.data.users)) {
              users = response.data.users;
            } else if (Array.isArray(response.data)) {
              users = response.data;
            }
          }
          
          memberCounts.set(group.id, users.length);
        } catch (error) {
          console.error(`Failed to load member count for group ${group.id}:`, error);
          memberCounts.set(group.id, 0);
        }
      });
      
      await Promise.all(memberCountPromises);
      
      // Update workflow assignments with real member counts
      setWorkflowAssignments(prev => {
        const newMap = new Map(prev);
        prev.forEach((assignment, workflowId) => {
          const updatedGroups = assignment.shared_groups.map(group => ({
            ...group,
            member_count: memberCounts.get(group.group_id) || 0
          }));
          
          newMap.set(workflowId, {
            ...assignment,
            shared_groups: updatedGroups
          });
        });
        return newMap;
      });
    } catch (error) {
      console.error('Failed to load group member counts:', error);
    }
  };

  const loadWorkflowPermissions = async (workflowId: string) => {
    try {
      const response = await getWorkflowPermissions(workflowId);
      const permissionsData = response.data;
      
      // Update the workflow assignments with real data
      setWorkflowAssignments(prev => new Map(prev.set(workflowId, {
        workflow_id: permissionsData.workflow_id,
        workflow_name: permissionsData.workflow_name,
        workflow_description: permissionsData.workflow_description,
        shared_groups: permissionsData.shared_groups,
        user_permissions: permissionsData.user_permissions
      })));
      
      // Update member counts for this workflow's groups
      await loadGroupMemberCounts(groups);
    } catch (error: any) {
      console.error('Failed to load workflow permissions:', error);
      // If the API endpoint doesn't exist yet, create empty data structure
      setWorkflowAssignments(prev => new Map(prev.set(workflowId, {
        workflow_id: workflowId,
        workflow_name: selectedWorkflow?.name || '',
        workflow_description: selectedWorkflow?.description,
        shared_groups: groups.map(group => ({
          group_id: group.id,
          group_name: group.name,
          group_description: group.description,
          is_shared: false,
          shared_at: undefined,
          member_count: 0 // Will be updated when loadGroupMemberCounts runs
        })),
        user_permissions: []
      })));
      
      // Update member counts for this workflow's groups
      await loadGroupMemberCounts(groups);
    }
  };

  const handleShareWithGroup = async (workflowId: string, groupId: string) => {
    try {
      setLoading(true);
      await shareWorkflowWithGroup(workflowId, groupId);
      
      // Update local state
      const assignment = workflowAssignments.get(workflowId);
      if (assignment) {
        const updatedGroups = assignment.shared_groups.map(group => 
          group.group_id === groupId 
            ? { ...group, is_shared: true, shared_at: new Date().toISOString() }
            : group
        );
        
        setWorkflowAssignments(new Map(workflowAssignments.set(workflowId, {
          ...assignment,
          shared_groups: updatedGroups
        })));
      }
      
      setMessage({ type: 'success', text: 'Workflow shared with group successfully!' });
    } catch (error: any) {
      setMessage({ type: 'error', text: 'Failed to share workflow: ' + (error.response?.data?.detail || error.message) });
    } finally {
      setLoading(false);
    }
  };

  const handleUnshareFromGroup = async (workflowId: string, groupId: string) => {
    try {
      setLoading(true);
      await unshareWorkflowWithGroup(workflowId, groupId);
      
      // Update local state
      const assignment = workflowAssignments.get(workflowId);
      if (assignment) {
        const updatedGroups = assignment.shared_groups.map(group => 
          group.group_id === groupId 
            ? { ...group, is_shared: false, shared_at: undefined }
            : group
        );
        
        setWorkflowAssignments(new Map(workflowAssignments.set(workflowId, {
          ...assignment,
          shared_groups: updatedGroups
        })));
      }
      
      setMessage({ type: 'success', text: 'Workflow unshared from group successfully!' });
    } catch (error: any) {
      setMessage({ type: 'error', text: 'Failed to unshare workflow: ' + (error.response?.data?.detail || error.message) });
    } finally {
      setLoading(false);
    }
  };

  const getPermissionBadgeClass = (permission: string) => {
    switch (permission) {
      case 'admin': return 'permission-badge admin';
      case 'write': return 'permission-badge write';
      case 'read': return 'permission-badge read';
      default: return 'permission-badge';
    }
  };

  const getPermissionLabel = (permission: string) => {
    switch (permission) {
      case 'admin': return 'Admin';
      case 'write': return 'Write';
      case 'read': return 'Read';
      default: return permission;
    }
  };

  const openUserPermissionsModal = (user: WorkflowPermission) => {
    // Check if user is admin (has admin permission)
    const isUserAdmin = user.permission === 'admin';
    
    setEditingUser(user);
    setEditForm({ 
      role: user.permission === 'write' ? 'manager' : user.permission === 'read' ? 'viewer' : 'admin',
      is_active: true // Default to true, could be enhanced to get actual status
    });
    setShowUserPermissionsModal(true);
    
    // If user is admin, show a message that role cannot be changed
    if (isUserAdmin) {
      setMessage({ 
        type: 'warning', 
        text: `User "${user.username}" has admin privileges. Their role cannot be changed.` 
      });
    }
  };

  const handleUpdateUserPermissions = async () => {
    if (!editingUser) return;
    
    // Check if user is admin and prevent role changes
    const isUserAdmin = editingUser.permission === 'admin';
    if (isUserAdmin) {
      setMessage({ 
        type: 'error', 
        text: `Cannot change role for admin user "${editingUser.username}". Admin users have immutable privileges.` 
      });
      return;
    }
    
    try {
      setLoading(true);
      console.log('🔧 Updating user permissions with payload:', editForm);
      console.log('🔧 Calling updateUserPermissionsNew with:', editingUser.user_id, editForm);
      
      await updateUserPermissionsNew(editingUser.user_id, editForm);
      
      // Update local state
      const assignment = workflowAssignments.get(selectedWorkflow!.id);
      if (assignment) {
        const updatedPermissions = assignment.user_permissions.map(user => 
          user.user_id === editingUser.user_id 
            ? { 
                ...user, 
                permission: (editForm.role === 'admin' ? 'admin' : editForm.role === 'manager' ? 'write' : 'read') as 'admin' | 'write' | 'read'
              }
            : user
        );
        
        setWorkflowAssignments(new Map(workflowAssignments.set(selectedWorkflow!.id, {
          ...assignment,
          user_permissions: updatedPermissions
        })));
      }
      
      setMessage({ type: 'success', text: `User permissions updated successfully!` });
      setShowUserPermissionsModal(false);
      setEditingUser(null);
    } catch (error: any) {
      console.error('❌ Error updating user permissions:', error);
      setMessage({ type: 'error', text: 'Failed to update user permissions: ' + (error.response?.data?.detail || error.message) });
    } finally {
      setLoading(false);
    }
  };

  const closeUserPermissionsModal = () => {
    setShowUserPermissionsModal(false);
    setEditingUser(null);
    setEditForm({ role: 'viewer', is_active: true });
  };

  if (loading && workflows.length === 0) {
    return (
      <div className="assign-workflows-page">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  return (
    <div className="assign-workflows-page">
      <div className="page-header">
        <h1>Assign Workflows</h1>
        <p>Manage workflow sharing with groups and user permissions</p>
      </div>

      {message && (
        <div className={`message ${message.type === 'success' ? 'success-message' : message.type === 'warning' ? 'warning-message' : 'error-message'}`}>
          {message.text}
          <button 
            className="message-close" 
            onClick={() => setMessage(null)}
          >
            ×
          </button>
        </div>
      )}

      <div className="workflow-selection">
        <h3>Select Workflow</h3>
        <div className="workflow-grid">
          {workflows.map(workflow => (
            <div
              key={workflow.id}
              className={`workflow-card ${selectedWorkflow?.id === workflow.id ? 'selected' : ''}`}
              onClick={() => setSelectedWorkflow(workflow)}
            >
              <h4>{workflow.name}</h4>
              <p>{workflow.description || 'No description'}</p>
              <div className="workflow-status">
                <span className="status-badge info">Active</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {selectedWorkflow && (
        <div className="assignment-details">
          <h3>Assignment Details: {selectedWorkflow.name}</h3>
          
          <div className="assignment-section">
            <h4>Group Sharing</h4>
            <div className="groups-table">
              <table>
                <thead>
                  <tr>
                    <th>Group Name</th>
                    <th>Description</th>
                    <th>Members</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {groups.map(group => {
                    const assignment = workflowAssignments.get(selectedWorkflow.id);
                    const groupShare = assignment?.shared_groups.find(g => g.group_id === group.id);
                    const isShared = groupShare?.is_shared || false;
                    
                    return (
                      <tr key={group.id}>
                        <td>{group.name}</td>
                        <td>{group.description || 'No description'}</td>
                        <td>{groupShare?.member_count || 0}</td>
                        <td>
                          <span className={`status-badge ${isShared ? 'success' : 'warning'}`}>
                            {isShared ? 'Shared' : 'Not Shared'}
                          </span>
                        </td>
                        <td>
                          {isShared ? (
                            <button
                              className="action-button danger"
                              onClick={() => handleUnshareFromGroup(selectedWorkflow.id, group.id)}
                              disabled={loading}
                            >
                              Unshare
                            </button>
                          ) : (
                            <button
                              className="action-button success"
                              onClick={() => handleShareWithGroup(selectedWorkflow.id, group.id)}
                              disabled={loading}
                            >
                              Share
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          <div className="assignment-section">
            <h4>User Permissions</h4>
            <div className="permissions-table">
              <table>
                <thead>
                  <tr>
                    <th>Username</th>
                    <th>Email</th>
                    <th>Permission</th>
                    <th>Granted At</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {workflowAssignments.get(selectedWorkflow.id)?.user_permissions.length ? (
                    workflowAssignments.get(selectedWorkflow.id)?.user_permissions.map(user => (
                      <tr key={user.user_id}>
                        <td>{user.username}</td>
                        <td>{user.email}</td>
                        <td>
                          <span className={getPermissionBadgeClass(user.permission)}>
                            {getPermissionLabel(user.permission)}
                          </span>
                        </td>
                        <td>{new Date(user.granted_at).toLocaleDateString()}</td>
                        <td>
                          <button
                            className={`action-button ${user.permission === 'admin' ? 'secondary disabled' : 'secondary'}`}
                            onClick={() => openUserPermissionsModal(user)}
                            disabled={loading || user.permission === 'admin'}
                            title={user.permission === 'admin' ? 'Admin users cannot be edited' : 'Edit user permissions'}
                          >
                            {user.permission === 'admin' ? 'Admin (Read-only)' : 'Edit'}
                          </button>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={5} style={{ textAlign: 'center', color: '#666' }}>
                        No user permissions configured for this workflow
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* User Permissions Modal */}
      {showUserPermissionsModal && editingUser && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>Edit User Permissions</h3>
              <button className="modal-close" onClick={closeUserPermissionsModal}>×</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label>Username</label>
                <input type="text" value={editingUser.username} disabled />
              </div>
              <div className="form-group">
                <label>Email</label>
                <input type="text" value={editingUser.email} disabled />
              </div>
              <div className="form-group">
                <label>Role *</label>
                <select 
                  value={editForm.role} 
                  onChange={(e) => setEditForm(prev => ({ ...prev, role: e.target.value as 'admin' | 'manager' | 'viewer' }))}
                  disabled={editingUser?.permission === 'admin'}
                >
                  <option value="viewer">Viewer</option>
                  <option value="manager">Manager</option>
                  <option value="admin">Admin</option>
                </select>
                {editingUser?.permission === 'admin' && (
                  <small style={{ color: '#856404', display: 'block', marginTop: '0.25rem' }}>
                    Admin users cannot have their role changed
                  </small>
                )}
              </div>
              <div className="form-group">
                <label>
                  <input 
                    type="checkbox" 
                    checked={editForm.is_active} 
                    onChange={(e) => setEditForm(prev => ({ ...prev, is_active: e.target.checked }))}
                  />
                  Active
                </label>
              </div>
            </div>
            <div className="modal-footer">
              <button className="cancel-button" onClick={closeUserPermissionsModal}>Cancel</button>
              <button className="add-button" onClick={handleUpdateUserPermissions} disabled={loading}>
                {loading ? 'Updating...' : 'Update Permissions'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AssignWorkflowsPage; 