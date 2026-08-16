import React from 'react';
import { Modal } from '../common/Modal';
import { JoinRequest } from '../../types';
import { Check, X, User as UserIcon } from 'lucide-react';

interface JoinRequestsModalProps {
  isOpen: boolean;
  onClose: () => void;
  requests: JoinRequest[];
  onApprove: (reqId: string) => void;
  onReject: (reqId: string) => void;
}

export const JoinRequestsModal: React.FC<JoinRequestsModalProps> = ({
  isOpen,
  onClose,
  requests,
  onApprove,
  onReject,
}) => {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Pending Join Requests"
      subtitle="Approve or reject users requesting to join this group."
    >
      {requests.length === 0 ? (
        <p className="text-sm text-slate-400 text-center py-6">No pending join requests.</p>
      ) : (
        <div className="space-y-3 max-h-72 overflow-y-auto pr-1">
          {requests.map((req) => (
            <div
              key={req.id}
              className="flex items-center justify-between p-3 rounded-xl bg-slate-900/60 border border-slate-800"
            >
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center text-slate-300 font-bold text-xs">
                  {req.user?.name ? req.user.name.charAt(0) : <UserIcon className="w-3.5 h-3.5" />}
                </div>
                <div>
                  <span className="block text-xs font-bold text-slate-200">
                    {req.user?.name || req.user_id.substring(0, 8)}
                  </span>
                  <span className="block text-[10px] text-slate-400">
                    Requested {new Date(req.requested_at).toLocaleDateString()}
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => onApprove(req.id)}
                  className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs"
                >
                  <Check className="w-3.5 h-3.5" /> Approve
                </button>

                <button
                  onClick={() => onReject(req.id)}
                  className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-rose-300 font-medium text-xs border border-slate-700"
                >
                  <X className="w-3.5 h-3.5" /> Reject
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </Modal>
  );
};
