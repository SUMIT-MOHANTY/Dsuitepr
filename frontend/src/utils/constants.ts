// App Configuration
export const APP_NAME = import.meta.env.VITE_APP_NAME || 'Flask React Todo App';
export const APP_VERSION = import.meta.env.VITE_APP_VERSION || '1.0.0';
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';

// Local Storage Keys
export const STORAGE_KEYS = {
  AUTH_TOKEN: 'todo_app_auth_token',
  USER_DATA: 'todo_app_user_data',
  THEME: 'todo_app_theme',
  FILTERS: 'todo_app_filters',
} as const;

// Route Paths
export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  REGISTER: '/register',
  DASHBOARD: '/dashboard',
  PROFILE: '/profile',
  NOT_FOUND: '/404',
} as const;

// Priority Configurations
export const PRIORITY_CONFIG = {
  low: {
    label: 'Low',
    color: 'bg-slate-100 text-slate-700',
    borderColor: 'border-slate-300',
    icon: 'arrow-down',
  },
  medium: {
    label: 'Medium',
    color: 'bg-warning-100 text-warning-700',
    borderColor: 'border-warning-300',
    icon: 'minus',
  },
  high: {
    label: 'High',
    color: 'bg-error-100 text-error-700',
    borderColor: 'border-error-300',
    icon: 'arrow-up',
  },
} as const;

// Status Configurations
export const STATUS_CONFIG = {
  all: { label: 'All Tasks', color: 'text-slate-600' },
  active: { label: 'Active', color: 'text-primary-600' },
  completed: { label: 'Completed', color: 'text-success-600' },
} as const;

// Sort Options
export const SORT_OPTIONS = [
  { value: 'createdAt', label: 'Created Date' },
  { value: 'dueDate', label: 'Due Date' },
  { value: 'priority', label: 'Priority' },
] as const;

// Pagination
export const DEFAULT_PAGE_SIZE = 20;
export const MAX_PAGE_SIZE = 100;

// Debounce Delays
export const DEBOUNCE_DELAY = {
  SEARCH: 300,
  INPUT: 500,
  RESIZE: 250,
} as const;

// Error Messages
export const ERROR_MESSAGES = {
  GENERIC: 'Something went wrong. Please try again.',
  NETWORK: 'Network error. Please check your connection.',
  UNAUTHORIZED: 'Session expired. Please log in again.',
  FORBIDDEN: 'You do not have permission to perform this action.',
  NOT_FOUND: 'The requested resource was not found.',
  VALIDATION: 'Please check your input and try again.',
} as const;

// Success Messages
export const SUCCESS_MESSAGES = {
  LOGIN: 'Welcome back!',
  REGISTER: 'Account created successfully!',
  LOGOUT: 'You have been logged out.',
  TODO_CREATED: 'Task created successfully!',
  TODO_UPDATED: 'Task updated successfully!',
  TODO_DELETED: 'Task deleted successfully!',
  PROFILE_UPDATED: 'Profile updated successfully!',
  PASSWORD_CHANGED: 'Password changed successfully!',
} as const;
