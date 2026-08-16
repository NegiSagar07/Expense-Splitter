import React from 'react';
import { Membership, MemberRole } from '../../types';
import { RoleBadge } from '../common/Badge';
import { useAuth } from '../../context/AuthContext';
import { Crown, Shield, UserMinus, User as UserIcon } from 'lucide-react';

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
        <h4 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
          Group Members ({members.length})
        </h4>

        <button
          onClick={onLeaveGroup}
          className="px-3 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 font-semibold text-xs border border-rose-500/30 transition-colors"
        >
          Leave Group
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
            !(isTargetAdmin && myRole !== 'super_admin'); // Admin cannot remove Admin (FR-A3/A4)

          return (
            <div
              key={mem.id}
              className="flex items-center justify-between p-3.5 rounded-xl glass-panel bg-slate-900/60 border border-slate-800"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-200 font-bold text-sm">
                  {mem.user?.name ? mem.user.name.charAt(0) : <UserIcon className="w-4 h-4" />}
                </div>

                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-slate-200">
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
                    className="p-2 text-slate-400 hover:text-sky-400 hover:bg-slate-800/80 rounded-lg transition-colors"
                  >
                    <Shield className="w-4 h-4" />
                  </button>
                )}

                {canRemove && (
                  <button
                    onClick={() => onRemoveMember(mem.user_id)}
                    title="Remove Member"
                    className="p-2 text-slate-400 hover:text-rose-400 hover:bg-slate-800/80 rounded-lg transition-colors"
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
