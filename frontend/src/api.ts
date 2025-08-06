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

// Workflow API interfaces
export interface WorkflowStep {
  action: string;
  target?: string;
  [key: string]: any;
}

export interface WorkflowCreate {
  name: string;
  description?: string;
  steps: WorkflowStep[];
  is_active?: boolean;
  script_type?: string;
  script_content?: string;
  script_filename?: string;
  run_command?: string;
  dependencies?: string[];
}

export interface WorkflowUpdate {
  name?: string;
  description?: string;
  steps?: WorkflowStep[];
  is_active?: boolean;
  script_type?: string;
  script_content?: string;
  script_filename?: string;
  run_command?: string;
  dependencies?: string[];
}

export interface Workflow {
  id: number;
  name: string;
  description?: string;
  steps: WorkflowStep[];
  is_active: boolean;
  script_type?: string;
  script_content?: string;
  script_filename?: string;
  run_command?: string;
  dependencies?: string[];
  created_at: string;
  updated_at: string;
  user_id: number;
}

// Workflow API functions
export const getWorkflows = (): Promise<AxiosResponse<Workflow[]>> => 
  API.get('/workflow/list');

export const getWorkflow = (workflowId: number): Promise<AxiosResponse<Workflow>> => 
  API.get(`/workflow/${workflowId}`);

export const createWorkflow = (workflow: WorkflowCreate): Promise<AxiosResponse<Workflow>> => 
  API.post('/workflow/create', workflow);

export const updateWorkflow = (workflowId: number, workflow: WorkflowUpdate): Promise<AxiosResponse<Workflow>> => 
  API.put(`/workflow/${workflowId}`, workflow);

export const deleteWorkflow = (workflowId: number): Promise<AxiosResponse> => 
  API.delete(`/workflow/${workflowId}`);

export const executeWorkflow = (workflowId: number): Promise<AxiosResponse> => 
  API.post(`/workflow/${workflowId}/execute`);

export const getWorkflowExecutions = (workflowId: number): Promise<AxiosResponse> => 
  API.get(`/workflow/${workflowId}/executions`);

export const installWorkflowDependencies = (workflowId: number): Promise<AxiosResponse> => 
  API.post(`/workflow/${workflowId}/install-dependencies`);

// Admin User Management API interfaces
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

// Admin User Management API functions
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