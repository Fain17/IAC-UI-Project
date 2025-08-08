import React, { useState } from 'react';
import axios from 'axios';
import tokenManager from '../../../utils/tokenManager';
import './CreateWorkflow.css';

interface CreateWorkflowRequest {
  name: string;
  description?: string;
}

interface CreateWorkflowResponse {
  success: boolean;
  workflow_id: string;
  message: string;
  steps_count: number;
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

const CreateWorkflow: React.FC = () => {
  const [formData, setFormData] = useState<CreateWorkflowRequest>({
    name: '',
    description: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name.trim()) {
      setError('Workflow name is required');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setSuccess(null);

      // Send the data as JSON
      const requestData = {
        name: formData.name.trim(),
        description: formData.description?.trim() || ''
      };

      const response = await API.post<CreateWorkflowResponse>('/workflow/create', requestData);
      
      if (response.data.success) {
        setSuccess(`Workflow "${formData.name}" created successfully!`);
        setFormData({ name: '', description: '' });
      } else {
        setError('Failed to create workflow');
      }
    } catch (err: any) {
      console.error('Error creating workflow:', err);
      
      // Handle different error formats
      if (err.response?.data?.detail) {
        if (Array.isArray(err.response.data.detail)) {
          // Handle validation errors
          const errorMessages = err.response.data.detail.map((error: any) => 
            `${error.loc?.join('.')}: ${error.msg}`
          ).join(', ');
          setError(errorMessages);
        } else {
          setError(err.response.data.detail);
        }
      } else {
        setError('Failed to create workflow');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFormData({ name: '', description: '' });
    setError(null);
    setSuccess(null);
  };

  return (
    <div className="create-workflow">
      <div className="create-workflow-header">
        <h2>Create New Workflow</h2>
        <p>Create a new workflow to automate your processes.</p>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {success && (
        <div className="success-message">
          {success}
        </div>
      )}

      <form onSubmit={handleSubmit} className="create-workflow-form">
        <div className="form-group">
          <label htmlFor="name">Workflow Name *</label>
          <input
            type="text"
            id="name"
            name="name"
            value={formData.name}
            onChange={handleInputChange}
            placeholder="Enter workflow name"
            required
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="description">Description</label>
          <textarea
            id="description"
            name="description"
            value={formData.description}
            onChange={handleInputChange}
            placeholder="Enter workflow description (optional)"
            rows={4}
            disabled={loading}
          />
        </div>

        <div className="form-actions">
          <button
            type="button"
            onClick={handleReset}
            className="reset-button"
            disabled={loading}
          >
            Reset
          </button>
          <button
            type="submit"
            className="submit-button"
            disabled={loading || !formData.name.trim()}
          >
            {loading ? 'Creating...' : 'Create Workflow'}
          </button>
        </div>
      </form>

      <div className="create-workflow-info">
        <h3>What is a Workflow?</h3>
        <p>
          A workflow is a series of automated steps that can be executed to perform 
          specific tasks. Workflows help you automate repetitive processes and 
          ensure consistency in your operations.
        </p>
        
        <h3>Next Steps</h3>
        <ul>
          <li>After creating a workflow, you can add steps to define the automation process</li>
          <li>Each step can be configured with specific parameters and actions</li>
          <li>Workflows can be executed manually or scheduled to run automatically</li>
          <li>You can monitor workflow execution and view results</li>
        </ul>
      </div>
    </div>
  );
};

export default CreateWorkflow; 