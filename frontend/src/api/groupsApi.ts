import { axiosClient } from './axiosClient';
import { Group, GroupBalanceResponse, GroupDetail, JoinRequest, AdminRequest, Membership } from '../types';

export const groupsApi = {
  createGroup: async (name: string): Promise<Group> => {
    const res = await axiosClient.post<Group>('/groups', { name });
    return res.data;
  },

  listGroups: async (): Promise<Group[]> => {
    const res = await axiosClient.get<Group[]>('/groups');
    return res.data;
  },

  getGroupDetail: async (groupId: string): Promise<GroupDetail> => {
    const res = await axiosClient.get<GroupDetail>(`/groups/${groupId}`);
    return res.data;
  },

  submitJoinRequest: async (groupId: string): Promise<JoinRequest> => {
    const res = await axiosClient.post<JoinRequest>(`/groups/${groupId}/join-requests`);
    return res.data;
  },

  listJoinRequests: async (groupId: string): Promise<JoinRequest[]> => {
    const res = await axiosClient.get<JoinRequest[]>(`/groups/${groupId}/join-requests`);
    return res.data;
  },

  approveJoinRequest: async (groupId: string, reqId: string): Promise<JoinRequest> => {
    const res = await axiosClient.post<JoinRequest>(`/groups/${groupId}/join-requests/${reqId}/approve`);
    return res.data;
  },

  rejectJoinRequest: async (groupId: string, reqId: string): Promise<JoinRequest> => {
    const res = await axiosClient.post<JoinRequest>(`/groups/${groupId}/join-requests/${reqId}/reject`);
    return res.data;
  },

  submitAdminRequest: async (groupId: string): Promise<AdminRequest> => {
    const res = await axiosClient.post<AdminRequest>(`/groups/${groupId}/admin-requests`);
    return res.data;
  },

  listAdminRequests: async (groupId: string): Promise<AdminRequest[]> => {
    const res = await axiosClient.get<AdminRequest[]>(`/groups/${groupId}/admin-requests`);
    return res.data;
  },

  approveAdminRequest: async (groupId: string, reqId: string): Promise<AdminRequest> => {
    const res = await axiosClient.post<AdminRequest>(`/groups/${groupId}/admin-requests/${reqId}/approve`);
    return res.data;
  },

  rejectAdminRequest: async (groupId: string, reqId: string): Promise<AdminRequest> => {
    const res = await axiosClient.post<AdminRequest>(`/groups/${groupId}/admin-requests/${reqId}/reject`);
    return res.data;
  },

  promoteMember: async (groupId: string, targetUserId: string): Promise<Membership> => {
    const res = await axiosClient.post<Membership>(`/groups/${groupId}/members/${targetUserId}/promote`);
    return res.data;
  },

  removeMember: async (groupId: string, targetUserId: string): Promise<Membership> => {
    const res = await axiosClient.post<Membership>(`/groups/${groupId}/members/${targetUserId}/remove`);
    return res.data;
  },

  leaveGroup: async (groupId: string, successorId?: string): Promise<Membership> => {
    const res = await axiosClient.post<Membership>(`/groups/${groupId}/leave`, {
      successor_id: successorId || null,
    });
    return res.data;
  },

  getBalances: async (groupId: string): Promise<GroupBalanceResponse> => {
    const res = await axiosClient.get<GroupBalanceResponse>(`/groups/${groupId}/balances`);
    return res.data;
  },
};
