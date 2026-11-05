import { api } from './api';
import type { User } from '@types/auth';
import type { ApiResponse } from '@types/api';

export interface UpdateProfileData {
  email?: string;
  displayName?: string;
  currentPassword: string;
}

export interface ChangePasswordData {
  currentPassword: string;
  newPassword: string;
  confirmNewPassword: string;
}

export interface DeleteAccountData {
  password: string;
}

/**
 * Get current authenticated user profile
 * GET /api/users/me
 */
export const getUser = async (): Promise<ApiResponse<User>> => {
  return api.get<User>('/users/me');
};

/**
 * Get user by ID
 * GET /api/users/{id}
 */
export const getUserById = async (id: number): Promise<ApiResponse<User>> => {
  return api.get<User>(`/users/${id}`);
};

/**
 * Update user profile
 * PUT /api/users/{id}
 * Requires current password for verification
 */
export const updateUser = async (
  id: number,
  data: UpdateProfileData
): Promise<ApiResponse<User>> => {
  return api.put<User>(`/users/${id}`, data);
};

/**
 * Change user password
 * POST /api/users/{id}/change-password
 */
export const changePassword = async (
  id: number,
  data: ChangePasswordData
): Promise<ApiResponse<void>> => {
  return api.post<void>(`/users/${id}/change-password`, data);
};

/**
 * Delete user account
 * DELETE /api/users/{id}
 * Requires password confirmation
 */
export const deleteAccount = async (
  id: number,
  data: DeleteAccountData
): Promise<ApiResponse<void>> => {
  return api.delete<void>(`/users/${id}`, { data } as any);
};

export const userApi = {
  getUser,
  getUserById,
  updateUser,
  changePassword,
  deleteAccount,
};

export default userApi;
