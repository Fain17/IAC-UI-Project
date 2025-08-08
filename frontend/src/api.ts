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

    if (error.response?.status === 401 && !originalRequest._retry) {
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
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
  updated_at: string;
  permission_level: string;
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

export const getAdminUser = (userId: number): Promise<AxiosResponse<AdminUser>> => 
  API.get(`/admin/users/${userId}`);

export interface UpdateUserPermissionsRequest {
  permission_level: string;
  is_admin?: boolean;
  is_active?: boolean;
}

export const updateUserPermissions = (userId: number, permissions: UpdateUserPermissionsRequest): Promise<AxiosResponse<AdminUser>> => 
  API.put(`/admin/users/${userId}/permissions`, permissions);

export interface UpdateUserActiveStatusRequest {
  is_active: boolean;
}

export const updateUserActiveStatus = (userId: number, isActive: boolean): Promise<AxiosResponse<AdminUser>> => 
  API.patch(`/admin/users/${userId}/active-status`, { is_active: isActive });

export const getUserPermissions = (userId: number): Promise<AxiosResponse<{ permission_level: string; is_active: boolean; is_admin: boolean }>> => 
  API.get(`/admin/users/${userId}/permissions`);

export const getCurrentUserPermissions = (): Promise<AxiosResponse<{ permission_level: string; is_active: boolean; is_admin: boolean }>> => 
  API.get('/settings/permissions');

export const getAllUsersPermissions = (): Promise<AxiosResponse<{ users: Array<{ id: number; username: string; email: string; permission_level: string; is_active: boolean; is_admin: boolean }> }>> => 
  API.get('/settings/permissions');

export const getAllUsersPermissionsNew = (): Promise<AxiosResponse<{ 
  user_permissions: Array<{ 
    user_id: number; 
    username: string; 
    email: string; 
    is_active: boolean; 
    is_admin: boolean; 
    permission_level: string; 
    permission_created_at: string; 
    permission_updated_at: string; 
  }>; 
  count: number; 
  permission_summary: { 
    admin: number; 
    manager: number; 
    viewer: number; 
  }; 
}>> => 
  API.get('/admin/users/permissions/all');

export const deleteUser = (userId: number): Promise<AxiosResponse> => 
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