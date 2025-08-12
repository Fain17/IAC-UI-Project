import axios, { AxiosResponse } from 'axios';
import tokenManager from './utils/tokenManager';

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

// Add response interceptor to handle token refresh on 401 errors
API.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    const status = error.response?.status;
    const detail: string | undefined = error.response?.data?.detail;

    // If backend indicates the token is invalid, logout immediately
    if (
      status === 401 &&
      typeof detail === 'string' &&
      (/invalid token/i.test(detail) || /could not validate credentials/i.test(detail) || /token is invalid/i.test(detail))
    ) {
      tokenManager.clearAuth();
      return Promise.reject(error);
    }

    if (status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshSuccess = await tokenManager.refreshAccessToken();
        if (refreshSuccess) {
          // Retry the original request with new token
          const newToken = tokenManager.getToken();
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          return API(originalRequest);
        }
      } catch (refreshError) {
        console.error('Token refresh failed:', refreshError);
      }

      // If refresh failed, logout user
      tokenManager.clearAuth();
    }

    return Promise.reject(error);
  }
);

export interface MappingResponse {
  data: {
    mappings: { [key: string]: string };
  };
}

export const getMappings = (): Promise<MappingResponse> => API.get('/workflow/get-all-mappings');
export const createMapping = (instance: string, launch_template: string): Promise<AxiosResponse> =>
  API.post('/workflow/create-mapping', { instance, launch_template });
export const deleteMapping = (instance: string): Promise<AxiosResponse> =>
  API.post('/workflow/delete-mapping', { instance });
export const runLaunchUpdate = (instance: string, launch_template: string): Promise<AxiosResponse> =>
  API.post('/workflow/run-json', { server: instance, lt: launch_template });

// Check if there are any existing users (for first user detection)
export const checkFirstUser = (): Promise<AxiosResponse> => 
  API.get('/auth/check-first-user');

// User Management Interfaces
export interface AdminUser {
  id: string;
  username: string;
  email: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
  updated_at: string;
  role: string;
  groups: string[];
}

export interface AdminUsersResponse {
  users: AdminUser[];
}

export interface CreateUserRequest {
  username: string;
  email: string;
  password: string;
  role?: string;
  group?: string;
  is_active?: boolean;
}

export const getAdminUsers = (): Promise<AxiosResponse<AdminUsersResponse>> => 
  API.get('/admin/users');

export const createAdminUser = (userData: CreateUserRequest): Promise<AxiosResponse<AdminUser>> => 
  API.post('/admin/users', userData);

export const getAdminUser = (userId: string): Promise<AxiosResponse<AdminUser>> =>
  API.get(`/admin/users/${userId}`);

export interface UpdateUserPermissionsRequest {
  role: 'admin' | 'manager' | 'viewer';
  is_active?: boolean;
}

// Update user permissions using the new API format
// Payload: { "role": "admin" | "manager" | "viewer", "is_active": boolean }
export const updateUserPermissionsNew = (userId: string, permissions: UpdateUserPermissionsRequest): Promise<AxiosResponse<AdminUser>> => {
  console.log('🚀 API: updateUserPermissionsNew called with:', { userId, permissions });
  console.log('🚀 API: Sending payload:', permissions);
  return API.put(`/admin/users/${userId}/permissions`, permissions);
};

export interface UpdateUserActiveStatusRequest {
  is_active: boolean;
}

export const updateUserActiveStatus = (userId: string, isActive: boolean): Promise<AxiosResponse<AdminUser>> =>
  API.patch(`/admin/users/${userId}/active-status`, { is_active: isActive });

export const getUserPermissions = (userId: string): Promise<AxiosResponse<{ permission_level: string; is_active: boolean; is_admin: boolean }>> =>
  API.get(`/admin/users/${userId}/permissions`);

export const getCurrentUserPermissions = (): Promise<AxiosResponse<{ permission_level: string; is_active: boolean; is_admin: boolean }>> => 
  API.get('/settings/permissions');

export const getAllUsersPermissions = (): Promise<AxiosResponse<{ users: Array<{ id: number; username: string; email: string; permission_level: string; is_active: boolean; is_admin: boolean }> }>> => 
  API.get('/settings/permissions');

