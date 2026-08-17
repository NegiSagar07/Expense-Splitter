import React from 'react';
import { MemberRole, ShareStatus, JoinRequestStatus } from '../../types';
import { Crown, Shield, User as UserIcon, CheckCircle2, Clock, XCircle } from 'lucide-react';

interface RoleBadgeProps {
  role: MemberRole;
}

export const RoleBadge: React.FC<RoleBadgeProps> = ({ role }) => {
  if (role === 'super_admin') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-amber-50 text-amber-700 border border-amber-200 shadow-2xs">
        <Crown className="w-3 h-3 text-amber-600" />
        Super Admin
      </span>
    );
  }
  if (role === 'admin') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200 shadow-2xs">
        <Shield className="w-3 h-3 text-indigo-600" />
        Admin
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-slate-100 text-slate-700 border border-slate-200">
      <UserIcon className="w-3 h-3 text-slate-500" />
      Member
    </span>
  );
};

interface StatusBadgeProps {
  status: ShareStatus | JoinRequestStatus;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  if (status === 'approved') {
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
        <CheckCircle2 className="w-3 h-3 text-emerald-600" />
        Approved
      </span>
    );
  }
  if (status === 'pending') {
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-amber-50 text-amber-700 border border-amber-200">
        <Clock className="w-3 h-3 text-amber-600 animate-pulse" />
        Pending
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-rose-50 text-rose-700 border border-rose-200">
      <XCircle className="w-3 h-3 text-rose-600" />
      {status === 'rejected' ? 'Rejected' : 'Expired'}
    </span>
  );
};
