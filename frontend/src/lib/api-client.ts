import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { getApiBaseUrl } from './api-config';

// --- Configuration ---

const API_URL = getApiBaseUrl();

const isServer = typeof window === 'undefined';

// --- Types ---

export interface ApiError {
  message: string;
  status?: number;
  code?: string;
  data?: any;
}

// --- Client Instance ---

class ApiClient {
  private client: AxiosInstance;
  private token: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      // Avoid throwing on 4xx/5xx to handle errors gracefully in wrapper
      validateStatus: (status) => status < 500, 
    });

    // Interceptor to attach token
    this.client.interceptors.request.use((config) => {
      if (this.token) {
        config.headers.Authorization = `Bearer ${this.token}`;
      } else if (!isServer) {
        // Fallback to localStorage for client-side
        const storedToken = localStorage.getItem('auth_token');
        if (storedToken) {
          config.headers.Authorization = `Bearer ${storedToken}`;
        }
      }
      return config;
    });

    // Interceptor for response parsing
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        // Format error
        const apiError: ApiError = {
          message: error.message || 'An unexpected error occurred',
          status: error.response?.status,
          data: error.response?.data,
        };
        return Promise.reject(apiError);
      }
    );
  }

  public setToken(token: string) {
    this.token = token;
    if (!isServer) {
      localStorage.setItem('auth_token', token);
    }
  }

  public clearToken() {
    this.token = null;
    if (!isServer) {
      localStorage.removeItem('auth_token');
    }
  }

  // --- Generic Methods ---

  public async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<T>(url, config);
    if (response.status >= 400) {
        throw {
            message: response.statusText,
            status: response.status,
            data: response.data
        } as ApiError;
    }
    return response.data;
  }

  public async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post<T>(url, data, config);
    if (response.status >= 400) {
        throw {
            message: response.statusText,
            status: response.status,
            data: response.data
        } as ApiError;
    }
    return response.data;
  }

  public async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.put<T>(url, data, config);
    if (response.status >= 400) {
        throw {
            message: response.statusText,
            status: response.status,
            data: response.data
        } as ApiError;
    }
    return response.data;
  }

  public async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete<T>(url, config);
    if (response.status >= 400) {
        throw {
            message: response.statusText,
            status: response.status,
            data: response.data
        } as ApiError;
    }
    return response.data;
  }
}

export const api = new ApiClient();

// Helper hook for SWR or React Query could go here