export const getAllUsersPermissionsNew = (): Promise<AxiosResponse<{ 
  success: boolean;
  permissions: Array<{ 
    id: string; 
    username: string; 
    email: string; 
    is_active: boolean; 
    is_admin: boolean; 
    created_at: string; 
    updated_at: string; 
    role: string; 
    groups: string[]; 
    role_permissions: string[]; 
    description: string; 
  }>; 
  count: number; 
  role_summary: { 
    admin: number; 
    manager: number; 
    viewer: number; 
  }; 
}>> => 
  API.get('/admin/users/permissions/all');

export const deleteUser = (userId: string): Promise<AxiosResponse> =>
  API.delete(`/admin/users/${userId}`);

// Workflow Step Management APIs
export interface WorkflowStep {
  id: string;
  name: string;
  description?: string;
  order: number;
  script_type?: string;
  script_filename?: string;
  run_command?: string;
  dependencies?: string[];
  parameters?: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  directory_name?: string;
}

export interface CreateStepRequest {
  name: string;
  description?: string;
  order?: number;
  script_type?: string;
  script_filename?: string;
  run_command?: string;
  dependencies?: string[];
  parameters?: Record<string, any>;
  is_active?: boolean;
}

export interface UpdateStepRequest {
  name?: string;
  description?: string;
  order?: number;
  script_type?: string;
  script_filename?: string;
  run_command?: string;
  dependencies?: string[];
  parameters?: Record<string, any>;
  is_active?: boolean;
}

export interface WorkflowStepsResponse {
  success: boolean;
  workflow_id: string;
  workflow_name: string;
  steps: WorkflowStep[];
  total_steps: number;
}

export interface CreateStepResponse {
  success: boolean;
  message: string;
  step: WorkflowStep;
  total_steps: number;
}

export interface UpdateStepResponse {
  success: boolean;
  message: string;
  updated_step: WorkflowStep;
  total_steps: number;
}

export interface DeleteStepResponse {
  success: boolean;
  message: string;
  deleted_step: WorkflowStep;
  total_steps: number;
}

export interface ReorderStepsResponse {
  success: boolean;
  message: string;
  steps: WorkflowStep[];
  total_steps: number;
}

// Get workflow steps
export const getWorkflowSteps = (workflowId: string): Promise<AxiosResponse<WorkflowStepsResponse>> =>
  API.get(`/workflow/${workflowId}/steps`);

// Add step to workflow
export const addWorkflowStep = (workflowId: string, stepData: CreateStepRequest): Promise<AxiosResponse<CreateStepResponse>> =>
  API.post(`/workflow/${workflowId}/steps`, stepData);

// Update workflow step
export const updateWorkflowStep = (workflowId: string, stepOrder: number, stepData: UpdateStepRequest): Promise<AxiosResponse<UpdateStepResponse>> =>
  API.put(`/workflow/${workflowId}/steps/${stepOrder}`, stepData);

// Update workflow step by ID
export const updateWorkflowStepById = (workflowId: string, stepId: string, stepData: UpdateStepRequest): Promise<AxiosResponse<UpdateStepResponse>> =>
  API.put(`/workflow/${workflowId}/steps/id/${stepId}`, stepData);

// Delete workflow step
export const deleteWorkflowStep = (workflowId: string, stepOrder: number): Promise<AxiosResponse<DeleteStepResponse>> =>
  API.delete(`/workflow/${workflowId}/steps/${stepOrder}`);

// Reorder workflow steps
export const reorderWorkflowSteps = (workflowId: string, stepOrders: number[]): Promise<AxiosResponse<ReorderStepsResponse>> =>
  API.put(`/workflow/${workflowId}/steps/reorder`, stepOrders);

// File Management APIs
export interface UploadFileResponse {
  success: boolean;
  message: string;
  file_path: string;
  file_size: number;
  step_id: string;
}

export interface UploadZipResponse {
  success: boolean;
  message: string;
  extracted_files: string[];
  step_id: string;
}

export interface CreateScriptResponse {
  success: boolean;
  message: string;
  file_path: string;
  file_size: number;
  step_id: string;
}

