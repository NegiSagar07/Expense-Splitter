import { axiosClient } from './axiosClient';
import { User, TokenResponse } from '../types';

export const authApi = {
  register: async (name: string, email: string, password: string): Promise<User> => {
    const res = await axiosClient.post<User>('/auth/register', { name, email, password });
    return res.data;
  },

  login: async (email: string, password: string): Promise<TokenResponse> => {
    const res = await axiosClient.post<TokenResponse>('/auth/login', { email, password });
    return res.data;
  },

  getMe: async (): Promise<User> => {
    const res = await axiosClient.get<User>('/auth/me');
    return res.data;
  },
};
