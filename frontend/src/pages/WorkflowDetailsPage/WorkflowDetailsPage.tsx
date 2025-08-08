import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  getWorkflowSteps, 
  addWorkflowStep, 
  deleteWorkflowStep,
  updateWorkflowStepById,
  uploadFileToStep,
  uploadZipToStep,
  createScriptForStep,
  WorkflowStep,
  CreateStepRequest,
  UpdateStepRequest,
  WorkflowStepsResponse
} from '../../api';
import './WorkflowDetailsPage.css';

interface Workflow {
  id: string;
  name: string;
  description?: string;
  user_id: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  steps: WorkflowStep[];
}

type FileUploadMethod = 'none' | 'file' | 'zip' | 'script';

const WorkflowDetailsPage: React.FC = () => {
  const { workflowId } = useParams<{ workflowId: string }>();
  const navigate = useNavigate();
  const [workflow, setWorkflow] = useState<Workflow | null>(null);
  const [steps, setSteps] = useState<WorkflowStep[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddStepModal, setShowAddStepModal] = useState(false);
  const [showEditStepModal, setShowEditStepModal] = useState(false);
  const [editingStep, setEditingStep] = useState<WorkflowStep | null>(null);
  const [newStep, setNewStep] = useState<CreateStepRequest>({
    name: '',
    description: '',
    script_type: 'python',
    script_filename: '',
    run_command: '',
    dependencies: [],
    parameters: {},
    is_active: true
  });
  const [editStep, setEditStep] = useState<UpdateStepRequest>({
    name: '',
    description: '',
    script_type: 'python',
    script_filename: '',
    run_command: '',
    dependencies: [],
    parameters: {},
    is_active: true
  });
  const [fileUploadMethod, setFileUploadMethod] = useState<FileUploadMethod>('none');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedZipFile, setSelectedZipFile] = useState<File | null>(null);
  const [scriptContent, setScriptContent] = useState('');

  useEffect(() => {
    if (workflowId) {
      fetchWorkflowDetails();
    }
  }, [workflowId]);

  const fetchWorkflowDetails = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await getWorkflowSteps(workflowId!);
      
      if (response.data.success) {
        setWorkflow({
          id: response.data.workflow_id,
          name: response.data.workflow_name,
          steps: response.data.steps,
          user_id: 0,
          is_active: true,
          created_at: '',
          updated_at: ''
        });
        setSteps(response.data.steps);
      } else {
        setError('Failed to fetch workflow details');
      }
    } catch (err: any) {
      console.error('Error fetching workflow details:', err);
      setError(err.response?.data?.detail || 'Failed to fetch workflow details');
    } finally {
      setLoading(false);
    }
  };

  const handleAddStep = async () => {
    if (!newStep.name.trim()) {
      setError('Step name is required');
      return;
    }

    // Validate script filename when script upload method is selected
    if (fileUploadMethod === 'script' && !newStep.script_filename?.trim()) {
      setError('Script filename is required when creating a script');
      return;
    }

    // Validate script content when script upload method is selected
    if (fileUploadMethod === 'script' && !scriptContent.trim()) {
      setError('Script content is required when creating a script');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      // First, create the step
      const response = await addWorkflowStep(workflowId!, newStep);
      
      if (response.data.success) {
        const createdStep = response.data.step;
        setSteps([...steps, createdStep]);

        // Handle file upload based on selected method
        if (fileUploadMethod !== 'none') {
          try {
            switch (fileUploadMethod) {
              case 'file':
                if (selectedFile) {
                  await uploadFileToStep(workflowId!, createdStep.id, selectedFile);
                }
                break;
              case 'zip':
                if (selectedZipFile) {
                  await uploadZipToStep(workflowId!, createdStep.id, selectedZipFile);
                }
                break;
              case 'script':
                if (scriptContent.trim() && newStep.script_filename?.trim()) {
                  await createScriptForStep(workflowId!, createdStep.id, newStep.script_filename, scriptContent);
                }
                break;
            }
          } catch (uploadError: any) {
            console.error('Error uploading file:', uploadError);
            // Don't fail the entire step creation if file upload fails
            setError(`Step created but file upload failed: ${uploadError.response?.data?.detail || 'Unknown error'}`);
          }
        }

        setShowAddStepModal(false);
        resetForm();
      } else {
        setError('Failed to add step');
      }
    } catch (err: any) {
      console.error('Error adding step:', err);
      setError(err.response?.data?.detail || 'Failed to add step');
    } finally {
      setLoading(false);
    }
  };

  const handleEditStep = async () => {
    if (!editingStep) return;

    if (!editStep.name?.trim()) {
      setError('Step name is required');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await updateWorkflowStepById(workflowId!, editingStep.id, editStep);
      
      if (response.data.success) {
        // Update the step in the local state
        setSteps(steps.map(step => 
          step.id === editingStep.id 
            ? { ...step, ...response.data.updated_step }
            : step
        ));
        
        setShowEditStepModal(false);
        setEditingStep(null);
        resetEditForm();
      } else {
        setError('Failed to update step');
      }
    } catch (err: any) {
      console.error('Error updating step:', err);
      setError(err.response?.data?.detail || 'Failed to update step');
    } finally {
      setLoading(false);
    }
  };

  const openEditStepModal = (step: WorkflowStep) => {
    setEditingStep(step);
    setEditStep({
      name: step.name,
      description: step.description || '',
      order: step.order,
      script_type: step.script_type || 'python',
      script_filename: step.script_filename || '',
      run_command: step.run_command || '',
      dependencies: step.dependencies || [],
      parameters: step.parameters || {},
      is_active: step.is_active
    });
    setShowEditStepModal(true);
  };

  const resetEditForm = () => {
    setEditStep({
      name: '',
      description: '',
      script_type: 'python',
      script_filename: '',
      run_command: '',
      dependencies: [],
      parameters: {},
      is_active: true
    });
    setEditingStep(null);
  };

  const resetForm = () => {
    setNewStep({
      name: '',
      description: '',
      script_type: 'python',
      script_filename: '',
      run_command: '',
      dependencies: [],
      parameters: {},
      is_active: true
    });
    setFileUploadMethod('none');
    setSelectedFile(null);
    setSelectedZipFile(null);
    setScriptContent('');
  };

  const handleDeleteStep = async (stepOrder: number) => {
    if (!window.confirm('Are you sure you want to delete this step?')) {
      return;
    }

    try {
      const response = await deleteWorkflowStep(workflowId!, stepOrder);
      
      if (response.data.success) {
        setSteps(steps.filter(step => step.order !== stepOrder));
      } else {
        setError('Failed to delete step');
      }
    } catch (err: any) {
      console.error('Error deleting step:', err);
      setError(err.response?.data?.detail || 'Failed to delete step');
    }
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
      <div className="workflow-details-page">
        <div className="loading-spinner"></div>
        <p>Loading workflow details...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="workflow-details-page">
        <div className="error-message">
          {error}
          <button onClick={fetchWorkflowDetails} className="retry-button">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="workflow-details-page">
      <div className="workflow-details-header">
        <button onClick={() => navigate('/workflows')} className="back-button">
          ← Back to Workflows
        </button>
        <h1>{workflow?.name}</h1>
        {workflow?.description && (
          <p className="workflow-description">{workflow.description}</p>
        )}
      </div>

      <div className="workflow-details-content">
        <div className="steps-section">
          <div className="steps-header">
            <h2>Steps ({steps.length})</h2>
            <button 
              onClick={() => setShowAddStepModal(true)}
              className="add-step-button"
            >
              + Add Step
            </button>
          </div>

          {steps.length === 0 ? (
            <div className="no-steps">
              <p>No steps added yet. Click "Add Step" to get started.</p>
            </div>
          ) : (
            <div className="steps-grid">
              {steps.map((step) => (
                <div key={step.id} className="step-card">
                  <div className="step-card-header">
                    <h3>{step.name}</h3>
                    <div className="step-status">
                      <span className={`status-badge ${step.is_active ? 'active' : 'inactive'}`}>
                        {step.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                  </div>
                  
                  {step.description && (
                    <p className="step-description">{step.description}</p>
                  )}
                  
                  <div className="step-details">
                    <div className="step-detail">
                      <span className="detail-label">Order:</span>
                      <span className="detail-value">{step.order}</span>
                    </div>
                    {step.script_type && (
                      <div className="step-detail">
                        <span className="detail-label">Script Type:</span>
                        <span className="detail-value">{step.script_type}</span>
                      </div>
                    )}
                    {step.script_filename && (
                      <div className="step-detail">
                        <span className="detail-label">Script File:</span>
                        <span className="detail-value">{step.script_filename}</span>
                      </div>
                    )}
                    {step.run_command && (
                      <div className="step-detail">
                        <span className="detail-label">Run Command:</span>
                        <span className="detail-value">{step.run_command}</span>
                      </div>
                    )}
                    {step.dependencies && step.dependencies.length > 0 && (
                      <div className="step-detail">
                        <span className="detail-label">Dependencies:</span>
                        <span className="detail-value">{step.dependencies.join(', ')}</span>
                      </div>
                    )}
                    <div className="step-detail">
                      <span className="detail-label">Created:</span>
                      <span className="detail-value">{formatDate(step.created_at)}</span>
                    </div>
                  </div>

                  <div className="step-actions">
                    <button 
                      className="action-button edit"
                      onClick={() => openEditStepModal(step)}
                    >
                      Edit
                    </button>
                    <button 
                      className="action-button delete"
                      onClick={() => handleDeleteStep(step.order)}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Add Step Modal */}
      {showAddStepModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>Add New Step</h3>
              <button 
                onClick={() => {
                  setShowAddStepModal(false);
                  resetForm();
                }}
                className="close-button"
              >
                ×
              </button>
            </div>
            
            <div className="modal-body">
              <div className="form-group">
                <label htmlFor="stepName">Step Name *</label>
                <input
                  type="text"
                  id="stepName"
                  value={newStep.name}
                  onChange={(e) => setNewStep({...newStep, name: e.target.value})}
                  placeholder="Enter step name"
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="stepDescription">Description</label>
                <textarea
                  id="stepDescription"
                  value={newStep.description || ''}
                  onChange={(e) => setNewStep({...newStep, description: e.target.value})}
                  placeholder="Enter step description (optional)"
                  rows={3}
                />
              </div>

              <div className="form-group">
                <label htmlFor="scriptType">Script Type</label>
                <select
                  id="scriptType"
                  value={newStep.script_type}
                  onChange={(e) => setNewStep({...newStep, script_type: e.target.value as 'python' | 'nodejs'})}
                >
                  <option value="python">Python</option>
                  <option value="nodejs">Node.js</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="scriptFilename">
                  Script Filename {fileUploadMethod === 'script' && <span className="required">*</span>}
                </label>
                <input
                  type="text"
                  id="scriptFilename"
                  value={newStep.script_filename || ''}
                  onChange={(e) => setNewStep({...newStep, script_filename: e.target.value})}
                  placeholder="e.g., deploy.py"
                  required={fileUploadMethod === 'script'}
                />
              </div>

              <div className="form-group">
                <label htmlFor="runCommand">Run Command</label>
                <input
                  type="text"
                  id="runCommand"
                  value={newStep.run_command || ''}
                  onChange={(e) => setNewStep({...newStep, run_command: e.target.value})}
                  placeholder="e.g., python deploy.py"
                />
              </div>

              <div className="form-group">
                <label htmlFor="dependencies">Dependencies (comma-separated)</label>
                <input
                  type="text"
                  id="dependencies"
                  value={newStep.dependencies?.join(', ') || ''}
                  onChange={(e) => setNewStep({
                    ...newStep, 
                    dependencies: e.target.value.split(',').map(d => d.trim()).filter(d => d)
                  })}
                  placeholder="e.g., boto3, requests"
                />
              </div>

              <div className="form-group">
                <label htmlFor="fileUploadMethod">File Upload Method</label>
                <select
                  id="fileUploadMethod"
                  value={fileUploadMethod}
                  onChange={(e) => setFileUploadMethod(e.target.value as FileUploadMethod)}
                >
                  <option value="none">No file upload</option>
                  <option value="file">Upload Single File</option>
                  <option value="zip">Upload ZIP Directory</option>
                  <option value="script">Create Script</option>
                </select>
              </div>

              {/* File Upload Section */}
              {fileUploadMethod === 'file' && (
                <div className="form-group">
                  <label htmlFor="fileUpload">Select File</label>
                  <input
                    type="file"
                    id="fileUpload"
                    onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                    accept="*/*"
                  />
                  {selectedFile && (
                    <p className="file-info">Selected: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(2)} KB)</p>
                  )}
                </div>
              )}

              {fileUploadMethod === 'zip' && (
                <div className="form-group">
                  <label htmlFor="zipUpload">Select ZIP File</label>
                  <input
                    type="file"
                    id="zipUpload"
                    onChange={(e) => setSelectedZipFile(e.target.files?.[0] || null)}
                    accept=".zip"
                  />
                  {selectedZipFile && (
                    <p className="file-info">Selected: {selectedZipFile.name} ({(selectedZipFile.size / 1024).toFixed(2)} KB)</p>
                  )}
                </div>
              )}

              {fileUploadMethod === 'script' && (
                <div className="form-group">
                  <label htmlFor="scriptContent">Script Content</label>
                  <textarea
                    id="scriptContent"
                    value={scriptContent}
                    onChange={(e) => setScriptContent(e.target.value)}
                    placeholder="Enter your script content here..."
                    rows={8}
                    required
                  />
                </div>
              )}
            </div>

            <div className="modal-footer">
              <button 
                onClick={() => {
                  setShowAddStepModal(false);
                  resetForm();
                }}
                className="cancel-button"
              >
                Cancel
              </button>
              <button 
                onClick={handleAddStep}
                className="add-button"
                disabled={loading}
              >
                {loading ? 'Adding...' : 'Add Step'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Step Modal */}
      {showEditStepModal && editingStep && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>Edit Step: {editingStep.name}</h3>
              <button 
                onClick={() => {
                  setShowEditStepModal(false);
                  resetEditForm();
                }}
                className="close-button"
              >
                ×
              </button>
            </div>
            
            <div className="modal-body">
              <div className="form-group">
                <label htmlFor="editStepName">Step Name *</label>
                <input
                  type="text"
                  id="editStepName"
                  value={editStep.name || ''}
                  onChange={(e) => setEditStep({...editStep, name: e.target.value})}
                  placeholder="Enter step name"
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="editStepDescription">Description</label>
                <textarea
                  id="editStepDescription"
                  value={editStep.description || ''}
                  onChange={(e) => setEditStep({...editStep, description: e.target.value})}
                  placeholder="Enter step description (optional)"
                  rows={3}
                />
              </div>

              <div className="form-group">
                <label htmlFor="editStepOrder">Order</label>
                <input
                  type="number"
                  id="editStepOrder"
                  value={editStep.order || 1}
                  onChange={(e) => setEditStep({...editStep, order: parseInt(e.target.value) || 1})}
                  min={1}
                  placeholder="Step order"
                />
              </div>

              <div className="form-group">
                <label htmlFor="editScriptType">Script Type</label>
                <select
                  id="editScriptType"
                  value={editStep.script_type || 'python'}
                  onChange={(e) => setEditStep({...editStep, script_type: e.target.value as 'python' | 'nodejs'})}
                >
                  <option value="python">Python</option>
                  <option value="nodejs">Node.js</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="editScriptFilename">Script Filename</label>
                <input
                  type="text"
                  id="editScriptFilename"
                  value={editStep.script_filename || ''}
                  onChange={(e) => setEditStep({...editStep, script_filename: e.target.value})}
                  placeholder="e.g., deploy.py"
                />
              </div>

              <div className="form-group">
                <label htmlFor="editRunCommand">Run Command</label>
                <input
                  type="text"
                  id="editRunCommand"
                  value={editStep.run_command || ''}
                  onChange={(e) => setEditStep({...editStep, run_command: e.target.value})}
                  placeholder="e.g., python deploy.py"
                />
              </div>

              <div className="form-group">
                <label htmlFor="editDependencies">Dependencies (comma-separated)</label>
                <input
                  type="text"
                  id="editDependencies"
                  value={editStep.dependencies?.join(', ') || ''}
                  onChange={(e) => setEditStep({
                    ...editStep, 
                    dependencies: e.target.value.split(',').map(d => d.trim()).filter(d => d)
                  })}
                  placeholder="e.g., boto3, requests"
                />
              </div>

              <div className="form-group">
                <label htmlFor="editIsActive">Active Status</label>
                <select
                  id="editIsActive"
                  value={editStep.is_active ? 'true' : 'false'}
                  onChange={(e) => setEditStep({...editStep, is_active: e.target.value === 'true'})}
                >
                  <option value="true">Active</option>
                  <option value="false">Inactive</option>
                </select>
              </div>
            </div>

            <div className="modal-footer">
              <button 
                onClick={() => {
                  setShowEditStepModal(false);
                  resetEditForm();
                }}
                className="cancel-button"
              >
                Cancel
              </button>
              <button 
                onClick={handleEditStep}
                className="add-button"
                disabled={loading}
              >
                {loading ? 'Updating...' : 'Update Step'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default WorkflowDetailsPage; 