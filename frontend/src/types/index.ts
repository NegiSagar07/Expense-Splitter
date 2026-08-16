/**
 * frontend/src/types/index.ts
 * Type definitions matching backend SQLAlchemy models and Pydantic schemas.
 */

export type MemberRole = 'super_admin' | 'admin' | 'member';
export type MemberStatus = 'active' | 'left';
export type JoinRequestStatus = 'pending' | 'approved' | 'rejected' | 'expired';
export type AdminRequestStatus = 'pending' | 'approved' | 'rejected';
export type SplitType = 'equal' | 'custom';
export type ShareStatus = 'pending' | 'approved' | 'rejected';

export interface User {
  id: string;
  name: string;
  email: string;
  created_at: string;
}

export interface Group {
  id: string;
  name: string;
  created_by: string;
  created_at: string;
}

export interface Membership {
  id: string;
  group_id: string;
  user_id: string;
  role: MemberRole;
  status: MemberStatus;
  joined_at: string;
  left_at: string | null;
  user?: User;
}

export interface GroupDetail extends Group {
  members: Membership[];
}

export interface JoinRequest {
  id: string;
  group_id: string;
  user_id: string;
  status: JoinRequestStatus;
  requested_at: string;
  resolved_at: string | null;
  resolved_by: string | null;
  user?: User;
}

export interface AdminRequest {
  id: string;
  group_id: string;
  user_id: string;
  status: AdminRequestStatus;
  requested_at: string;
  resolved_at: string | null;
  resolved_by: string | null;
  user?: User;
}

export interface ExpenseShare {
  id: string;
  expense_id: string;
  user_id: string;
  amount: string; // Decimal returned as string from API
  status: ShareStatus;
  responded_at: string | null;
  user?: User;
}

export interface CustomShareInput {
  user_id: string;
  amount: number;
}

export interface Expense {
  id: string;
  group_id: string;
  owner_id: string;
  description: string;
  total_amount: string; // Decimal
  split_type: SplitType;
  is_deleted: boolean;
  owner_locked: boolean;
  created_at: string;
  updated_at: string;
  owner?: User;
  shares: ExpenseShare[];
}

export interface NetDebt {
  debtor_id: string;
  debtor?: User;
  creditor_id: string;
  creditor?: User;
  amount: string; // Decimal
}

export interface UserBalanceSummary {
  user_id: string;
  user?: User;
  total_paid: string;
  total_owed: string;
  net_balance: string;
}

export interface GroupBalanceResponse {
  group_id: string;
  user_balances: UserBalanceSummary[];
  net_debts: NetDebt[];
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}
