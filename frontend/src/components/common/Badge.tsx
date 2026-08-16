import React from 'react';
import { MemberRole, ShareStatus, JoinRequestStatus } from '../../types';
import { Crown, Shield, User as UserIcon, CheckCircle2, Clock, XCircle } from 'lucide-react';

interface RoleBadgeProps {
  role: MemberRole;
}

export const RoleBadge: React.FC<RoleBadgeProps> = ({ role }) => {
  if (role === 'super_admin') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-amber-500/10 text-amber-300 border border-amber-500/30">
        <Crown className="w-3 h-3 text-amber-400" />
        Super Admin
      </span>
    );
  }
  if (role === 'admin') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-sky-500/10 text-sky-300 border border-sky-500/30">
        <Shield className="w-3 h-3 text-sky-400" />
        Admin
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-slate-800 text-slate-300 border border-slate-700">
      <UserIcon className="w-3 h-3 text-slate-400" />
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
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
        <CheckCircle2 className="w-3 h-3" />
        Approved
      </span>
    );
  }
  if (status === 'pending') {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
        <Clock className="w-3 h-3 animate-pulse" />
        Pending
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
      <XCircle className="w-3 h-3" />
      {status === 'rejected' ? 'Rejected' : 'Expired'}
    </span>
  );
};
