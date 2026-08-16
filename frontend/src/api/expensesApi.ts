import { axiosClient } from './axiosClient';
import { Expense, ExpenseShare, CustomShareInput, SplitType } from '../types';

export interface CreateExpensePayload {
  description: string;
  total_amount: number;
  split_type: SplitType;
  participant_ids?: string[];
  custom_shares?: CustomShareInput[];
}

export interface UpdateExpensePayload {
  description?: string;
  total_amount?: number;
  split_type?: SplitType;
  participant_ids?: string[];
  custom_shares?: CustomShareInput[];
}

export const expensesApi = {
  createExpense: async (groupId: string, payload: CreateExpensePayload): Promise<Expense> => {
    const res = await axiosClient.post<Expense>(`/groups/${groupId}/expenses`, payload);
    return res.data;
  },

  listGroupExpenses: async (groupId: string, includeDeleted = false): Promise<Expense[]> => {
    const res = await axiosClient.get<Expense[]>(`/groups/${groupId}/expenses`, {
      params: { include_deleted: includeDeleted },
    });
    return res.data;
  },

  getExpense: async (expenseId: string): Promise<Expense> => {
    const res = await axiosClient.get<Expense>(`/expenses/${expenseId}`);
    return res.data;
  },

  updateExpense: async (expenseId: string, payload: UpdateExpensePayload): Promise<Expense> => {
    const res = await axiosClient.patch<Expense>(`/expenses/${expenseId}`, payload);
    return res.data;
  },

  deleteExpense: async (expenseId: string): Promise<Expense> => {
    const res = await axiosClient.delete<Expense>(`/expenses/${expenseId}`);
    return res.data;
  },

  respondShare: async (expenseId: string, approve: boolean): Promise<ExpenseShare> => {
    const res = await axiosClient.post<ExpenseShare>(`/expenses/${expenseId}/shares/respond`, {
      approve,
    });
    return res.data;
  },
};