// Upload single file to step
export const uploadFileToStep = (workflowId: string, stepId: string, file: File): Promise<AxiosResponse<UploadFileResponse>> => {
  const formData = new FormData();
  formData.append('file', file);
  return API.post(`/workflow/${workflowId}/steps/${stepId}/upload-file`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
};

// Upload ZIP file to step
export const uploadZipToStep = (workflowId: string, stepId: string, zipFile: File): Promise<AxiosResponse<UploadZipResponse>> => {
  const formData = new FormData();
  formData.append('zip_file', zipFile);
  return API.post(`/workflow/${workflowId}/steps/${stepId}/upload-zip`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
};

// Create script for step
export const createScriptForStep = (workflowId: string, stepId: string, filename: string, scriptContent: string): Promise<AxiosResponse<CreateScriptResponse>> => {
  const formData = new URLSearchParams();
  formData.append('filename', filename);
  formData.append('script_content', scriptContent);
  return API.post(`/workflow/${workflowId}/steps/${stepId}/create-script`, formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    }
  });
}; 

export interface WorkflowExecutionResultStep {
  id: string;
  name: string;
  order: number;
  status: string;
  execution_time?: number;
  return_code?: number;
  error?: string | null;
  output?: string;
  reason?: string;
}

export interface WorkflowExecutionResponse {
  success: boolean;
  workflow_id: string;
  execution_type: 'local' | 'docker';
  status: string;
  started_at: string;
  ended_at: string;
  total_time: number;
  steps_executed: number;
  steps_skipped: number;
  steps_failed: number;
  results: WorkflowExecutionResultStep[];
}

export interface StepExecutionResponse {
  success: boolean;
  error: string | null;
  execution_time: number;
  output: string;
  status: string;
  return_code: number;
  start_time: string;
  end_time: string;
  workflow_id: string;
  step_id: string;
  step_name: string;
  script_filename?: string;
  run_command?: string;
  execution_type: 'local' | 'docker';
  container_id?: string;
  script_type?: 'python' | 'nodejs';
}

export interface StepExecutionStatusResponse {
  workflow_id: string;
  step_id: string;
  step_name: string;
  workflow_active: boolean;
  step_active: boolean;
  script_filename: string | null;
  run_command: string | null;
  script_type: 'python' | 'nodejs' | null;
  script_exists: boolean;
  script_path?: string;
  docker_available: boolean;
  can_execute: boolean;
  validation_error: string | null;
  execution_prerequisites: Record<string, boolean>;
}

// Execute entire workflow
export const executeEntireWorkflow = (
  workflowId: string,
  executionType: 'local' | 'docker' = 'local',
  continueOnFailure: boolean = false
): Promise<AxiosResponse<WorkflowExecutionResponse>> =>
  API.post(`/workflow/${workflowId}/execute`, null, {
    params: { execution_type: executionType, continue_on_failure: continueOnFailure },
  });

// Execute single step locally
export const executeStepLocal = (
  workflowId: string,
  stepId: string
): Promise<AxiosResponse<StepExecutionResponse>> =>
  API.post(`/workflow/${workflowId}/steps/${stepId}/execute/local`);

// Execute single step in docker
export const executeStepDocker = (
  workflowId: string,
  stepId: string
): Promise<AxiosResponse<StepExecutionResponse>> =>
  API.post(`/workflow/${workflowId}/steps/${stepId}/execute/docker`);

// Get step execution status
export const getStepExecutionStatus = (
  workflowId: string,
  stepId: string
): Promise<AxiosResponse<StepExecutionStatusResponse>> =>
  API.get(`/workflow/${workflowId}/steps/${stepId}/execute/status`); 

export interface AdminGroup {
  id: string;
  name: string;
  description: string;
  created_at?: string;
  updated_at?: string;
}

export interface AdminGroupUser {
  id: string;
  username: string;
  email: string;
  is_active: boolean;
  is_admin: boolean;
}

export const createAdminGroup = (group: { name: string; description?: string }): Promise<AxiosResponse<AdminGroup>> =>
  API.post('/admin/groups', group);

export const getAdminGroups = (): Promise<AxiosResponse<{ groups: AdminGroup[] } | AdminGroup[]>> =>
  API.get('/admin/groups');

