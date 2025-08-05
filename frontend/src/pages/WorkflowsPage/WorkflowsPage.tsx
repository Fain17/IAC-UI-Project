import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import tokenManager from '../../utils/tokenManager';
import { 
  getWorkflows, 
  createWorkflow, 
  updateWorkflow, 
  deleteWorkflow, 
  executeWorkflow,
  getMappings,
  createMapping,
  deleteMapping,
  Workflow, 
  WorkflowCreate, 
  WorkflowUpdate,
  WorkflowStep 
} from '../../api';
import AddMappingForm from '../../components/AddMappingForm';
import MappingList from '../../components/MappingList';
import './WorkflowsPage.css';

const WorkflowsPage: React.FC = () => {
  // State for workflows list
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // State for mappings
  const [mappings, setMappings] = useState<{ [key: string]: string }>({});

  // State for create/edit form
  const [activeSubMenu, setActiveSubMenu] = useState<string>('list');
  const [editingWorkflow, setEditingWorkflow] = useState<Workflow | null>(null);
  const [formData, setFormData] = useState<WorkflowCreate>({
    name: '',
    description: '',
    steps: [{ action: '', target: '' }],
    is_active: true,
    script_type: '',
    script_content: '',
    script_filename: '',
    run_command: '',
    dependencies: []
  });

  // State for file upload
  const [fileName, setFileName] = useState<string>('');
  const [fileType, setFileType] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  // User state
  const [username, setUsername] = useState<string>('');
  const [email, setEmail] = useState<string>('');
  const navigate = useNavigate();

  useEffect(() => {
    const user = tokenManager.getUser();
    if (user) {
      setUsername(user.username || '');
      setEmail(user.email || '');
    }
    if (activeSubMenu === 'list') {
      fetchWorkflows();
    }
    if (activeSubMenu === 'create') {
      fetchMappings();
    }
  }, [activeSubMenu]);

  // Fetch mappings when script type changes to supported types
  useEffect(() => {
    if (activeSubMenu === 'create' && 
        (formData.script_type === 'python' || formData.script_type === 'javascript' || formData.script_type === 'typescript')) {
      fetchMappings();
    }
  }, [formData.script_type, activeSubMenu]);

  const fetchWorkflows = async () => {
    setLoading(true);
    try {
      const response = await getWorkflows();
      
      // Handle different possible response structures
      let workflowsData: Workflow[] = [];
      const responseData = response.data as any;
      
      if (responseData && Array.isArray(responseData)) {
        workflowsData = responseData;
      } else if (responseData && Array.isArray(responseData.workflows)) {
        workflowsData = responseData.workflows;
      } else if (responseData && responseData.data && Array.isArray(responseData.data)) {
        workflowsData = responseData.data;
      } else {
        console.warn('Unexpected response structure:', responseData);
        workflowsData = [];
      }
      
      setWorkflows(workflowsData);
    } catch (error: any) {
      console.error('Error fetching workflows:', error);
      setMessage({ type: 'error', text: 'Failed to fetch workflows: ' + (error.response?.data?.detail || error.message) });
      setWorkflows([]); // Ensure workflows is always an array
    } finally {
      setLoading(false);
    }
  };

  const fetchMappings = async () => {
    try {
      const response = await getMappings();
      setMappings(response.data.mappings);
    } catch (error: any) {
      console.error('Error fetching mappings:', error);
      setMessage({ type: 'error', text: 'Failed to fetch mappings: ' + (error.response?.data?.detail || error.message) });
    }
  };

  const handleCreateMapping = async (instance: string, lt: string) => {
    try {
      await createMapping(instance, lt);
      setMessage({ type: 'success', text: 'Mapping created successfully!' });
      fetchMappings();
    } catch (error: any) {
      setMessage({ type: 'error', text: 'Failed to create mapping: ' + (error.response?.data?.detail || error.message) });
    }
  };

  const handleDeleteMapping = async (instance: string) => {
    try {
      await deleteMapping(instance);
      setMessage({ type: 'success', text: 'Mapping deleted successfully!' });
      fetchMappings();
    } catch (error: any) {
      setMessage({ type: 'error', text: 'Failed to delete mapping: ' + (error.response?.data?.detail || error.message) });
    }
  };

  const getFileType = (fileName: string): string => {
    const extension = fileName.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'py':
        return 'Python (boto3)';
      case 'js':
        return 'JavaScript/Node.js';
      case 'ts':
        return 'TypeScript/Node.js';
      case 'yaml':
      case 'yml':
        return 'YAML';
      case 'json':
        return 'JSON';
      case 'tf':
        return 'Terraform';
      case 'tfvars':
        return 'Terraform Variables';
      case 'hcl':
        return 'HCL (HashiCorp)';
      case 'txt':
        return 'Text';
      default:
        return 'Unknown';
    }
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setFileName(file.name);
      const detectedType = getFileType(file.name);
      setFileType(detectedType);
      
      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target?.result as string;
        setFormData(prev => ({
          ...prev,
          script_content: content,
          script_filename: file.name,
          script_type: detectedType.toLowerCase().split(' ')[0]
        }));
        setMessage({ 
          type: 'success', 
          text: `File "${file.name}" (${detectedType}) loaded successfully!` 
        });
        setTimeout(() => setMessage(null), 3000);
      };
      reader.readAsText(file);
    }
  };

  const handleFormChange = (field: keyof WorkflowCreate, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const addStep = () => {
    const newStep: WorkflowStep = {
      action: '',
      target: ''
    };
    setFormData(prev => ({
      ...prev,
      steps: [...(prev.steps || []), newStep]
    }));
  };

  const updateStep = (index: number, field: keyof WorkflowStep, value: string) => {
    setFormData(prev => ({
      ...prev,
      steps: prev.steps?.map((step, i) => 
        i === index ? { ...step, [field]: value } : step
      ) || []
    }));
  };

  const removeStep = (index: number) => {
    setFormData(prev => ({
      ...prev,
      steps: prev.steps?.filter((_, i) => i !== index) || []
    }));
  };

  const handleSubmit = async () => {
    if (!formData.name.trim()) {
      setMessage({ type: 'error', text: 'Workflow name is required.' });
      return;
    }

    if (!(formData.script_content || '').trim()) {
      setMessage({ type: 'error', text: 'Script content is required.' });
      return;
    }

    if (!formData.steps || formData.steps.length === 0) {
      setMessage({ type: 'error', text: 'At least one workflow step is required.' });
      return;
    }

    setLoading(true);
    try {
      if (editingWorkflow) {
        await updateWorkflow(editingWorkflow.id, formData);
        setMessage({ type: 'success', text: 'Workflow updated successfully!' });
      } else {
        await createWorkflow(formData);
        setMessage({ type: 'success', text: 'Workflow created successfully!' });
      }
      
      // Reset form and switch to list view
      resetForm();
      setActiveSubMenu('list');
      fetchWorkflows();
    } catch (error: any) {
      setMessage({ type: 'error', text: 'Failed to save workflow: ' + (error.response?.data?.detail || error.message) });
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (workflow: Workflow) => {
    setEditingWorkflow(workflow);
    setFormData({
      name: workflow.name,
      description: workflow.description || '',
      steps: workflow.steps,
      is_active: workflow.is_active,
      script_type: workflow.script_type || '',
      script_content: workflow.script_content || '',
      script_filename: workflow.script_filename || '',
      run_command: workflow.run_command || '',
      dependencies: workflow.dependencies || []
    });
    setActiveSubMenu('create');
  };

  const handleDelete = async (workflowId: number) => {
    if (!window.confirm('Are you sure you want to delete this workflow?')) {
      return;
    }

    setLoading(true);
    try {
      await deleteWorkflow(workflowId);
      setMessage({ type: 'success', text: 'Workflow deleted successfully!' });
      fetchWorkflows();
    } catch (error: any) {
      setMessage({ type: 'error', text: 'Failed to delete workflow: ' + (error.response?.data?.detail || error.message) });
    } finally {
      setLoading(false);
    }
  };

  const handleExecute = async (workflowId: number) => {
    setLoading(true);
    try {
      await executeWorkflow(workflowId);
      setMessage({ type: 'success', text: 'Workflow execution started!' });
    } catch (error: any) {
      setMessage({ type: 'error', text: 'Failed to execute workflow: ' + (error.response?.data?.detail || error.message) });
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      steps: [{ action: '', target: '' }],
      is_active: true,
      script_type: '',
      script_content: '',
      script_filename: '',
      run_command: '',
      dependencies: []
    });
    setEditingWorkflow(null);
    setFileName('');
    setFileType('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleLogout = async () => {
    await tokenManager.logout();
  };

  const displayName = username || email;
  const initial = displayName ? displayName[0].toUpperCase() : '?';

  const renderContent = () => {
    switch (activeSubMenu) {
      case 'list':
        return (
          <div className="workflows-section">
            <div className="section-header">
              <h2>Workflows</h2>
            </div>
            
            {loading ? (
              <div className="loading">Loading workflows...</div>
            ) : (workflows || []).length === 0 ? (
              <div className="empty-state">
                <p>No workflows found. Create your first workflow to get started!</p>
              </div>
            ) : (
              <div className="workflows-list">
                {(workflows || []).map((workflow) => (
                  <div key={workflow.id} className="workflow-card">
                    <div className="workflow-header">
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
                      <div className="detail-item">
                        <strong>Script Type:</strong> {workflow.script_type || 'Not specified'}
                      </div>
                      <div className="detail-item">
                        <strong>Created:</strong> {new Date(workflow.created_at).toLocaleDateString()}
                      </div>
                      {workflow.dependencies && workflow.dependencies.length > 0 && (
                        <div className="detail-item">
                          <strong>Dependencies:</strong> {workflow.dependencies.join(', ')}
                        </div>
                      )}
                    </div>
                    
                    <div className="workflow-actions">
                      <button 
                        onClick={() => handleExecute(workflow.id)}
                        className="action-button execute"
                        disabled={loading}
                      >
                        Execute
                      </button>
                      <button 
                        onClick={() => handleEdit(workflow)}
                        className="action-button edit"
                      >
                        Edit
                      </button>
                      <button 
                        onClick={() => handleDelete(workflow.id)}
                        className="action-button delete"
                        disabled={loading}
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      
      case 'create':
        return (
          <div className="workflows-section">
            <div className="section-header">
              <h2>{editingWorkflow ? 'Edit Workflow' : 'Create New Workflow'}</h2>
              <button 
                onClick={() => {
                  resetForm();
                  setActiveSubMenu('list');
                }}
                className="back-button"
              >
                Back to List
              </button>
            </div>
            
            <form onSubmit={(e) => { e.preventDefault(); handleSubmit(); }} className="workflow-form">
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="name">Workflow Name *</label>
                  <input
                    id="name"
                    type="text"
                    value={formData.name}
                    onChange={(e) => handleFormChange('name', e.target.value)}
                    placeholder="Enter workflow name"
                    required
                  />
                </div>
                
                <div className="form-group">
                  <label htmlFor="description">Description</label>
                  <input
                    id="description"
                    type="text"
                    value={formData.description}
                    onChange={(e) => handleFormChange('description', e.target.value)}
                    placeholder="Enter workflow description"
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="script_type">Script Type</label>
                  <select
                    id="script_type"
                    value={formData.script_type}
                    onChange={(e) => handleFormChange('script_type', e.target.value)}
                  >
                    <option value="">Select script type</option>
                    <option value="python">Python (boto3)</option>
                    <option value="javascript">JavaScript/Node.js</option>
                    <option value="typescript">TypeScript/Node.js</option>
                    <option value="yaml">YAML</option>
                    <option value="json">JSON</option>
                    <option value="terraform">Terraform</option>
                    <option value="bash">Bash</option>
                    <option value="powershell">PowerShell</option>
                  </select>
                </div>
                
                <div className="form-group">
                  <label htmlFor="run_command">Run Command</label>
                  <input
                    id="run_command"
                    type="text"
                    value={formData.run_command}
                    onChange={(e) => handleFormChange('run_command', e.target.value)}
                    placeholder="e.g., python script.py, node app.js"
                  />
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="dependencies">Dependencies (comma-separated)</label>
                <input
                  id="dependencies"
                  type="text"
                  value={formData.dependencies?.join(', ') || ''}
                  onChange={(e) => handleFormChange('dependencies', e.target.value.split(',').map(d => d.trim()).filter(d => d))}
                  placeholder="e.g., aws-cli, jq, curl"
                />
              </div>

              {/* Workflow Steps Section */}
              <div className="form-group">
                <label>Workflow Steps *</label>
                <div className="steps-container">
                  {formData.steps?.map((step, index) => (
                    <div key={index} className="step-item">
                      <div className="step-header">
                        <span className="step-number">Step {index + 1}</span>
                        <button
                          type="button"
                          onClick={() => removeStep(index)}
                          className="remove-step-button"
                          disabled={formData.steps?.length === 1}
                        >
                          🗑️
                        </button>
                      </div>
                      <div className="step-fields">
                        <input
                          type="text"
                          value={step.action}
                          onChange={(e) => updateStep(index, 'action', e.target.value)}
                          placeholder="Action (e.g., backup, deploy, test)"
                          className="step-action"
                        />
                        <input
                          type="text"
                          value={step.target || ''}
                          onChange={(e) => updateStep(index, 'target', e.target.value)}
                          placeholder="Target (e.g., database, app, service)"
                          className="step-target"
                        />
                      </div>
                    </div>
                  ))}
                  <button
                    type="button"
                    onClick={addStep}
                    className="add-step-button"
                  >
                    ➕ Add Step
                  </button>
                </div>
              </div>

              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => handleFormChange('is_active', e.target.checked)}
                  />
                  Active
                </label>
              </div>

              {/* Mappings Section - Only show for boto3 and node.js */}
              {(formData.script_type === 'python' || formData.script_type === 'javascript' || formData.script_type === 'typescript') && (
                <div className="mappings-section">
                  <h3>Instance Mappings</h3>
                  <p className="mappings-description">
                    Configure instance-to-launch-template mappings for your AWS infrastructure.
                  </p>
                  
                  <div className="mappings-container">
                    <AddMappingForm onCreate={handleCreateMapping} />
                    <MappingList mappings={mappings} onDelete={handleDeleteMapping} />
                  </div>
                </div>
              )}

              {/* File Upload Section */}
              <div className="upload-section">
                <h3>Upload Script File</h3>
                <div className="file-upload-container">
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileUpload}
                    accept=".yaml,.yml,.json,.txt,.py,.js,.ts,.tf,.tfvars,.hcl,.sh,.ps1"
                    className="file-input"
                    id="file-upload"
                  />
                  <label htmlFor="file-upload" className="file-upload-label">
                    <span className="upload-icon">📁</span>
                    Choose File
                  </label>
                  {fileName && (
                    <div className="file-info">
                      <div className="file-name">Selected: {fileName}</div>
                      {fileType && <div className="file-type">Type: {fileType}</div>}
                    </div>
                  )}
                </div>
              </div>

              {/* Code Editor Section */}
              <div className="code-section">
                <h3>Script Content *</h3>
                <div className="code-templates">
                  <span className="template-label">Quick templates:</span>
                  <button 
                    type="button"
                    className="template-btn"
                    onClick={() => handleFormChange('script_content', `import boto3

# AWS EC2 Instance Creation with boto3
def create_ec2_instance():
    ec2 = boto3.client('ec2')
    
    response = ec2.run_instances(
        ImageId='ami-12345678',
        MinCount=1,
        MaxCount=1,
        InstanceType='t2.micro',
        KeyName='my-key-pair',
        SecurityGroupIds=['sg-12345678'],
        TagSpecifications=[
            {
                'ResourceType': 'instance',
                'Tags': [
                    {
                        'Key': 'Name',
                        'Value': 'MyEC2Instance'
                    }
                ]
            }
        ]
    )
    
    return response

if __name__ == "__main__":
    create_ec2_instance()`)}
                  >
                    Python boto3
                  </button>
                  <button 
                    type="button"
                    className="template-btn"
                    onClick={() => handleFormChange('script_content', `const AWS = require('aws-sdk');

// AWS EC2 Instance Creation with Node.js
async function createEC2Instance() {
    const ec2 = new AWS.EC2();
    
    const params = {
        ImageId: 'ami-12345678',
        MinCount: 1,
        MaxCount: 1,
        InstanceType: 't2.micro',
        KeyName: 'my-key-pair',
        SecurityGroupIds: ['sg-12345678'],
        TagSpecifications: [{
            ResourceType: 'instance',
            Tags: [{
                Key: 'Name',
                Value: 'MyEC2Instance'
            }]
        }]
    };
    
    try {
        const result = await ec2.runInstances(params).promise();
        console.log('Instance created:', result);
        return result;
    } catch (error) {
        console.error('Error creating instance:', error);
        throw error;
    }
}

createEC2Instance();`)}
                  >
                    Node.js AWS SDK
                  </button>
                  <button 
                    type="button"
                    className="template-btn"
                    onClick={() => handleFormChange('script_content', `# Terraform EC2 Instance
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  region = "us-west-2"
}

resource "aws_instance" "example" {
  ami           = "ami-12345678"
  instance_type = "t2.micro"
  key_name      = "my-key-pair"
  
  vpc_security_group_ids = [aws_security_group.example.id]
  
  tags = {
    Name = "MyEC2Instance"
  }
}

resource "aws_security_group" "example" {
  name_prefix = "example-sg"
  
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}`)}
                  >
                    Terraform
                  </button>
                </div>
                
                <div className="code-editor-container">
                  <textarea
                    value={formData.script_content}
                    onChange={(e) => handleFormChange('script_content', e.target.value)}
                    placeholder="Paste your workflow code here (YAML, JSON, Python boto3, Node.js, Terraform, etc.)..."
                    className="code-editor"
                    rows={20}
                    required
                  />
                  <div className="code-actions">
                    <button 
                      type="button"
                      onClick={() => handleFormChange('script_content', '')}
                      className="clear-button"
                      disabled={loading}
                    >
                      Clear
                    </button>
                    <div className="char-count">
                      {(formData.script_content || '').length} characters
                    </div>
                  </div>
                </div>
              </div>

              <div className="form-actions">
                <button 
                  type="submit"
                  className="submit-button"
                  disabled={loading || !formData.name.trim() || !(formData.script_content || '').trim()}
                >
                  {loading ? 'Saving...' : (editingWorkflow ? 'Update Workflow' : 'Create Workflow')}
                </button>
                <button 
                  type="button"
                  onClick={() => {
                    resetForm();
                    setActiveSubMenu('list');
                  }}
                  className="cancel-button"
                  disabled={loading}
                >
                  Cancel
                </button>
              </div>
            </form>
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
        <Link to="/settings" className="nav-link">Settings</Link>
        
        <div className="workflows-submenu">
          <div className="submenu-header">Workflows</div>
          <button 
            className={`submenu-item ${activeSubMenu === 'list' ? 'active' : ''}`}
            onClick={() => setActiveSubMenu('list')}
          >
            📋 List Workflows
          </button>
          <button 
            className={`submenu-item ${activeSubMenu === 'create' ? 'active' : ''}`}
            onClick={() => {
              resetForm();
              setActiveSubMenu('create');
            }}
          >
            ➕ Create Workflow
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
          {username && <div className="name">{username}</div>}
          {email && <div className="email">{email}</div>}
        </div>

        <div className="workflows-content">
          <h1>Workflows</h1>
          
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

export default WorkflowsPage; 