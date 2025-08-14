import React, { useState, useEffect } from 'react';
import { 
  getWorkflowSchedules, 
  createWorkflowSchedule, 
  updateWorkflowSchedule, 
  deleteWorkflowSchedule,
  getScheduleStatus,
  WorkflowSchedule,
  CreateWorkflowScheduleRequest,
  UpdateWorkflowScheduleRequest,
  ScheduleStatus,
  SchedulerStatus
} from '../api';
import './WorkflowSchedules.css';

interface WorkflowSchedulesProps {
  workflowId: string;
  workflowName: string;
  onClose: () => void;
}

const WorkflowSchedules: React.FC<WorkflowSchedulesProps> = ({ workflowId, workflowName, onClose }) => {
  const [schedules, setSchedules] = useState<WorkflowSchedule[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  
  // Status states
  const [scheduleStatuses, setScheduleStatuses] = useState<ScheduleStatus[]>([]);
  const [schedulerStatus, setSchedulerStatus] = useState<SchedulerStatus | null>(null);
  const [statusLoading, setStatusLoading] = useState(false);
  
  // Schedule details popup state
  const [showScheduleDetailsModal, setShowScheduleDetailsModal] = useState(false);
  const [selectedScheduleForDetails, setSelectedScheduleForDetails] = useState<WorkflowSchedule | null>(null);
  
  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingSchedule, setEditingSchedule] = useState<WorkflowSchedule | null>(null);
  
  // Form states
  const [createForm, setCreateForm] = useState<CreateWorkflowScheduleRequest>({
    workflow_id: workflowId,
    schedule_type: 'cron',
    schedule_value: '',
    description: '',
    continue_on_failure: false
  });
  
  const [editForm, setEditForm] = useState<UpdateWorkflowScheduleRequest>({
    schedule_type: '',
    schedule_value: '',
    description: '',
    continue_on_failure: false
  });

  useEffect(() => {
    loadSchedules();
    loadScheduleStatuses();
  }, [workflowId]);

  const loadSchedules = async () => {
    try {
      setLoading(true);
      const response = await getWorkflowSchedules(workflowId);
      if (response.data.success) {
        setSchedules(response.data.schedules || []);
      }
    } catch (error: any) {
      setMessage({ type: 'error', text: 'Failed to load schedules: ' + (error.response?.data?.detail || error.message) });
    } finally {
      setLoading(false);
    }
  };

  const loadScheduleStatuses = async () => {
    try {
      setStatusLoading(true);
      const response = await getScheduleStatus(workflowId);
      if (response.data.success) {
        setScheduleStatuses(response.data.user_schedules || []);
        setSchedulerStatus(response.data.scheduler_status || null);
      }
    } catch (error: any) {
      console.error('Failed to load schedule statuses:', error);
      // Don't show error message for status loading as it's not critical
    } finally {
      setStatusLoading(false);
    }
  };

  const openScheduleDetails = (schedule: WorkflowSchedule) => {
    setSelectedScheduleForDetails(schedule);
    setShowScheduleDetailsModal(true);
  };

  const handleCreateSchedule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createForm.schedule_value.trim() || !createForm.description.trim()) {
      setMessage({ type: 'error', text: 'Please fill in all required fields' });
      return;
    }

    try {
      setLoading(true);
      await createWorkflowSchedule(createForm);
      setMessage({ type: 'success', text: 'Schedule created successfully!' });
      setShowCreateModal(false);
      setCreateForm({
        workflow_id: workflowId,
        schedule_type: 'cron',
        schedule_value: '',
        description: '',
        continue_on_failure: false
      });
      await loadSchedules();
      await loadScheduleStatuses();
    } catch (error: any) {
      setMessage({ type: 'error', text: 'Failed to create schedule: ' + (error.response?.data?.detail || error.message) });
    } finally {
      setLoading(false);
    }
  };

  const handleEditSchedule = (schedule: WorkflowSchedule) => {
    setEditingSchedule(schedule);
    setEditForm({
      schedule_type: schedule.schedule_type,
      schedule_value: schedule.schedule_value,
      description: schedule.description,
      continue_on_failure: schedule.continue_on_failure
    });
    setShowEditModal(true);
  };

  const handleUpdateSchedule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingSchedule || !editForm.schedule_value?.trim() || !editForm.description?.trim()) {
      setMessage({ type: 'error', text: 'Please fill in all required fields' });
      return;
    }

    try {
      setLoading(true);
      await updateWorkflowSchedule(editingSchedule.id, editForm);
      setMessage({ type: 'success', text: 'Schedule updated successfully!' });
      setShowEditModal(false);
      setEditingSchedule(null);
      await loadSchedules();
      await loadScheduleStatuses();
    } catch (error: any) {
      setMessage({ type: 'error', text: 'Failed to update schedule: ' + (error.response?.data?.detail || error.message) });
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteSchedule = async (schedule: WorkflowSchedule) => {
    if (!window.confirm(`Are you sure you want to delete the schedule "${schedule.description}"? This action cannot be undone.`)) {
      return;
    }

    try {
      setLoading(true);
      await deleteWorkflowSchedule(schedule.id);
      setMessage({ type: 'success', text: 'Schedule deleted successfully!' });
      await loadSchedules();
      await loadScheduleStatuses();
    } catch (error: any) {
      setMessage({ type: 'error', text: 'Failed to delete schedule: ' + (error.response?.data?.detail || error.message) });
    } finally {
      setLoading(false);
    }
  };

  const getScheduleTypeLabel = (type: string) => {
    switch (type) {
      case 'cron': return 'Cron Expression';
      case 'interval': return 'Time Interval';
      case 'daily': return 'Daily';
      case 'weekly': return 'Weekly';
      case 'monthly': return 'Monthly';
      default: return type;
    }
  };

  const getScheduleTypeOptions = () => [
    { value: 'cron', label: 'Cron Expression' },
    { value: 'interval', label: 'Time Interval' },
    { value: 'daily', label: 'Daily' },
    { value: 'weekly', label: 'Weekly' },
    { value: 'monthly', label: 'Monthly' }
  ];

  return (
    <div className="workflow-schedules-overlay">
      <div className="workflow-schedules-modal">
        <div className="modal-header">
          <h2>Workflow Schedules: {workflowName}</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        {message && (
          <div className={`message ${message.type === 'success' ? 'success-message' : 'error-message'}`}>
            {message.text}
            <button className="message-close" onClick={() => setMessage(null)}>×</button>
          </div>
        )}

        <div className="modal-body">
          <div className="schedules-header">
            <button 
              className="create-button"
              onClick={() => setShowCreateModal(true)}
              disabled={loading}
            >
              ➕ Create Schedule
            </button>
            <button 
              className="refresh-status-button"
              onClick={loadScheduleStatuses}
              disabled={statusLoading}
            >
              🔄 Refresh Status
            </button>
          </div>

          {/* Scheduler Status Section */}
          {schedulerStatus && (
            <div className="scheduler-status-section">
              <h3>Scheduler Status</h3>
              <div className="status-grid">
                <div className="status-item">
                  <span className="status-label">Scheduler Running:</span>
                  <span className={`status-value ${schedulerStatus.scheduler_running ? 'running' : 'stopped'}`}>
                    {schedulerStatus.scheduler_running ? '✅ Running' : '❌ Stopped'}
                  </span>
                </div>
                <div className="status-item">
                  <span className="status-label">Active Schedules:</span>
                  <span className="status-value">{schedulerStatus.active_schedules}</span>
                </div>
                <div className="status-item">
                  <span className="status-label">Total Tasks:</span>
                  <span className="status-value">{schedulerStatus.total_tasks}</span>
                </div>
              </div>
            </div>
          )}

          {loading && schedules.length === 0 ? (
            <div className="loading">Loading schedules...</div>
          ) : schedules.length === 0 ? (
            <div className="no-schedules">
              <p>No schedules configured for this workflow.</p>
              <p>Create a schedule to automate workflow execution.</p>
            </div>
          ) : (
            <div className="schedules-table">
              <table>
                <thead>
                  <tr>
                    <th>Schedule Type</th>
                    <th>Schedule Value</th>
                    <th>Description</th>
                    <th>Status</th>
                    <th>Created</th>
                  </tr>
                </thead>
                <tbody>
                  {schedules.map((schedule) => {
                    const status = scheduleStatuses.find(s => s.schedule_id === schedule.id);
                    
                    return (
                      <tr 
                        key={schedule.id} 
                        className="clickable-row"
                        onClick={() => openScheduleDetails(schedule)}
                      >
                        <td>
                          <span className="schedule-type-badge">
                            {getScheduleTypeLabel(schedule.schedule_type)}
                          </span>
                        </td>
                        <td>
                          <code className="schedule-value">{schedule.schedule_value}</code>
                        </td>
                        <td>{schedule.description}</td>
                        <td>
                          {status ? (
                            <span className={`status-badge ${status.execution_status === 'executed' ? 'success' : 'info'}`}>
                              {status.execution_status}
                            </span>
                          ) : (
                            <span className="status-badge info">Unknown</span>
                          )}
                        </td>
                        <td>{new Date(schedule.created_at).toLocaleDateString()}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Create Schedule Modal */}
        {showCreateModal && (
          <div className="modal-overlay">
            <div className="modal-content">
              <div className="modal-header">
                <h3>Create Workflow Schedule</h3>
                <button className="modal-close" onClick={() => setShowCreateModal(false)}>×</button>
              </div>
              <form onSubmit={handleCreateSchedule}>
                <div className="modal-body">
                  <div className="form-group">
                    <label>Schedule Type *</label>
                    <select 
                      value={createForm.schedule_type} 
                      onChange={(e) => setCreateForm(prev => ({ ...prev, schedule_type: e.target.value }))}
                      required
                    >
                      {getScheduleTypeOptions().map(option => (
                        <option key={option.value} value={option.value}>{option.label}</option>
                      ))}
                    </select>
                  </div>
                  
                  <div className="form-group">
                    <label>Schedule Value *</label>
                    <input 
                      type="text" 
                      value={createForm.schedule_value} 
                      onChange={(e) => setCreateForm(prev => ({ ...prev, schedule_value: e.target.value }))}
                      placeholder={createForm.schedule_type === 'cron' ? '0 0 * * *' : 'Enter schedule value'}
                      required
                    />
                    <small>
                      {createForm.schedule_type === 'cron' && 'Format: minute hour day month weekday (e.g., 0 0 * * *)'}
                      {createForm.schedule_type === 'interval' && 'Format: 1h, 30m, 1d (e.g., 1h for every hour)'}
                      {createForm.schedule_type === 'daily' && 'Format: HH:MM (e.g., 09:00 for 9 AM daily)'}
                      {createForm.schedule_type === 'weekly' && 'Format: day HH:MM (e.g., monday 09:00)'}
                      {createForm.schedule_type === 'monthly' && 'Format: day HH:MM (e.g., 1 09:00 for 1st of month at 9 AM)'}
                    </small>
                  </div>
                  
                  <div className="form-group">
                    <label>Description *</label>
                    <textarea 
                      value={createForm.description} 
                      onChange={(e) => setCreateForm(prev => ({ ...prev, description: e.target.value }))}
                      placeholder="Describe what this schedule does"
                      rows={3}
                      required
                    />
                  </div>
                  
                  <div className="form-group">
                    <label>
                      <input 
                        type="checkbox" 
                        checked={createForm.continue_on_failure} 
                        onChange={(e) => setCreateForm(prev => ({ ...prev, continue_on_failure: e.target.checked }))}
                      />
                      Continue on Failure
                    </label>
                    <small>If checked, the workflow will continue running even if individual steps fail</small>
                  </div>
                </div>
                <div className="modal-footer">
                  <button type="button" className="cancel-button" onClick={() => setShowCreateModal(false)}>Cancel</button>
                  <button type="submit" className="add-button" disabled={loading}>
                    {loading ? 'Creating...' : 'Create Schedule'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Edit Schedule Modal */}
        {showEditModal && editingSchedule && (
          <div className="modal-overlay">
            <div className="modal-content">
              <div className="modal-header">
                <h3>Edit Workflow Schedule</h3>
                <button className="modal-close" onClick={() => setShowEditModal(false)}>×</button>
              </div>
              <form onSubmit={handleUpdateSchedule}>
                <div className="modal-body">
                  <div className="form-group">
                    <label>Schedule Type *</label>
                    <select 
                      value={editForm.schedule_type || ''} 
                      onChange={(e) => setEditForm(prev => ({ ...prev, schedule_type: e.target.value }))}
                      required
                    >
                      {getScheduleTypeOptions().map(option => (
                        <option key={option.value} value={option.value}>{option.label}</option>
                      ))}
                    </select>
                  </div>
                  
                  <div className="form-group">
                    <label>Schedule Value *</label>
                    <input 
                      type="text" 
                      value={editForm.schedule_value || ''} 
                      onChange={(e) => setEditForm(prev => ({ ...prev, schedule_value: e.target.value }))}
                      placeholder="Enter schedule value"
                      required
                    />
                  </div>
                  
                  <div className="form-group">
                    <label>Description *</label>
                    <textarea 
                      value={editForm.description || ''} 
                      onChange={(e) => setEditForm(prev => ({ ...prev, description: e.target.value }))}
                      placeholder="Describe what this schedule does"
                      rows={3}
                      required
                    />
                  </div>
                  
                  <div className="form-group">
                    <label>
                      <input 
                        type="checkbox" 
                        checked={editForm.continue_on_failure || false} 
                        onChange={(e) => setEditForm(prev => ({ ...prev, continue_on_failure: e.target.checked }))}
                      />
                      Continue on Failure
                    </label>
                  </div>
                </div>
                <div className="modal-footer">
                  <button type="button" className="cancel-button" onClick={() => setShowEditModal(false)}>Cancel</button>
                  <button type="submit" className="add-button" disabled={loading}>
                    {loading ? 'Updating...' : 'Update Schedule'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Schedule Details Modal */}
        {showScheduleDetailsModal && selectedScheduleForDetails && (
          <div className="modal-overlay">
            <div className="modal-content schedule-details-modal">
              <div className="modal-header">
                <h3>Schedule Details</h3>
                <button className="modal-close" onClick={() => setShowScheduleDetailsModal(false)}>×</button>
              </div>
              
              <div className="modal-body">
                <div className="schedule-details-grid">
                  <div className="detail-section">
                    <h4>Basic Information</h4>
                    <div className="detail-item">
                      <span className="detail-label">Schedule Type:</span>
                      <span className="detail-value">
                        {getScheduleTypeLabel(selectedScheduleForDetails.schedule_type)}
                      </span>
                    </div>
                    <div className="detail-item">
                      <span className="detail-label">Schedule Value:</span>
                      <span className="detail-value">
                        <code>{selectedScheduleForDetails.schedule_value}</code>
                      </span>
                    </div>
                    <div className="detail-item">
                      <span className="detail-label">Description:</span>
                      <span className="detail-value">{selectedScheduleForDetails.description}</span>
                    </div>
                    <div className="detail-item">
                      <span className="detail-label">Continue on Failure:</span>
                      <span className="detail-value">
                        <span className={`status-badge ${selectedScheduleForDetails.continue_on_failure ? 'success' : 'warning'}`}>
                          {selectedScheduleForDetails.continue_on_failure ? 'Yes' : 'No'}
                        </span>
                      </span>
                    </div>
                    <div className="detail-item">
                      <span className="detail-label">Created:</span>
                      <span className="detail-value">
                        {new Date(selectedScheduleForDetails.created_at).toLocaleString()}
                      </span>
                    </div>
                  </div>

                  <div className="detail-section">
                    <h4>Execution Status</h4>
                    {(() => {
                      const status = scheduleStatuses.find(s => s.schedule_id === selectedScheduleForDetails.id);
                      const schedulerInfo = schedulerStatus?.schedules.find(s => s.schedule_id === selectedScheduleForDetails.id);
                      
                      if (!status) {
                        return <p className="text-muted">No status information available</p>;
                      }

                      return (
                        <>
                          <div className="detail-item">
                            <span className="detail-label">Status:</span>
                            <span className={`status-badge ${status.execution_status === 'executed' ? 'success' : 'info'}`}>
                              {status.execution_status}
                            </span>
                          </div>
                          <div className="detail-item">
                            <span className="detail-label">Last Execution:</span>
                            <span className="detail-value">
                              {status.last_execution ? new Date(status.last_execution).toLocaleString() : 'Never'}
                            </span>
                          </div>
                          {schedulerInfo && (
                            <div className="detail-item">
                              <span className="detail-label">Next Run:</span>
                              <span className="detail-value">
                                {new Date(schedulerInfo.next_run).toLocaleString()}
                              </span>
                            </div>
                          )}
                          {status.execution_details && (
                            <>
                              <div className="detail-item">
                                <span className="detail-label">Execution Result:</span>
                                <span className={`detail-value ${status.execution_details.success ? 'success' : 'error'}`}>
                                  {status.execution_details.success ? '✅ Success' : '❌ Failed'}
                                </span>
                              </div>
                              {status.execution_details.execution_time !== undefined && (
                                <div className="detail-item">
                                  <span className="detail-label">Execution Time:</span>
                                  <span className="detail-value">{status.execution_details.execution_time}ms</span>
                                </div>
                              )}
                              {status.execution_details.output && (
                                <div className="detail-item">
                                  <span className="detail-label">Output:</span>
                                  <span className="detail-value output-text">{status.execution_details.output}</span>
                                </div>
                              )}
                              {status.execution_details.error && (
                                <div className="detail-item">
                                  <span className="detail-label">Error:</span>
                                  <span className="detail-value error-text">{status.execution_details.error}</span>
                                </div>
                              )}
                            </>
                          )}
                        </>
                      );
                    })()}
                  </div>
                </div>
              </div>

              <div className="modal-footer">
                <button 
                  className="action-button edit"
                  onClick={() => {
                    setShowScheduleDetailsModal(false);
                    handleEditSchedule(selectedScheduleForDetails);
                  }}
                  disabled={loading}
                >
                  ✏️ Edit Schedule
                </button>
                <button 
                  className="action-button delete"
                  onClick={() => {
                    setShowScheduleDetailsModal(false);
                    handleDeleteSchedule(selectedScheduleForDetails);
                  }}
                  disabled={loading}
                >
                  🗑️ Delete Schedule
                </button>
                <button 
                  className="cancel-button"
                  onClick={() => setShowScheduleDetailsModal(false)}
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default WorkflowSchedules; 