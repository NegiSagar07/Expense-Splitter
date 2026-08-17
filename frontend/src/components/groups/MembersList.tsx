import React from 'react';
import { Membership, MemberRole } from '../../types';
import { RoleBadge } from '../common/Badge';
import { useAuth } from '../../context/AuthContext';
import { Shield, UserMinus, User as UserIcon, LogOut } from 'lucide-react';

interface MembersListProps {
  members: Membership[];
  myRole: MemberRole;
  onPromoteMember: (userId: string) => void;
  onRemoveMember: (userId: string) => void;
  onLeaveGroup: () => void;
}

export const MembersList: React.FC<MembersListProps> = ({
  members,
  myRole,
  onPromoteMember,
  onRemoveMember,
  onLeaveGroup,
}) => {
  const { user } = useAuth();
  const isAdminOrSuper = myRole === 'admin' || myRole === 'super_admin';

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-bold text-slate-800 uppercase tracking-wider">
          Group Members ({members.length})
        </h4>

        <button
          onClick={onLeaveGroup}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-700 font-semibold text-xs border border-rose-200 transition-colors cursor-pointer"
        >
          <LogOut className="w-3.5 h-3.5" />
          <span>Leave Group</span>
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {members.map((mem) => {
          const isMe = mem.user_id === user?.id;
          const isTargetSuper = mem.role === 'super_admin';
          const isTargetAdmin = mem.role === 'admin';

          const canPromote = isAdminOrSuper && mem.role === 'member';
          const canRemove =
            isAdminOrSuper &&
            !isMe &&
            !isTargetSuper &&
            !(isTargetAdmin && myRole !== 'super_admin');

          return (
            <div
              key={mem.id}
              className="flex items-center justify-between p-3.5 rounded-2xl bg-white border border-slate-200/80 shadow-xs hover:border-slate-300 transition-all"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-700 font-bold text-sm shadow-2xs">
                  {mem.user?.name ? mem.user.name.charAt(0).toUpperCase() : <UserIcon className="w-4 h-4" />}
                </div>

                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-slate-900">
                      {mem.user?.name || 'Member'} {isMe && '(You)'}
                    </span>
                  </div>
                  <div className="mt-1">
                    <RoleBadge role={mem.role} />
                  </div>
                </div>
              </div>

              {/* Action buttons */}
              <div className="flex items-center gap-1">
                {canPromote && (
                  <button
                    onClick={() => onPromoteMember(mem.user_id)}
                    title="Promote to Admin"
                    className="p-2 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-xl transition-colors cursor-pointer"
                  >
                    <Shield className="w-4 h-4" />
                  </button>
                )}

                {canRemove && (
                  <button
                    onClick={() => onRemoveMember(mem.user_id)}
                    title="Remove Member"
                    className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-xl transition-colors cursor-pointer"
                  >
                    <UserMinus className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
