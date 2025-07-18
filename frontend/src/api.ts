import axios, { AxiosResponse } from 'axios';

const API = axios.create({
  baseURL: 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' }
});

API.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

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