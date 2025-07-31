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

export const getMappings = (): Promise<MappingResponse> => API.get('/api/get-all-mappings');
export const createMapping = (instance: string, launch_template: string): Promise<AxiosResponse> =>
  API.post('/api/create-mapping', { instance, launch_template });
export const deleteMapping = (instance: string): Promise<AxiosResponse> =>
  API.post('/api/delete-mapping', { instance });
export const runLaunchUpdate = (instance: string, launch_template: string): Promise<AxiosResponse> =>
  API.post('/api/run-json', { server: instance, lt: launch_template });

// Check if there are any existing users (for first user detection)
export const checkFirstUser = (): Promise<AxiosResponse> => 
  API.get('/auth/check-first-user'); 