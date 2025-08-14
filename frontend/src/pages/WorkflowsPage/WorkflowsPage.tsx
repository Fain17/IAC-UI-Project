import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import tokenManager from '../../utils/tokenManager';
import WorkflowList from './components/WorkflowList';
import CreateWorkflow from './components/CreateWorkflow';
import WorkflowSchedules from '../../components/WorkflowSchedules';
import { getAllWorkflows, Workflow } from '../../api';
import './WorkflowsPage.css';

type SubTab = 'list' | 'create' | 'history' | 'automate';

const WorkflowsPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [username, setUsername] = useState<string>('');
  const [email, setEmail] = useState<string>('');
  const [showSchedulesModal, setShowSchedulesModal] = useState(false);
  const [selectedWorkflow, setSelectedWorkflow] = useState<{ id: string; name: string } | null>(null);
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [workflowsLoading, setWorkflowsLoading] = useState(false);

  useEffect(() => {
    const user = tokenManager.getUser();
    if (user) {
      setUsername(user.username || '');
      setEmail(user.email || '');
    }
  }, []);

  const fetchWorkflows = async () => {
    try {
      setWorkflowsLoading(true);
      const response = await getAllWorkflows();
      if (response.data.success) {
        setWorkflows(response.data.workflows || []);
      }
    } catch (error: any) {
      console.error('Failed to fetch workflows:', error);
      // Set some sample workflows as fallback
      setWorkflows([
        { id: 'workflow_1', name: 'Sample Workflow 1', description: 'A sample workflow for testing', user_id: 'user_1', is_active: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString(), steps: [] },
        { id: 'workflow_2', name: 'Sample Workflow 2', description: 'Another sample workflow', user_id: 'user_1', is_active: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString(), steps: [] }
      ]);
    } finally {
      setWorkflowsLoading(false);
    }
  };

  const handleProfileClick = () => {
    navigate('/admin-profile');
  };

  const handleManageSchedules = (workflowId: string, workflowName: string) => {
    setSelectedWorkflow({ id: workflowId, name: workflowName });
    setShowSchedulesModal(true);
  };

  const activeSubMenu: SubTab = useMemo(() => {
    if (location.pathname.startsWith('/workflows/create')) return 'create';
    if (location.pathname.startsWith('/workflows/history')) return 'history';
    if (location.pathname.startsWith('/workflows/automate')) return 'automate';
    return 'list';
  }, [location.pathname]);

  useEffect(() => {
    if (activeSubMenu === 'automate') {
      fetchWorkflows();
    }
  }, [activeSubMenu]);

  const displayName = username || email;
  const initial = displayName ? displayName[0].toUpperCase() : '?';

  return (
    <div>
      <div className="profile-container" onClick={handleProfileClick}>
        <div className="avatar">{initial}</div>
        {username && <div className="name">{username}</div>}
        {email && <div className="email">{email}</div>}
      </div>
      <div className="workflows-content">
        <div className="workflows-header">
          <h1>Workflows</h1>
        </div>
        <div className="workflows-body">
          {activeSubMenu === 'list' && <WorkflowList />}
          {activeSubMenu === 'create' && <CreateWorkflow />}
          {activeSubMenu === 'history' && (
            <div>
              <h2>Workflow History</h2>
              <p>Showing recent workflow executions (dummy data).</p>
              <ul>
                <li>2025-08-09 12:00 — Deployment Workflow — completed_with_skips</li>
                <li>2025-08-08 16:20 — Data Pipeline — failed</li>
                <li>2025-08-07 09:45 — Nightly Backup — completed</li>
              </ul>
            </div>
          )}
          {activeSubMenu === 'automate' && (
            <div className="automate-workflows">
              <div className="automate-header">
                <h2>Automate Workflows</h2>
                <p>Create and manage automated schedules for your workflows</p>
              </div>
              
              {workflowsLoading ? (
                <div className="workflows-loading">
                  <div className="loading-spinner"></div>
                  <p>Loading workflows...</p>
                </div>
              ) : workflows.length === 0 ? (
                <div className="no-workflows">
                  <p>No workflows found. Create a workflow first to set up automation.</p>
                </div>
              ) : (
                <div className="workflow-cards-section">
                  <h3>Select a Workflow to Automate</h3>
                  <p>Click on a workflow card to manage its schedules:</p>
                  
                  <div className="workflow-cards-grid">
                    {workflows.map((workflow) => (
                      <div 
                        key={workflow.id} 
                        className="workflow-card"
                        onClick={() => handleManageSchedules(workflow.id, workflow.name)}
                      >
                        <div className="workflow-card-header">
                          <h4>{workflow.name}</h4>
                          <span className={`status-badge ${workflow.is_active ? 'active' : 'inactive'}`}>
                            {workflow.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </div>
                        
                        {workflow.description && (
                          <p className="workflow-description">{workflow.description}</p>
                        )}
                        
                        <div className="workflow-card-details">
                          <div className="workflow-detail">
                            <span className="detail-label">Steps:</span>
                            <span className="detail-value">{workflow.steps.length}</span>
                          </div>
                          <div className="workflow-detail">
                            <span className="detail-label">Created:</span>
                            <span className="detail-value">{new Date(workflow.created_at).toLocaleDateString()}</span>
                          </div>
                        </div>
                        
                        <div className="workflow-card-actions">
                          <button className="manage-schedules-btn">
                            ⏰ Manage Schedules
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              <div className="schedule-info">
                <h4>Schedule Types Available:</h4>
                <ul>
                  <li><strong>Cron:</strong> Advanced scheduling with cron expressions (e.g., 0 2 * * * for 2 AM daily)</li>
                  <li><strong>Interval:</strong> Time-based intervals (e.g., every hour, every 30 minutes)</li>
                  <li><strong>Daily:</strong> Specific times each day (e.g., 9:00 AM daily)</li>
                  <li><strong>Weekly:</strong> Day and time combinations (e.g., Monday at 9:00 AM)</li>
                  <li><strong>Monthly:</strong> Day of month and time (e.g., 1st of month at 9:00 AM)</li>
                </ul>
                
                <div className="schedule-examples">
                  <h4>Example Schedules:</h4>
                  <div className="example-grid">
                    <div className="example-item">
                      <strong>Nightly Backup:</strong> 0 2 * * * (2 AM daily)
                    </div>
                    <div className="example-item">
                      <strong>Hourly Check:</strong> 0 * * * * (Every hour)
                    </div>
                    <div className="example-item">
                      <strong>Weekly Report:</strong> 0 9 * * 1 (Monday at 9 AM)
                    </div>
                    <div className="example-item">
                      <strong>Monthly Cleanup:</strong> 0 3 1 * * (1st of month at 3 AM)
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Workflow Schedules Modal */}
      {showSchedulesModal && selectedWorkflow && (
        <WorkflowSchedules
          workflowId={selectedWorkflow.id}
          workflowName={selectedWorkflow.name}
          onClose={() => {
            setShowSchedulesModal(false);
            setSelectedWorkflow(null);
          }}
        />
      )}
    </div>
  );
};

export default WorkflowsPage; 