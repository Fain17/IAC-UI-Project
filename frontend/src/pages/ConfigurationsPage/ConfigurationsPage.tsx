import React, { useMemo, useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { 
  getDockerMappings, 
  createDockerMapping, 
  updateDockerMapping, 
  deleteDockerMapping,
  DockerMapping,
  CreateDockerMappingRequest,
  UpdateDockerMappingRequest,
  getResourceMappings,
  createResourceMapping,
  updateResourceMapping,
  deleteResourceMapping,
  ResourceMapping,
  CreateResourceMappingRequest,
  UpdateResourceMappingRequest,
  getVaultConfigs,
  createVaultConfig,
  updateVaultConfig,
  deleteVaultConfig,
  testVaultConnection,
  VaultConfig,
  CreateVaultConfigRequest,
  UpdateVaultConfigRequest
} from '../../api';
import './ConfigurationsPage.css';

// Docker Mapping Modal Component
interface DockerMappingModalProps {
  mapping?: DockerMapping | null;
  onSubmit: (data: CreateDockerMappingRequest) => void;
  onCancel: () => void;
  acceptedScriptTypes: string[];
}

const DockerMappingModal: React.FC<DockerMappingModalProps> = ({ 
  mapping, 
  onSubmit, 
  onCancel, 
  acceptedScriptTypes 
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
        <h3>{mapping ? 'Edit Docker Mapping' : 'Create Docker Mapping'}</h3>
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
            <div className="env-vars-input">
              <input
                type="text"
                placeholder="Key"
                value={envKey}
                onChange={(e) => setEnvKey(e.target.value)}
              />
              <input
                type="text"
                placeholder="Value"
                value={envValue}
                onChange={(e) => setEnvValue(e.target.value)}
              />
              <button type="button" onClick={addEnvironmentVariable} className="add-button">
                Add
              </button>
            </div>
            {Object.entries(formData.environment_variables).map(([key, value]) => (
              <div key={key} className="env-var-item">
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
              {mapping ? 'Update' : 'Create'}
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

// Resource Mapping Modal Component
interface ResourceMappingModalProps {
  mapping?: ResourceMapping | null;
  onSubmit: (data: CreateResourceMappingRequest) => void;
  onCancel: () => void;
}

const ResourceMappingModal: React.FC<ResourceMappingModalProps> = ({ 
  mapping, 
  onSubmit, 
  onCancel 
}) => {
  const [formData, setFormData] = useState<CreateResourceMappingRequest>({
    mapping_type: mapping?.mapping_type || 'ec2_to_lt',
    source_resource: mapping?.source_resource || '',
    target_resource: mapping?.target_resource || '',
    description: mapping?.description || '',
    metadata: mapping?.metadata || {},
    is_active: mapping?.is_active ?? true
  });

  const [metadataKey, setMetadataKey] = useState('');
  const [metadataValue, setMetadataValue] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  const addMetadata = () => {
    if (metadataKey && metadataValue) {
      setFormData(prev => ({
        ...prev,
        metadata: { ...prev.metadata, [metadataKey]: metadataValue }
      }));
      setMetadataKey('');
      setMetadataValue('');
    }
  };

  const removeMetadata = (key: string) => {
    const newMetadata = { ...formData.metadata };
    delete newMetadata[key];
    setFormData(prev => ({ ...prev, metadata: newMetadata }));
  };

  return (
    <div className="modal-overlay">
      <div className="modal resource-mapping-modal">
        <h3>{mapping ? 'Edit Resource Mapping' : 'Create Resource Mapping'}</h3>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="mapping_type">Mapping Type *</label>
            <select
              id="mapping_type"
              value={formData.mapping_type}
              onChange={(e) => setFormData(prev => ({ ...prev, mapping_type: e.target.value }))}
              required
            >
              <option value="ec2_to_lt">EC2 to Launch Template</option>
              <option value="ec2_to_ami">EC2 to AMI</option>
              <option value="lt_to_lt">Launch Template to Launch Template</option>
              <option value="ami_to_ami">AMI to AMI</option>
              <option value="custom">Custom</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="source_resource">Source Resource *</label>
            <input
              id="source_resource"
              type="text"
              value={formData.source_resource}
              onChange={(e) => setFormData(prev => ({ ...prev, source_resource: e.target.value }))}
              placeholder="e.g., i-1234567890abcdef0"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="target_resource">Target Resource *</label>
            <input
              id="target_resource"
              type="text"
              value={formData.target_resource}
              onChange={(e) => setFormData(prev => ({ ...prev, target_resource: e.target.value }))}
              placeholder="e.g., lt-0987654321fedcba0"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="description">Description *</label>
            <textarea
              id="description"
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              placeholder="e.g., EC2 instance mapped to launch template"
              required
            />
          </div>

          <div className="form-group">
            <label>Metadata</label>
            <div className="metadata-input">
              <input
                type="text"
                placeholder="Key"
                value={metadataKey}
                onChange={(e) => setMetadataKey(e.target.value)}
              />
              <input
                type="text"
                placeholder="Value"
                value={metadataValue}
                onChange={(e) => setMetadataValue(e.target.value)}
              />
              <button type="button" onClick={addMetadata} className="add-button">
                Add
              </button>
            </div>
            {Object.entries(formData.metadata).map(([key, value]) => (
              <div key={key} className="metadata-item">
                <span>{key}={value}</span>
                <button type="button" onClick={() => removeMetadata(key)} className="remove-button">
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
              {mapping ? 'Update' : 'Create'}
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

// Vault Configuration Modal Component
interface VaultConfigModalProps {
  config?: VaultConfig | null;
  onSubmit: (data: CreateVaultConfigRequest) => void;
  onCancel: () => void;
}

const VaultConfigModal: React.FC<VaultConfigModalProps> = ({ 
  config, 
  onSubmit, 
  onCancel 
}) => {
  const [formData, setFormData] = useState<CreateVaultConfigRequest>({
    config_name: config?.config_name || '',
    vault_address: config?.vault_address || '',
    vault_token: config?.vault_token || '',
    namespace: config?.namespace || '',
    mount_path: config?.mount_path || 'secret',
    engine_type: config?.engine_type || 'kv',
    engine_version: config?.engine_version || '2',
    is_active: config?.is_active ?? true
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <div className="modal-overlay">
      <div className="modal vault-config-modal">
        <h3>{config ? 'Edit Vault Configuration' : 'Create Vault Configuration'}</h3>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="vaultName">Configuration Name *</label>
            <input
              id="vaultName"
              type="text"
              value={formData.config_name}
              onChange={(e) => setFormData(prev => ({ ...prev, config_name: e.target.value }))}
              placeholder="e.g., production-vault"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="vaultAddress">Vault Address *</label>
            <input
              id="vaultAddress"
              type="url"
              value={formData.vault_address}
              onChange={(e) => setFormData(prev => ({ ...prev, vault_address: e.target.value }))}
              placeholder="https://vault.example.com:8200"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="vaultToken">Vault Token *</label>
            <input
              id="vaultToken"
              type="password"
              value={formData.vault_token}
              onChange={(e) => setFormData(prev => ({ ...prev, vault_token: e.target.value }))}
              placeholder="Enter your vault token"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="vaultNamespace">Namespace (Optional)</label>
            <input
              id="vaultNamespace"
              type="text"
              value={formData.namespace}
              onChange={(e) => setFormData(prev => ({ ...prev, namespace: e.target.value }))}
              placeholder="e.g., team-a"
            />
          </div>

          <div className="form-group">
            <label htmlFor="vaultMountPath">Mount Path *</label>
            <input
              id="vaultMountPath"
              type="text"
              value={formData.mount_path}
              onChange={(e) => setFormData(prev => ({ ...prev, mount_path: e.target.value }))}
              placeholder="e.g., secret/"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="vaultEngineType">Engine Type *</label>
            <select
              id="vaultEngineType"
              value={formData.engine_type}
              onChange={(e) => setFormData(prev => ({ ...prev, engine_type: e.target.value }))}
              required
            >
              <option value="kv">Key-Value (KV)</option>
              <option value="aws">AWS</option>
              <option value="azure">Azure</option>
              <option value="gcp">Google Cloud Platform</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="vaultEngineVersion">Engine Version *</label>
            <select
              id="vaultEngineVersion"
              value={formData.engine_version}
              onChange={(e) => setFormData(prev => ({ ...prev, engine_version: e.target.value }))}
              required
            >
              <option value="2">Version 2 (Recommended)</option>
              <option value="1">Version 1</option>
              <option value="kv">Legacy KV</option>
            </select>
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
              {config ? 'Update' : 'Create'}
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

const ConfigurationsPage: React.FC = () => {
  const location = useLocation();
  const [dockerMappings, setDockerMappings] = useState<DockerMapping[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingMapping, setEditingMapping] = useState<DockerMapping | null>(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deletingMapping, setDeletingMapping] = useState<DockerMapping | null>(null);
  
  // Resource mapping states
  const [resourceMappings, setResourceMappings] = useState<ResourceMapping[]>([]);
  const [showResourceCreateModal, setShowResourceCreateModal] = useState(false);
  const [editingResourceMapping, setEditingResourceMapping] = useState<ResourceMapping | null>(null);
  const [showResourceDeleteModal, setShowResourceDeleteModal] = useState(false);
  const [deletingResourceMapping, setDeletingResourceMapping] = useState<ResourceMapping | null>(null);

  // Vault configuration states
  const [vaultConfigs, setVaultConfigs] = useState<VaultConfig[]>([]);
  const [showVaultCreateModal, setShowVaultCreateModal] = useState(false);
  const [editingVaultConfig, setEditingVaultConfig] = useState<VaultConfig | null>(null);
  const [showVaultDeleteModal, setShowVaultDeleteModal] = useState(false);
  const [deletingVaultConfig, setDeletingVaultConfig] = useState<VaultConfig | null>(null);
  const [testingConnection, setTestingConnection] = useState<string | null>(null);

  const active = useMemo<'docker' | 'custom' | 'vault'>(() => {
    if (location.pathname.startsWith('/configurations/custom')) return 'custom';
    if (location.pathname.startsWith('/configurations/vault')) return 'vault';
    return 'docker';
  }, [location.pathname]);

  // Accepted script types
  const acceptedScriptTypes = [
    'python', 'nodejs', 'ansible', 'terraform', 'sh', 'bash', 'zsh'
  ];

  // Fetch Docker mappings
  const fetchDockerMappings = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await getDockerMappings();
      if (response.data.success) {
        setDockerMappings(response.data.mappings);
      }
    } catch (err: any) {
      console.error('Error fetching Docker mappings:', err);
      setError(err.response?.data?.detail || 'Failed to fetch Docker mappings');
    } finally {
      setLoading(false);
    }
  };

  // Load Docker mappings when docker tab is active
  useEffect(() => {
    if (active === 'docker') {
      fetchDockerMappings();
    }
  }, [active]);

  // Fetch resource mappings
  const fetchResourceMappings = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await getResourceMappings();
      if (response.data.success) {
        setResourceMappings(response.data.mappings);
      }
    } catch (err: any) {
      console.error('Error fetching resource mappings:', err);
      setError(err.response?.data?.detail || 'Failed to fetch resource mappings');
    } finally {
      setLoading(false);
    }
  };

  // Load resource mappings when custom tab is active
  useEffect(() => {
    if (active === 'custom') {
      fetchResourceMappings();
    }
  }, [active]);

  // Fetch vault configurations
  const fetchVaultConfigs = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await getVaultConfigs();
      console.log('Vault configs response:', response.data);
      if (response.data.success) {
        setVaultConfigs(response.data.configs || []);
      } else {
        setVaultConfigs([]);
        setError('Failed to fetch vault configurations');
      }
    } catch (err: any) {
      console.error('Error fetching vault configurations:', err);
      setError(err.response?.data?.detail || 'Failed to fetch vault configurations');
      setVaultConfigs([]);
    } finally {
      setLoading(false);
    }
  };

  // Load vault configurations when vault tab is active
  useEffect(() => {
    if (active === 'vault') {
      fetchVaultConfigs();
    }
  }, [active]);

  // Initialize vault configs on component mount
  useEffect(() => {
    setVaultConfigs([]);
  }, []);

  // Handle create Docker mapping
  const handleCreateMapping = async (data: CreateDockerMappingRequest) => {
    try {
      setLoading(true);
      setError(null);
      const response = await createDockerMapping(data);
      if (response.data.success) {
        setShowCreateModal(false);
        fetchDockerMappings();
      }
    } catch (err: any) {
      console.error('Error creating Docker mapping:', err);
      setError(err.response?.data?.detail || 'Failed to create Docker mapping');
    } finally {
      setLoading(false);
    }
  };

  // Handle update Docker mapping
  const handleUpdateMapping = async (mappingId: string, data: UpdateDockerMappingRequest) => {
    try {
      setLoading(true);
      setError(null);
      const response = await updateDockerMapping(mappingId, data);
      if (response.data.success) {
        setEditingMapping(null);
        fetchDockerMappings();
      }
    } catch (err: any) {
      console.error('Error updating Docker mapping:', err);
      setError(err.response?.data?.detail || 'Failed to update Docker mapping');
    } finally {
      setLoading(false);
    }
  };

  // Handle delete Docker mapping
  const handleDeleteMapping = async () => {
    if (!deletingMapping) return;
    
    try {
      setLoading(true);
      setError(null);
      const response = await deleteDockerMapping(deletingMapping.id);
      if (response.data.success) {
        setShowDeleteModal(false);
        setDeletingMapping(null);
        fetchDockerMappings();
      }
    } catch (err: any) {
      console.error('Error deleting Docker mapping:', err);
      setError(err.response?.data?.detail || 'Failed to delete Docker mapping');
    } finally {
      setLoading(false);
    }
  };

  // Handle create resource mapping
  const handleCreateResourceMapping = async (data: CreateResourceMappingRequest) => {
    try {
      setLoading(true);
      setError(null);
      const response = await createResourceMapping(data);
      if (response.data.success) {
        setShowResourceCreateModal(false);
        fetchResourceMappings();
      }
    } catch (err: any) {
      console.error('Error creating resource mapping:', err);
      setError(err.response?.data?.detail || 'Failed to create resource mapping');
    } finally {
      setLoading(false);
    }
  };

  // Handle update resource mapping
  const handleUpdateResourceMapping = async (mappingId: string, data: UpdateResourceMappingRequest) => {
    try {
      setLoading(true);
      setError(null);
      const response = await updateResourceMapping(mappingId, data);
      if (response.data.success) {
        setEditingResourceMapping(null);
        fetchResourceMappings();
      }
    } catch (err: any) {
      console.error('Error updating resource mapping:', err);
      setError(err.response?.data?.detail || 'Failed to update resource mapping');
    } finally {
      setLoading(false);
    }
  };

  // Handle delete resource mapping
  const handleDeleteResourceMapping = async () => {
    if (!deletingResourceMapping) return;
    
    try {
      setLoading(true);
      setError(null);
      const response = await deleteResourceMapping(deletingResourceMapping.id);
      if (response.data.success) {
        setShowResourceDeleteModal(false);
        setDeletingResourceMapping(null);
        fetchResourceMappings();
      }
    } catch (err: any) {
      console.error('Error deleting resource mapping:', err);
      setError(err.response?.data?.detail || 'Failed to delete resource mapping');
    } finally {
      setLoading(false);
    }
  };

  // Handle create vault configuration
  const handleCreateVaultConfig = async (data: CreateVaultConfigRequest) => {
    try {
      setLoading(true);
      setError(null);
      const response = await createVaultConfig(data);
      if (response.data.success) {
        setShowVaultCreateModal(false);
        fetchVaultConfigs();
      }
    } catch (err: any) {
      console.error('Error creating vault configuration:', err);
      setError(err.response?.data?.detail || 'Failed to create vault configuration');
    } finally {
      setLoading(false);
    }
  };

  // Handle update vault configuration
  const handleUpdateVaultConfig = async (configId: string, data: UpdateVaultConfigRequest) => {
    try {
      setLoading(true);
      setError(null);
      const response = await updateVaultConfig(configId, data);
      if (response.data.success) {
        setEditingVaultConfig(null);
        fetchVaultConfigs();
      }
    } catch (err: any) {
      console.error('Error updating vault configuration:', err);
      setError(err.response?.data?.detail || 'Failed to update vault configuration');
    } finally {
      setLoading(false);
    }
  };

  // Handle delete vault configuration
  const handleDeleteVaultConfig = async () => {
    if (!deletingVaultConfig) return;
    
    try {
      setLoading(true);
      setError(null);
      const response = await deleteVaultConfig(deletingVaultConfig.id);
      if (response.data.success) {
        setShowVaultDeleteModal(false);
        setDeletingVaultConfig(null);
        fetchVaultConfigs();
      }
    } catch (err: any) {
      console.error('Error deleting vault configuration:', err);
      setError(err.response?.data?.detail || 'Failed to delete vault configuration');
    } finally {
      setLoading(false);
    }
  };

  // Handle test vault connection
  const handleTestVaultConnection = async (configId: string) => {
    try {
      setTestingConnection(configId);
      setError(null);
      const response = await testVaultConnection(configId);
      if (response.data.success) {
        alert('Vault connection test successful!');
      } else {
        alert('Vault connection test failed');
      }
    } catch (err: any) {
      console.error('Error testing vault connection:', err);
      alert(err.response?.data?.detail || 'Failed to test vault connection');
    } finally {
      setTestingConnection(null);
    }
  };

  // Format environment variables for display
  const formatEnvVars = (envVars: Record<string, string>) => {
    return Object.entries(envVars).map(([key, value]) => `${key}=${value}`).join(', ');
  };

  // Format arrays for display
  const formatArray = (arr: string[]) => {
    return arr.join(', ');
  };

  return (
    <div>
      <div className="workflows-content">
        <div className="workflows-header">
          <h1>Configurations</h1>
        </div>
        <div className="workflows-body">
          {active === 'docker' && (
            <div className="docker-mappings-section">
              <div className="section-header">
              <h2>Docker Execution Mapping</h2>
                <button 
                  onClick={() => setShowCreateModal(true)}
                  className="create-button"
                >
                  + Create Mapping
                </button>
              </div>

              {error && (
                <div className="error-message">
                  {error}
                  <button onClick={fetchDockerMappings} className="retry-button">
                    Retry
                  </button>
                </div>
              )}

              {loading ? (
                <div className="loading-spinner">Loading...</div>
              ) : dockerMappings.length === 0 ? (
                <div className="no-mappings">
                  <p>No Docker mappings found. Create your first mapping to get started.</p>
                </div>
              ) : (
                <div className="mappings-grid">
                  {dockerMappings.map((mapping) => (
                    <div key={mapping.id} className="mapping-card">
                      <div className="mapping-header">
                        <h3>{mapping.script_type}</h3>
                        <div className="mapping-actions">
                          <button 
                            onClick={() => setEditingMapping(mapping)}
                            className="edit-button"
                            title="Edit Mapping"
                          >
                            ✏️
                          </button>
                          <button 
                            onClick={() => {
                              setDeletingMapping(mapping);
                              setShowDeleteModal(true);
                            }}
                            className="delete-button"
                            title="Delete Mapping"
                          >
                            🗑️
                          </button>
                        </div>
                      </div>
                      
                      <div className="mapping-details">
                        <div className="detail-row">
                          <strong>Image:</strong> {mapping.docker_image}:{mapping.docker_tag}
                        </div>
                        <div className="detail-row">
                          <strong>Description:</strong> {mapping.description}
                        </div>
                        {Object.keys(mapping.environment_variables).length > 0 && (
                          <div className="detail-row">
                            <strong>Environment:</strong> {formatEnvVars(mapping.environment_variables)}
                          </div>
                        )}
                        {mapping.volumes.length > 0 && (
                          <div className="detail-row">
                            <strong>Volumes:</strong> {formatArray(mapping.volumes)}
                          </div>
                        )}
                        {mapping.ports.length > 0 && (
                          <div className="detail-row">
                            <strong>Ports:</strong> {formatArray(mapping.ports)}
                          </div>
                        )}
                        <div className="detail-row">
                          <strong>Status:</strong> 
                          <span className={`status-badge ${mapping.is_active ? 'active' : 'inactive'}`}>
                            {mapping.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
          {active === 'custom' && (
            <div className="custom-mappings-section">
              <div className="section-header">
                <h2>Custom Mappings</h2>
                <p>Define custom resource mappings and run commands for your workflows.</p>
              </div>

              {/* Resource Mappings Section */}
              <div className="mapping-subsection">
                <div className="subsection-header">
                  <h3>Resource Mappings</h3>
                  <button 
                    onClick={() => setShowResourceCreateModal(true)}
                    className="create-button"
                  >
                    + Create Resource Mapping
                  </button>
                </div>

                {error && (
                  <div className="error-message">
                    {error}
                    <button onClick={fetchResourceMappings} className="retry-button">
                      Retry
                    </button>
                  </div>
                )}

                {loading ? (
                  <div className="loading-spinner">Loading...</div>
                ) : resourceMappings.length === 0 ? (
                  <div className="no-mappings">
                    <p>No resource mappings found. Create your first mapping to get started.</p>
                  </div>
                ) : (
                  <div className="mappings-grid">
                    {resourceMappings.map((mapping) => (
                      <div key={mapping.id} className="mapping-card resource-mapping-card">
                        <div className="mapping-header">
                          <h4>{mapping.mapping_type}</h4>
                          <div className="mapping-actions">
                            <button 
                              onClick={() => setEditingResourceMapping(mapping)}
                              className="edit-button"
                              title="Edit Mapping"
                            >
                              ✏️
                            </button>
                            <button 
                              onClick={() => {
                                setDeletingResourceMapping(mapping);
                                setShowResourceDeleteModal(true);
                              }}
                              className="delete-button"
                              title="Delete Mapping"
                            >
                              🗑️
                            </button>
                          </div>
                        </div>
                        
                        <div className="mapping-details">
                          <div className="detail-row">
                            <strong>Source:</strong> {mapping.source_resource}
                          </div>
                          <div className="detail-row">
                            <strong>Target:</strong> {mapping.target_resource}
                          </div>
                          <div className="detail-row">
                            <strong>Description:</strong> {mapping.description}
                          </div>
                          {Object.keys(mapping.metadata).length > 0 && (
                            <div className="detail-row">
                              <strong>Metadata:</strong> 
                              <div className="metadata-display">
                                {Object.entries(mapping.metadata).map(([key, value]) => (
                                  <div key={key} className="metadata-item">
                                    <span className="metadata-key">{key}:</span>
                                    <span className="metadata-value">{String(value)}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                          <div className="detail-row">
                            <strong>Status:</strong> 
                            <span className={`status-badge ${mapping.is_active ? 'active' : 'inactive'}`}>
                              {mapping.is_active ? 'Active' : 'Inactive'}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Additional Custom Mapping Types can be added here */}
              <div className="mapping-subsection">
                <div className="subsection-header">
                  <h3>Run Commands & Environments</h3>
                  <p>Define custom run commands and environments for your workflow steps.</p>
                </div>
                <div className="placeholder-content">
                  <p>Custom run command and environment configuration options will be available here.</p>
                </div>
              </div>
            </div>
          )}
          {active === 'vault' && (
            <div className="vault-config-section">
              <div className="section-header">
                <h2>Vault Configuration (HashiCorp)</h2>
                <p>Configure HashiCorp Vault connections for secure secret management during workflow execution.</p>
                <button 
                  onClick={() => setShowVaultCreateModal(true)}
                  className="create-button"
                >
                  + Create Vault Config
                </button>
              </div>

              {error && (
                <div className="error-message">
                  {error}
                  <button onClick={fetchVaultConfigs} className="retry-button">
                    Retry
                  </button>
                </div>
              )}

              {loading ? (
                <div className="loading-spinner">Loading...</div>
              ) : !vaultConfigs || vaultConfigs.length === 0 ? (
                <div className="no-mappings">
                  <p>No vault configurations found. Create your first configuration to get started.</p>
                </div>
              ) : (
                <div className="mappings-grid">
                  {vaultConfigs && vaultConfigs.map((config) => (
                    <div key={config.id} className="mapping-card vault-config-card">
                      <div className="mapping-header">
                        <h3>{config.config_name}</h3>
                        <div className="mapping-actions">
                          <button 
                            onClick={() => handleTestVaultConnection(config.id)}
                            className="test-button"
                            title="Test Connection"
                            disabled={testingConnection === config.id}
                          >
                            {testingConnection === config.id ? '⏳' : '🔗'}
                          </button>
                          <button 
                            onClick={() => setEditingVaultConfig(config)}
                            className="edit-button"
                            title="Edit Configuration"
                          >
                            ✏️
                          </button>
                          <button 
                            onClick={() => {
                              setDeletingVaultConfig(config);
                              setShowVaultDeleteModal(true);
                            }}
                            className="delete-button"
                            title="Delete Configuration"
                          >
                            🗑️
                          </button>
                        </div>
                      </div>
                      
                      <div className="mapping-details">
                        <div className="detail-row">
                          <strong>Address:</strong> {config.vault_address}
                        </div>
                        <div className="detail-row">
                          <strong>Mount Path:</strong> {config.mount_path}
                        </div>
                        <div className="detail-row">
                          <strong>Engine Type:</strong> {config.engine_type.toUpperCase()}
                        </div>
                        <div className="detail-row">
                          <strong>Engine Version:</strong> {config.engine_version}
                        </div>
                        {config.namespace && (
                          <div className="detail-row">
                            <strong>Namespace:</strong> {config.namespace}
                          </div>
                        )}
                        <div className="detail-row">
                          <strong>Status:</strong> 
                          <span className={`status-badge ${config.is_active ? 'active' : 'inactive'}`}>
                            {config.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Create/Edit Docker Mapping Modal */}
      {(showCreateModal || editingMapping) && (
        <DockerMappingModal
          mapping={editingMapping}
          onSubmit={editingMapping ? 
            (data) => handleUpdateMapping(editingMapping.id, data) : 
            handleCreateMapping
          }
          onCancel={() => {
            setShowCreateModal(false);
            setEditingMapping(null);
          }}
          acceptedScriptTypes={acceptedScriptTypes}
        />
      )}

      {/* Create/Edit Resource Mapping Modal */}
      {(showResourceCreateModal || editingResourceMapping) && (
        <ResourceMappingModal
          mapping={editingResourceMapping}
          onSubmit={editingResourceMapping ? 
            (data) => handleUpdateResourceMapping(editingResourceMapping.id, data) : 
            handleCreateResourceMapping
          }
          onCancel={() => {
            setShowResourceCreateModal(false);
            setEditingResourceMapping(null);
          }}
        />
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && deletingMapping && (
        <div className="modal-overlay">
          <div className="modal">
            <h3>Confirm Deletion</h3>
            <p>Are you sure you want to delete the Docker mapping for <strong>{deletingMapping.script_type}</strong>?</p>
            <p>This action cannot be undone.</p>
            <div className="modal-buttons">
              <button
                onClick={handleDeleteMapping}
                disabled={loading}
                className="modal-button confirm"
              >
                {loading ? 'Deleting...' : 'Delete'}
              </button>
              <button
                onClick={() => {
                  setShowDeleteModal(false);
                  setDeletingMapping(null);
                }}
                className="modal-button cancel"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Resource Mapping Delete Confirmation Modal */}
      {showResourceDeleteModal && deletingResourceMapping && (
        <div className="modal-overlay">
          <div className="modal">
            <h3>Confirm Deletion</h3>
            <p>Are you sure you want to delete the resource mapping for <strong>{deletingResourceMapping.mapping_type}</strong>?</p>
            <p>This action cannot be undone.</p>
            <div className="modal-buttons">
              <button
                onClick={handleDeleteResourceMapping}
                disabled={loading}
                className="modal-button confirm"
              >
                {loading ? 'Deleting...' : 'Delete'}
              </button>
              <button
                onClick={() => {
                  setShowResourceDeleteModal(false);
                  setDeletingResourceMapping(null);
                }}
                className="modal-button cancel"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create/Edit Vault Configuration Modal */}
      {(showVaultCreateModal || editingVaultConfig) && (
        <VaultConfigModal
          config={editingVaultConfig}
          onSubmit={editingVaultConfig ? 
            (data) => handleUpdateVaultConfig(editingVaultConfig.id, data) : 
            handleCreateVaultConfig
          }
          onCancel={() => {
            setShowVaultCreateModal(false);
            setEditingVaultConfig(null);
          }}
        />
      )}

      {/* Vault Configuration Delete Confirmation Modal */}
      {showVaultDeleteModal && deletingVaultConfig && (
        <div className="modal-overlay">
          <div className="modal">
            <h3>Confirm Deletion</h3>
            <p>Are you sure you want to delete the vault configuration <strong>{deletingVaultConfig.config_name}</strong>?</p>
            <p>This action cannot be undone.</p>
            <div className="modal-buttons">
              <button
                onClick={handleDeleteVaultConfig}
                disabled={loading}
                className="modal-button confirm"
              >
                {loading ? 'Deleting...' : 'Delete'}
              </button>
              <button
                onClick={() => {
                  setShowVaultDeleteModal(false);
                  setDeletingVaultConfig(null);
                }}
                className="modal-button cancel"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ConfigurationsPage; 