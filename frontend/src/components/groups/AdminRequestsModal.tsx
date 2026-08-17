import React from 'react';
import { Modal } from '../common/Modal';
import { AdminRequest } from '../../types';
import { Check, X, Shield } from 'lucide-react';

interface AdminRequestsModalProps {
  isOpen: boolean;
  onClose: () => void;
  requests: AdminRequest[];
  onApprove: (reqId: string) => void;
  onReject: (reqId: string) => void;
}

export const AdminRequestsModal: React.FC<AdminRequestsModalProps> = ({
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
      title="Admin Promotion Requests"
      subtitle="Approve members requesting Admin role."
    >
      {requests.length === 0 ? (
        <p className="text-sm text-slate-500 text-center py-6">No pending admin requests.</p>
      ) : (
        <div className="space-y-3 max-h-72 overflow-y-auto pr-1">
          {requests.map((req) => (
            <div
              key={req.id}
              className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-200"
            >
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold text-xs">
                  <Shield className="w-4 h-4" />
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
                  className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs shadow-2xs transition-colors cursor-pointer"
                >
                  <Check className="w-3.5 h-3.5" /> Approve Admin
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
