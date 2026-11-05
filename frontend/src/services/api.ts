import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { API_BASE_URL, STORAGE_KEYS, ERROR_MESSAGES } from '@utils/constants';
import type { ApiResponse, ApiError } from '@types/api';

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
  timeout: 30000,
});

// Request interceptor
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Get token from localStorage
    const token = localStorage.getItem(STORAGE_KEYS.AUTH_TOKEN);
    
    // Add auth header if token exists and not skipped
    if (token && !config.headers?.['X-Skip-Auth']) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Remove internal header before sending
    delete config.headers['X-Skip-Auth'];
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error: AxiosError<ApiError>) => {
    const { response, request, message } = error;
    
    // Handle different error scenarios
    if (response) {
      const { status, data } = response;
      
      // Handle 401 Unauthorized
      if (status === 401) {
        localStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN);
        localStorage.removeItem(STORAGE_KEYS.USER_DATA);
        // Use a custom event to trigger navigation instead of direct window.location
        // This avoids sandbox escape while still allowing auth state reset
        window.dispatchEvent(new CustomEvent('auth:unauthorized'));
        return Promise.reject({
          success: false,
          error: ERROR_MESSAGES.UNAUTHORIZED,
          statusCode: status,
        } as ApiError);
      }
      
      // Handle 403 Forbidden
      if (status === 403) {
        return Promise.reject({
          success: false,
          error: data?.error || ERROR_MESSAGES.FORBIDDEN,
          message: data?.message,
          statusCode: status,
        } as ApiError);
      }
      
      // Handle 404 Not Found
      if (status === 404) {
        return Promise.reject({
          success: false,
          error: data?.error || ERROR_MESSAGES.NOT_FOUND,
          message: data?.message,
          statusCode: status,
        } as ApiError);
      }
      
      // Handle validation errors (422)
      if (status === 422) {
        return Promise.reject({
          success: false,
          error: data?.error || ERROR_MESSAGES.VALIDATION,
          message: data?.message,
          statusCode: status,
        } as ApiError);
      }
      
      // Handle other errors
      return Promise.reject({
        success: false,
        error: data?.error || ERROR_MESSAGES.GENERIC,
        message: data?.message,
        statusCode: status,
      } as ApiError);
    }
    
    // Handle network errors
    if (request) {
      return Promise.reject({
        success: false,
        error: ERROR_MESSAGES.NETWORK,
        message: 'Unable to connect to the server',
      } as ApiError);
    }
    
    // Handle other errors
    return Promise.reject({
      success: false,
      error: message || ERROR_MESSAGES.GENERIC,
    } as ApiError);
  }
);

// Helper functions for API calls
export const api = {
  get: <T>(url: string, params?: Record<string, unknown>) =>
    apiClient.get<ApiResponse<T>>(url, { params }).then((res) => res.data),
    
  post: <T>(url: string, data?: unknown) =>
    apiClient.post<ApiResponse<T>>(url, data).then((res) => res.data),
    
  put: <T>(url: string, data?: unknown) =>
    apiClient.put<ApiResponse<T>>(url, data).then((res) => res.data),
    
  patch: <T>(url: string, data?: unknown) =>
    apiClient.patch<ApiResponse<T>>(url, data).then((res) => res.data),
    
  delete: <T>(url: string) =>
    apiClient.delete<ApiResponse<T>>(url).then((res) => res.data),
};

export default apiClient;
