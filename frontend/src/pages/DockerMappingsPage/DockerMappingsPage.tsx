import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  getDockerMappings, 
  createDockerMapping, 
  updateDockerMapping, 
  deleteDockerMapping,
  getDockerMapping,
  DockerMapping,
  CreateDockerMappingRequest,
  UpdateDockerMappingRequest
} from '../../api';
import tokenManager from '../../utils/tokenManager';
import './DockerMappingsPage.css';

interface DockerMappingModalProps {
  mapping?: DockerMapping | null;
  onSubmit: (data: CreateDockerMappingRequest) => void;
  onCancel: () => void;
  acceptedScriptTypes: string[];
  isEdit?: boolean;
}

const DockerMappingModal: React.FC<DockerMappingModalProps> = ({ 
  mapping, 
  onSubmit, 
  onCancel, 
  acceptedScriptTypes,
  isEdit = false
}) => {
  const [formData, setFormData] = useState<CreateDockerMappingRequest>({
    script_type: mapping?.script_type || 'python',
    docker_image: mapping?.docker_image || '',
    docker_tag: mapping?.docker_tag || 'latest',
    description: mapping?.description || '',
    environment_variables: mapping?.environment_variables || {},
    volumes: mapping?.volumes || [],
    ports: mapping?.ports || [],
    is_active: mapping?.is_active ?? true
  });

  const [envKey, setEnvKey] = useState('');
  const [envValue, setEnvValue] = useState('');
  const [volumePath, setVolumePath] = useState('');
  const [portMapping, setPortMapping] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  const addEnvironmentVariable = () => {
    if (envKey && envValue) {
      setFormData(prev => ({
        ...prev,
        environment_variables: { ...prev.environment_variables, [envKey]: envValue }
      }));
      setEnvKey('');
      setEnvValue('');
    }
  };

  const removeEnvironmentVariable = (key: string) => {
    const newEnvVars = { ...formData.environment_variables };
    delete newEnvVars[key];
    setFormData(prev => ({ ...prev, environment_variables: newEnvVars }));
  };

  const addVolume = () => {
    if (volumePath) {
      setFormData(prev => ({ ...prev, volumes: [...prev.volumes, volumePath] }));
      setVolumePath('');
    }
  };

  const removeVolume = (index: number) => {
    setFormData(prev => ({ ...prev, volumes: prev.volumes.filter((_, i) => i !== index) }));
  };

  const addPort = () => {
    if (portMapping) {
      setFormData(prev => ({ ...prev, ports: [...prev.ports, portMapping] }));
      setPortMapping('');
    }
  };

  const removePort = (index: number) => {
    setFormData(prev => ({ ...prev, ports: prev.ports.filter((_, i) => i !== index) }));
  };

  return (
    <div className="modal-overlay">
      <div className="modal docker-mapping-modal">
        <div className="modal-header">
          <h3>{isEdit ? 'Edit Docker Mapping' : 'Create Docker Mapping'}</h3>
          <button onClick={onCancel} className="close-button">✕</button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="script_type">Script Type *</label>
            <select
              id="script_type"
              value={formData.script_type}
              onChange={(e) => setFormData(prev => ({ ...prev, script_type: e.target.value }))}
              required
            >
              {acceptedScriptTypes.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="docker_image">Docker Image *</label>
            <input
              id="docker_image"
              type="text"
              value={formData.docker_image}
              onChange={(e) => setFormData(prev => ({ ...prev, docker_image: e.target.value }))}
              placeholder="e.g., custom-python:3.9"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="docker_tag">Docker Tag *</label>
            <input
              id="docker_tag"
              type="text"
              value={formData.docker_tag}
              onChange={(e) => setFormData(prev => ({ ...prev, docker_tag: e.target.value }))}
              placeholder="e.g., latest"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="description">Description *</label>
            <textarea
              id="description"
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              placeholder="e.g., Custom Python 3.9 environment"
              required
            />
          </div>

          <div className="form-group">
            <label>Environment Variables</label>
            <div className="array-input">
              <input
                type="text"
                placeholder="Variable name"
                value={envKey}
                onChange={(e) => setEnvKey(e.target.value)}
              />
              <input
                type="text"
                placeholder="Variable value"
                value={envValue}
                onChange={(e) => setEnvValue(e.target.value)}
              />
              <button type="button" onClick={addEnvironmentVariable} className="add-button">
                Add
              </button>
            </div>
            {Object.entries(formData.environment_variables).map(([key, value]) => (
              <div key={key} className="array-item">
                <span>{key}={value}</span>
                <button type="button" onClick={() => removeEnvironmentVariable(key)} className="remove-button">
                  ×
                </button>
              </div>
            ))}
          </div>

          <div className="form-group">
            <label>Volumes</label>
            <div className="array-input">
              <input
                type="text"
                placeholder="e.g., /host/data:/container/data"
                value={volumePath}
                onChange={(e) => setVolumePath(e.target.value)}
              />
              <button type="button" onClick={addVolume} className="add-button">
                Add
              </button>
            </div>
            {formData.volumes.map((volume, index) => (
              <div key={index} className="array-item">
                <span>{volume}</span>
                <button type="button" onClick={() => removeVolume(index)} className="remove-button">
                  ×
                </button>
              </div>
            ))}
          </div>

          <div className="form-group">
            <label>Ports</label>
            <div className="array-input">
              <input
                type="text"
                placeholder="e.g., 8080:8080"
                value={portMapping}
                onChange={(e) => setPortMapping(e.target.value)}
              />
              <button type="button" onClick={addPort} className="add-button">
                Add
              </button>
            </div>
            {formData.ports.map((port, index) => (
              <div key={index} className="array-item">
                <span>{port}</span>
                <button type="button" onClick={() => removePort(index)} className="remove-button">
                  ×
                </button>
              </div>
            ))}
          </div>

          <div className="form-group">
            <label>
              <input
                type="checkbox"
                checked={formData.is_active}
                onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
              />
              Active
            </label>
          </div>

          <div className="modal-buttons">
            <button type="submit" className="modal-button confirm">
              {isEdit ? 'Update' : 'Create'}
            </button>
            <button type="button" onClick={onCancel} className="modal-button cancel">
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const DockerMappingsPage: React.FC = () => {
  const [dockerMappings, setDockerMappings] = useState<DockerMapping[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingMapping, setEditingMapping] = useState<DockerMapping | null>(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deletingMapping, setDeletingMapping] = useState<DockerMapping | null>(null);
  const [selectedMapping, setSelectedMapping] = useState<DockerMapping | null>(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);

  const navigate = useNavigate();

  // Accepted script types
  const acceptedScriptTypes = [
    'python', 'nodejs', 'ansible', 'terraform', 'sh', 'bash', 'zsh', 'powershell', 'go', 'rust', 'java', 'csharp'
  ];

  // Fetch Docker mappings
  const fetchDockerMappings = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      console.log('🔄 Loading Docker mappings...');
      const response = await getDockerMappings();
      console.log('✅ Docker mappings response:', response);
      
      const mappings = response.data.mappings || [];
      console.log('📋 Docker mappings data:', mappings);
      setDockerMappings(mappings);
    } catch (error: any) {
      console.error('❌ Error loading Docker mappings:', error);
      const errorMessage = error.response?.data?.detail || 
                          error.response?.data?.message || 
                          error.message || 
                          'Failed to load Docker mappings';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  // Load mappings on component mount
  useEffect(() => {
    fetchDockerMappings();
  }, [fetchDockerMappings]);

  // Create Docker mapping
  const handleCreateMapping = async (data: CreateDockerMappingRequest) => {
    setLoading(true);
    try {
      console.log('🔄 Creating Docker mapping:', data);
      await createDockerMapping(data);
      setMessage({ type: 'success', text: 'Docker mapping created successfully!' });
      setShowCreateModal(false);
      await fetchDockerMappings(); // Refresh the list
    } catch (error: any) {
      console.error('❌ Error creating Docker mapping:', error);
      const errorMessage = error.response?.data?.detail || 
                          error.response?.data?.message || 
                          error.message || 
                          'Failed to create Docker mapping';
      setMessage({ type: 'error', text: errorMessage });
    } finally {
      setLoading(false);
    }
  };

  // Update Docker mapping
  const handleUpdateMapping = async (data: CreateDockerMappingRequest) => {
    if (!editingMapping) return;
    
    setLoading(true);
    try {
      console.log('🔄 Updating Docker mapping:', editingMapping.id, data);
      await updateDockerMapping(editingMapping.id, data as UpdateDockerMappingRequest);
      setMessage({ type: 'success', text: 'Docker mapping updated successfully!' });
      setEditingMapping(null);
      await fetchDockerMappings(); // Refresh the list
    } catch (error: any) {
      console.error('❌ Error updating Docker mapping:', error);
      const errorMessage = error.response?.data?.detail || 
                          error.response?.data?.message || 
                          error.message || 
                          'Failed to update Docker mapping';
      setMessage({ type: 'error', text: errorMessage });
    } finally {
      setLoading(false);
    }
  };

  // Delete Docker mapping
  const handleDeleteMapping = async (mapping: DockerMapping) => {
    if (!window.confirm(`Are you sure you want to delete the Docker mapping "${mapping.docker_image}:${mapping.docker_tag}"? This action cannot be undone.`)) {
      return;
    }

    setLoading(true);
    try {
      console.log('🔄 Deleting Docker mapping:', mapping.id);
      await deleteDockerMapping(mapping.id);
      setMessage({ type: 'success', text: 'Docker mapping deleted successfully!' });
      setShowDeleteModal(false);
      setDeletingMapping(null);
      await fetchDockerMappings(); // Refresh the list
    } catch (error: any) {
      console.error('❌ Error deleting Docker mapping:', error);
      const errorMessage = error.response?.data?.detail || 
                          error.response?.data?.message || 
                          error.message || 
                          'Failed to delete Docker mapping';
      setMessage({ type: 'error', text: errorMessage });
    } finally {
      setLoading(false);
    }
  };

  // View mapping details
  const handleViewDetails = async (mapping: DockerMapping) => {
    setSelectedMapping(mapping);
    setShowDetailsModal(true);
  };

  // Format environment variables for display
  const formatEnvVars = (envVars: Record<string, string>) => {
    return Object.entries(envVars).map(([key, value]) => `${key}=${value}`).join(', ');
  };

  // Format arrays for display
  const formatArray = (arr: string[]) => {
    return arr.join(', ');
  };

  // Clear messages after 5 seconds
  useEffect(() => {
    if (message) {
      const timer = setTimeout(() => setMessage(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [message]);

  return (
    <div className="docker-mappings-page">
      <div className="page-header">
        <h1>🐳 Docker Mappings</h1>
        <p>Manage Docker execution mappings for different script types</p>
      </div>

      {/* Message Display */}
      {message && (
        <div className={`message ${message.type}-message`}>
          {message.text}
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="error-message">
          {error}
          <button onClick={fetchDockerMappings} className="retry-button">
            Retry
          </button>
        </div>
      )}

      {/* Action Bar */}
      <div className="action-bar">
        <button 
          onClick={() => setShowCreateModal(true)}
          className="create-button"
          disabled={loading}
        >
          ➕ Create Mapping
        </button>
        <button 
          onClick={fetchDockerMappings}
          className="refresh-button"
          disabled={loading}
        >
          🔄 Refresh
        </button>
      </div>

      {/* Mappings Table */}
      {loading ? (
        <div className="loading">Loading Docker mappings...</div>
      ) : (
        <div className="mappings-table">
          <table>
            <thead>
              <tr>
                <th>Script Type</th>
                <th>Docker Image</th>
                <th>Tag</th>
                <th>Description</th>
                <th>Status</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {dockerMappings.length > 0 ? (
                dockerMappings.map((mapping) => (
                  <tr key={mapping.id}>
                    <td>
                      <span className={`script-type-badge ${mapping.script_type}`}>
                        {mapping.script_type}
                      </span>
                    </td>
                    <td>
                      <code className="docker-image">{mapping.docker_image}</code>
                    </td>
                    <td>
                      <span className="docker-tag">{mapping.docker_tag}</span>
                    </td>
                    <td>
                      <div className="description">
                        {mapping.description}
                      </div>
                    </td>
                    <td>
                      <span className={`status-badge ${mapping.is_active ? 'active' : 'inactive'}`}>
                        {mapping.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td>
                      {new Date(mapping.created_at).toLocaleDateString()}
                    </td>
                    <td>
                      <div className="action-buttons">
                        <button 
                          className="action-button view" 
                          onClick={() => handleViewDetails(mapping)}
                          title="View Details"
                        >
                          👁️
                        </button>
                        <button 
                          className="action-button edit" 
                          onClick={() => setEditingMapping(mapping)}
                          title="Edit Mapping"
                        >
                          ✏️
                        </button>
                        <button 
                          className="action-button delete" 
                          onClick={() => handleDeleteMapping(mapping)}
                          title="Delete Mapping"
                        >
                          🗑️
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="no-data">
                    No Docker mappings found. Create your first mapping to get started!
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <DockerMappingModal
          onSubmit={handleCreateMapping}
          onCancel={() => setShowCreateModal(false)}
          acceptedScriptTypes={acceptedScriptTypes}
        />
      )}

      {/* Edit Modal */}
      {editingMapping && (
        <DockerMappingModal
          mapping={editingMapping}
          onSubmit={handleUpdateMapping}
          onCancel={() => setEditingMapping(null)}
          acceptedScriptTypes={acceptedScriptTypes}
          isEdit={true}
        />
      )}

      {/* Details Modal */}
      {showDetailsModal && selectedMapping && (
        <div className="modal-overlay">
          <div className="modal details-modal">
            <div className="modal-header">
              <h3>Docker Mapping Details</h3>
              <button onClick={() => setShowDetailsModal(false)} className="close-button">✕</button>
            </div>
            <div className="modal-body">
              <div className="detail-section">
                <h4>Basic Information</h4>
                <div className="detail-row">
                  <label>Script Type:</label>
                  <span className={`script-type-badge ${selectedMapping.script_type}`}>
                    {selectedMapping.script_type}
                  </span>
                </div>
                <div className="detail-row">
                  <label>Docker Image:</label>
                  <code className="docker-image">{selectedMapping.docker_image}</code>
                </div>
                <div className="detail-row">
                  <label>Docker Tag:</label>
                  <span className="docker-tag">{selectedMapping.docker_tag}</span>
                </div>
                <div className="detail-row">
                  <label>Description:</label>
                  <span>{selectedMapping.description}</span>
                </div>
                <div className="detail-row">
                  <label>Status:</label>
                  <span className={`status-badge ${selectedMapping.is_active ? 'active' : 'inactive'}`}>
                    {selectedMapping.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
              </div>

              <div className="detail-section">
                <h4>Environment Variables</h4>
                {Object.keys(selectedMapping.environment_variables).length > 0 ? (
                  <div className="env-vars">
                    {Object.entries(selectedMapping.environment_variables).map(([key, value]) => (
                      <div key={key} className="env-var">
                        <code>{key}={value}</code>
                      </div>
                    ))}
                  </div>
                ) : (
                  <span className="no-data">No environment variables</span>
                )}
              </div>

              <div className="detail-section">
                <h4>Volumes</h4>
                {selectedMapping.volumes.length > 0 ? (
                  <div className="volumes">
                    {selectedMapping.volumes.map((volume, index) => (
                      <div key={index} className="volume">
                        <code>{volume}</code>
                      </div>
                    ))}
                  </div>
                ) : (
                  <span className="no-data">No volumes</span>
                )}
              </div>

              <div className="detail-section">
                <h4>Ports</h4>
                {selectedMapping.ports.length > 0 ? (
                  <div className="ports">
                    {selectedMapping.ports.map((port, index) => (
                      <div key={index} className="port">
                        <code>{port}</code>
                      </div>
                    ))}
                  </div>
                ) : (
                  <span className="no-data">No ports</span>
                )}
              </div>

              <div className="detail-section">
                <h4>Metadata</h4>
                <div className="detail-row">
                  <label>Created:</label>
                  <span>{new Date(selectedMapping.created_at).toLocaleString()}</span>
                </div>
                <div className="detail-row">
                  <label>Updated:</label>
                  <span>{new Date(selectedMapping.updated_at).toLocaleString()}</span>
                </div>
                <div className="detail-row">
                  <label>ID:</label>
                  <code className="mapping-id">{selectedMapping.id}</code>
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button 
                onClick={() => {
                  setEditingMapping(selectedMapping);
                  setShowDetailsModal(false);
                }}
                className="modal-button edit"
              >
                Edit Mapping
              </button>
              <button 
                onClick={() => setShowDetailsModal(false)}
                className="modal-button cancel"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DockerMappingsPage; 