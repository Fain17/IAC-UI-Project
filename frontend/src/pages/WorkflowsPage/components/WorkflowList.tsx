import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import tokenManager from '../../../utils/tokenManager';
import './WorkflowList.css';

interface Workflow {
  id: string;
  name: string;
  description?: string;
  user_id: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  steps: any[];
  access_type?: string;
  workflow_permission?: string;
  user_role?: string;
  effective_permissions?: {
    read: boolean;
    write: boolean;
    delete: boolean;
    execute: boolean;
  };
  shared_at?: string;
  last_updated?: string;
  shared_groups?: any[];
  total_groups_shared?: number;
}

interface WorkflowListResponse {
  success: boolean;
  workflows: Workflow[];
  count: number;
  permission_summary: {
    total_workflows: number;
    owned_workflows: number;
    shared_workflows: number;
    total_groups_shared: number;
    user_role: string;
    can_create: boolean;
    can_delete: boolean;
    can_execute: boolean;
  };
  own_count: number;
  team_count: number;
}

const API = axios.create({
  baseURL: 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' }
});

// Add request interceptor to automatically include JWT token
API.interceptors.request.use(config => {
  const token = tokenManager.getToken();
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

const WorkflowList: React.FC = () => {
  const navigate = useNavigate();
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [permissionSummary, setPermissionSummary] = useState<WorkflowListResponse['permission_summary'] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchWorkflows();
  }, []);

  const fetchWorkflows = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await API.get<WorkflowListResponse>('/workflow/list');
      
      if (response.data.success) {
        setWorkflows(response.data.workflows);
        setPermissionSummary(response.data.permission_summary);
      } else {
        setError('Failed to fetch workflows');
      }
    } catch (err: any) {
      console.error('Error fetching workflows:', err);
      setError(err.response?.data?.detail || 'Failed to fetch workflows');
    } finally {
      setLoading(false);
    }
  };

  const handleWorkflowClick = (workflowId: string) => {
    navigate(`/workflows/${workflowId}`);
  };



  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="workflow-list">
        <div className="loading-spinner"></div>
        <p>Loading workflows...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="workflow-list">
        <div className="error-message">
          {error}
          <button onClick={fetchWorkflows} className="retry-button">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="workflow-list">
      <div className="workflow-list-header">
        <h2>Workflows ({workflows.length})</h2>
        {permissionSummary && (
          <div className="permission-summary">
            <div className="summary-stats">
              <div className="summary-stat">
                <span className="stat-label">Total:</span>
                <span className="stat-value">{permissionSummary.total_workflows}</span>
              </div>
              <div className="summary-stat">
                <span className="stat-label">Owned:</span>
                <span className="stat-value">{permissionSummary.owned_workflows}</span>
              </div>
              <div className="summary-stat">
                <span className="stat-label">Shared:</span>
                <span className="stat-value">{permissionSummary.shared_workflows}</span>
              </div>
              <div className="summary-stat">
                <span className="stat-label">Role:</span>
                <span className="stat-value">{permissionSummary.user_role}</span>
              </div>
            </div>
          </div>
        )}
        {workflows.length === 0 && (
          <p className="no-workflows">No workflows found. Create your first workflow to get started.</p>
        )}
      </div>

      {workflows.length > 0 && (
        <div className="workflow-grid">
          {workflows.map((workflow) => (
            <div 
              key={workflow.id} 
              className="workflow-card clickable"
              onClick={() => handleWorkflowClick(workflow.id)}
            >
              <div className="workflow-card-header">
                <h3 className="workflow-title">
                  {workflow.name}
                </h3>
                <div className="workflow-status">
                  <span className={`status-badge ${workflow.is_active ? 'active' : 'inactive'}`}>
                    {workflow.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
              </div>
              
              {workflow.description && (
                <p className="workflow-description">{workflow.description}</p>
              )}
              
              <div className="workflow-details">
                <div className="workflow-detail">
                  <span className="detail-label">Steps:</span>
                  <span className="detail-value">{workflow.steps.length}</span>
                </div>
                <div className="workflow-detail">
                  <span className="detail-label">Created:</span>
                  <span className="detail-value">{formatDate(workflow.created_at)}</span>
                </div>
                <div className="workflow-detail">
                  <span className="detail-label">Updated:</span>
                  <span className="detail-value">{formatDate(workflow.updated_at)}</span>
                </div>
                {workflow.access_type && (
                  <div className="workflow-detail">
                    <span className="detail-label">Access:</span>
                    <span className="detail-value">{workflow.access_type}</span>
                  </div>
                )}
                {workflow.total_groups_shared && workflow.total_groups_shared > 0 && (
                  <div className="workflow-detail">
                    <span className="detail-label">Shared Groups:</span>
                    <span className="detail-value">{workflow.total_groups_shared}</span>
                  </div>
                )}
              </div>

              {/* Click hint */}
              <div className="click-hint">
                <span className="hint-text">Click to view and edit workflow steps</span>
              </div>

              {/* Permissions Summary */}
              {workflow.effective_permissions && (
                <div className="workflow-permissions">
                  <div className="permissions-title">Permissions:</div>
                  <div className="permissions-grid">
                    {workflow.effective_permissions.read && (
                      <span className="permission-badge read">Read</span>
                    )}
                    {workflow.effective_permissions.write && (
                      <span className="permission-badge write">Write</span>
                    )}
                    {workflow.effective_permissions.execute && (
                      <span className="permission-badge execute">Execute</span>
                    )}
                    {workflow.effective_permissions.delete && (
                      <span className="permission-badge delete">Delete</span>
                    )}
                  </div>
                </div>
              )}


            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default WorkflowList; 