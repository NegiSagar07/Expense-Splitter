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
        <p className="text-sm text-slate-500 text-center py-6">No pending join requests.</p>
      ) : (
        <div className="space-y-3 max-h-72 overflow-y-auto pr-1">
          {requests.map((req) => (
            <div
              key={req.id}
              className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-200"
            >
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-700 font-bold text-xs">
                  {req.user?.name ? req.user.name.charAt(0).toUpperCase() : <UserIcon className="w-3.5 h-3.5" />}
                </div>
                <div>
                  <span className="block text-xs font-bold text-slate-900">
                    {req.user?.name || req.user_id.substring(0, 8)}
                  </span>
                  <span className="block text-[10px] text-slate-500">
                    Requested {new Date(req.requested_at).toLocaleDateString()}
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => onApprove(req.id)}
                  className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-2xs transition-colors cursor-pointer"
                >
                  <Check className="w-3.5 h-3.5" /> Approve
                </button>

                <button
                  onClick={() => onReject(req.id)}
                  className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-white hover:bg-slate-100 text-rose-600 font-semibold text-xs border border-slate-200 transition-colors cursor-pointer"
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
