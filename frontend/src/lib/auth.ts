/**
 * Authentication utility functions
 * Handles login, registration, logout, and user state management
 */

import { getApiBaseUrl } from './api-config';

export interface User {
  id: number;
  email: string;
  username: string;
  full_name?: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  preferred_categories?: string[];
  onboarding_completed?: boolean;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface RegisterData {
  email: string;
  username: string;
  password: string;
  full_name?: string;
  referral_code?: string;
}

const AUTH_TOKEN_KEY = 'auth_token';

/**
 * Store authentication token
 */
export function setAuthToken(token: string): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem(AUTH_TOKEN_KEY, token);
    // Also set in cookie for middleware access
    document.cookie = `${AUTH_TOKEN_KEY}=${token}; path=/; max-age=${30 * 24 * 60 * 60}; SameSite=Lax`;
  }
}

/**
 * Get authentication token
 */
export function getAuthToken(): string | null {
  if (typeof window !== 'undefined') {
    return localStorage.getItem(AUTH_TOKEN_KEY);
  }
  return null;
}

/**
 * Remove authentication token
 */
export function removeAuthToken(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    // Also remove from cookie
    document.cookie = `${AUTH_TOKEN_KEY}=; path=/; max-age=0; SameSite=Lax`;
  }
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated(): boolean {
  return getAuthToken() !== null;
}

/**
 * Login with email and password
 */
export async function login(email: string, password: string): Promise<LoginResponse> {
  const apiUrl = getApiBaseUrl();
  
  const response = await fetch(`${apiUrl}/api/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Login failed' }));
    throw new Error(error.detail || 'Login failed');
  }

  const data: LoginResponse = await response.json();
  setAuthToken(data.access_token);
  return data;
}

/**
 * Register a new user
 */
export async function register(userData: RegisterData): Promise<LoginResponse> {
  const apiUrl = getApiBaseUrl();
  
  const response = await fetch(`${apiUrl}/api/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(userData),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Registration failed' }));
    throw new Error(error.detail || 'Registration failed');
  }

  const data: LoginResponse = await response.json();
  setAuthToken(data.access_token);
  return data;
}

/**
 * Get current user information
 */
export async function getCurrentUser(): Promise<User | null> {
  const token = getAuthToken();
  if (!token) {
    return null;
  }

  const apiUrl = getApiBaseUrl();
  
  try {
    const response = await fetch(`${apiUrl}/api/auth/me`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      if (response.status === 401) {
        // Token is invalid, remove it
        removeAuthToken();
        return null;
      }
      throw new Error('Failed to fetch user');
    }

    const user: User = await response.json();
    return user;
  } catch (error) {
    console.error('Error fetching current user:', error);
    return null;
  }
}

/**
 * Logout user
 */
export function logout(): void {
  removeAuthToken();
  // Redirect to home page
  if (typeof window !== 'undefined') {
    window.location.href = '/';
  }
}

/**
 * Initiate Google OAuth login
 */
export function googleLogin(): void {
  const apiUrl = getApiBaseUrl();
  // Redirect to backend OAuth endpoint
  window.location.href = `${apiUrl}/api/auth/google/login`;
}

/**
 * Handle OAuth callback (called from signin page after redirect)
 * Extracts token from URL parameters and stores it
 */
export function handleOAuthCallback(): string | null {
  if (typeof window === 'undefined') {
    return null;
  }

  const params = new URLSearchParams(window.location.search);
  const token = params.get('token');
  const error = params.get('error');
  const success = params.get('success');

  // Log for debugging
  console.log('OAuth callback:', { token: token ? 'present' : 'missing', error, success });

  if (error) {
    console.error('OAuth error in callback:', error);
    throw new Error(`OAuth error: ${error}`);
  }

  // Try to get token from URL
  if (success === 'true' && token) {
    console.log('Token received, storing...');
    setAuthToken(token);
    // Clean up URL to remove sensitive token
    const cleanUrl = window.location.pathname;
    window.history.replaceState({}, document.title, cleanUrl);
    console.log('Token stored successfully');
    return token;
  }

  // If success=true but no token, something went wrong
  if (success === 'true' && !token) {
    console.error('Success flag set but no token received');
    throw new Error('OAuth authentication succeeded but token was not received');
  }

  return null;
}

