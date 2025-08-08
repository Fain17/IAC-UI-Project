import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import tokenManager from '../../../utils/tokenManager';
import './WorkflowList.css';

interface Workflow {
  id: string;
  name: string;
  description?: string;
  user_id: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  steps: any[];
}

interface WorkflowListResponse {
  success: boolean;
  workflows: Workflow[];
  count: number;
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
                <h3>{workflow.name}</h3>
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
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default WorkflowList; 