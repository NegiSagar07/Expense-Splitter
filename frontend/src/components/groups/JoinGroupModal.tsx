import React, { useState } from 'react';
import { Modal } from '../common/Modal';
import { groupsApi } from '../../api/groupsApi';
import { useToast } from '../../context/ToastContext';
import { UserPlus, Loader2 } from 'lucide-react';

interface JoinGroupModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const JoinGroupModal: React.FC<JoinGroupModalProps> = ({ isOpen, onClose }) => {
  const [groupId, setGroupId] = useState('');
  const [loading, setLoading] = useState(false);
  const { success, error } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!groupId.trim()) return;

    setLoading(true);
    try {
      await groupsApi.submitJoinRequest(groupId.trim());
      success(
        'Join Request Submitted!',
        'An admin of the group will review and approve your request.'
      );
      setGroupId('');
      onClose();
    } catch (err: any) {
      error('Failed to submit join request', err.response?.data?.detail || 'Invalid Group ID');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Join an Existing Group"
      subtitle="Enter the Group UUID provided by your friend or group admin."
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
            Group UUID / Invite Code
          </label>
          <input
            type="text"
            required
            placeholder="e.g. ea3c6682-baec-48ef-94ff-876bc5488a1c"
            value={groupId}
            onChange={(e) => setGroupId(e.target.value)}
            className="w-full px-4 py-2.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 placeholder-slate-400 font-mono text-xs focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 transition-all"
          />
        </div>

        <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2.5 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer"
          >
            Cancel
          </button>

          <button
            type="submit"
            disabled={loading || !groupId.trim()}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-bold text-xs transition-all shadow-md hover:shadow-lg cursor-pointer"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <UserPlus className="w-4 h-4" />}
            <span>Submit Request</span>
          </button>
        </div>
      </form>
    </Modal>
  );
};