export const getUserGroups = (userId: string): Promise<AxiosResponse<{ groups: AdminGroup[] } | AdminGroup[]>> =>
  API.get(`/admin/users/${userId}/groups`);

export const addUserToGroup = (userId: string, groupId: string): Promise<AxiosResponse> =>
  API.post(`/admin/users/${userId}/groups/${groupId}`);

export const removeUserFromGroup = (userId: string, groupId: string): Promise<AxiosResponse> =>
  API.delete(`/admin/users/${userId}/groups/${groupId}`);

export const getGroupUsers = (groupId: string): Promise<AxiosResponse<{ users: AdminGroupUser[] } | AdminGroupUser[]>> =>
  API.get(`/admin/groups/${groupId}/users`);

export const deleteAdminGroup = (groupId: string): Promise<AxiosResponse<{ success: boolean; message: string }>> =>
  API.delete(`/admin/groups/${groupId}`);

export const updateAdminGroup = (groupId: string, groupData: { name: string; description?: string }): Promise<AxiosResponse<AdminGroup>> =>
  API.put(`/admin/groups/${groupId}`, groupData);

// Workflow Sharing APIs
export const shareWorkflowWithGroup = (workflowId: string, groupId: string): Promise<AxiosResponse<{ success: boolean; message: string }>> =>
  API.post(`/workflow/${workflowId}/share/groups/${groupId}`);

export const unshareWorkflowWithGroup = (workflowId: string, groupId: string): Promise<AxiosResponse<{ success: boolean; message: string }>> =>
  API.delete(`/workflow/${workflowId}/share/groups/${groupId}`);

// Get workflow permissions and sharing data
export const getWorkflowPermissions = (workflowId: string): Promise<AxiosResponse<{
  workflow_id: string;
  workflow_name: string;
  workflow_description?: string;
  shared_groups: WorkflowGroupShare[];
  user_permissions: WorkflowPermission[];
}>> => API.get(`/workflow/${workflowId}/permissions`);

// Get all workflows with their permissions (for bulk loading)
export const getAllWorkflowsWithPermissions = (): Promise<AxiosResponse<{
  workflows: Array<{
    workflow: Workflow;
    permissions: {
      shared_groups: WorkflowGroupShare[];
      user_permissions: WorkflowPermission[];
    };
  }>;
}>> => API.get('/workflow/permissions/all');

// Dummy data interfaces for workflow permissions
export interface WorkflowPermission {
  user_id: string;
  username: string;
  email: string;
  permission: 'read' | 'write' | 'admin';
  granted_at: string;
}

export interface WorkflowGroupShare {
  group_id: string;
  group_name: string;
  group_description?: string;
  is_shared: boolean;
  shared_at?: string;
  member_count: number;
}

export interface WorkflowAssignmentData {
  workflow_id: string;
  workflow_name: string;
  workflow_description?: string;
  shared_groups: WorkflowGroupShare[];
  user_permissions: WorkflowPermission[];
} 

// Workflow Management APIs
export interface Workflow {
  id: string;
  name: string;
  description?: string;
  user_id: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  steps: any[];
}

export interface WorkflowListResponse {
  success: boolean;
  workflows: Workflow[];
  count: number;
}

export const getWorkflows = (): Promise<AxiosResponse<WorkflowListResponse>> =>
  API.get('/workflow/list');

export const getWorkflow = (workflowId: string): Promise<AxiosResponse<Workflow>> =>
  API.get(`/workflow/${workflowId}`);

export const createWorkflow = (workflowData: { name: string; description?: string }): Promise<AxiosResponse<{ success: boolean; workflow_id: string; message: string }>> =>
  API.post('/workflow/create', workflowData);

export const updateWorkflow = (workflowId: string, workflowData: { name?: string; description?: string }): Promise<AxiosResponse<{ success: boolean; message: string }>> =>
  API.put(`/workflow/${workflowId}`, workflowData);

export const deleteWorkflow = (workflowId: string): Promise<AxiosResponse<{ success: boolean; message: string }>> =>
  API.delete(`/workflow/${workflowId}`); 