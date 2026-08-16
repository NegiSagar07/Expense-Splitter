import React, { useState } from 'react';
import { Modal } from '../common/Modal';
import { Membership, SplitType, CustomShareInput } from '../../types';
import { expensesApi } from '../../api/expensesApi';
import { useToast } from '../../context/ToastContext';
import { Receipt, Loader2, Check, Users, Calculator } from 'lucide-react';

interface CreateExpenseModalProps {
  isOpen: boolean;
  onClose: () => void;
  groupId: string;
  members: Membership[];
  onExpenseCreated: () => void;
}

export const CreateExpenseModal: React.FC<CreateExpenseModalProps> = ({
  isOpen,
  onClose,
  groupId,
  members,
  onExpenseCreated,
}) => {
  const [description, setDescription] = useState('');
  const [totalAmount, setTotalAmount] = useState('');
  const [splitType, setSplitType] = useState<SplitType>('equal');
  const [selectedUserIds, setSelectedUserIds] = useState<string[]>(
    members.map((m) => m.user_id)
  );
  const [customShares, setCustomShares] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const { success, error } = useToast();

  const toggleUser = (userId: string) => {
    if (selectedUserIds.includes(userId)) {
      if (selectedUserIds.length === 1) return; // Keep at least 1
      setSelectedUserIds((prev) => prev.filter((id) => id !== userId));
    } else {
      setSelectedUserIds((prev) => [...prev, userId]);
    }
  };

  const handleCustomShareChange = (userId: string, val: string) => {
    setCustomShares((prev) => ({ ...prev, [userId]: val }));
  };

  const parsedTotal = parseFloat(totalAmount) || 0;
  const equalPerPerson =
    splitType === 'equal' && selectedUserIds.length > 0
      ? (parsedTotal / selectedUserIds.length).toFixed(2)
      : '0.00';

  const customTotalSum = Object.values(customShares).reduce(
    (sum, val) => sum + (parseFloat(val) || 0),
    0
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!description.trim() || parsedTotal <= 0) return;

    setLoading(true);

    try {
      if (splitType === 'equal') {
        await expensesApi.createExpense(groupId, {
          description: description.trim(),
          total_amount: parsedTotal,
          split_type: 'equal',
          participant_ids: selectedUserIds,
        });
      } else {
        // Custom split payload
        const formattedShares: CustomShareInput[] = members.map((m) => ({
          user_id: m.user_id,
          amount: parseFloat(customShares[m.user_id] || '0') || 0,
        }));

        const totalCustom = formattedShares.reduce((s, x) => s + x.amount, 0);
        if (Math.abs(totalCustom - parsedTotal) > 0.01) {
          error(
            'Custom shares error',
            `Sum of custom shares (₹${totalCustom.toFixed(
              2
            )}) must equal total amount (₹${parsedTotal.toFixed(2)})`
          );
          setLoading(false);
          return;
        }

        await expensesApi.createExpense(groupId, {
          description: description.trim(),
          total_amount: parsedTotal,
          split_type: 'custom',
          custom_shares: formattedShares,
        });
      }

      success('Expense Logged!', `₹${parsedTotal} logged for "${description}".`);
      onExpenseCreated();
      onClose();
    } catch (err: any) {
      error('Failed to log expense', err.response?.data?.detail || 'Unexpected error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Log New Group Expense"
      subtitle="Select split type and participants."
      maxWidth="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Description & Amount */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="sm:col-span-2">
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1">
              Description
            </label>
            <input
              type="text"
              required
              placeholder="e.g. Dinner, Fuel, Grocery"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900/80 border border-slate-700 text-slate-100 text-sm focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1">
              Total Amount (₹)
            </label>
            <input
              type="number"
              step="0.01"
              required
              min="0.01"
              placeholder="0.00"
              value={totalAmount}
              onChange={(e) => setTotalAmount(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900/80 border border-slate-700 text-slate-100 font-mono-amount font-bold text-sm focus:outline-none focus:border-emerald-500"
            />
          </div>
        </div>

        {/* Split Type Selector */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
            Split Strategy
          </label>
          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => setSplitType('equal')}
              className={`flex items-center gap-3 p-3 rounded-xl border text-left transition-all ${
                splitType === 'equal'
                  ? 'bg-emerald-500/10 border-emerald-500 text-emerald-300'
                  : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700'
              }`}
            >
              <Users className="w-5 h-5 shrink-0" />
              <div>
                <span className="block text-xs font-bold text-slate-100">Equal Split</span>
                <span className="block text-[11px] text-slate-400">Divide total evenly</span>
              </div>
            </button>

            <button
              type="button"
              onClick={() => setSplitType('custom')}
              className={`flex items-center gap-3 p-3 rounded-xl border text-left transition-all ${
                splitType === 'custom'
                  ? 'bg-emerald-500/10 border-emerald-500 text-emerald-300'
                  : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700'
              }`}
            >
              <Calculator className="w-5 h-5 shrink-0" />
              <div>
                <span className="block text-xs font-bold text-slate-100">Custom Split</span>
                <span className="block text-[11px] text-slate-400">Specific per-person share</span>
              </div>
            </button>
          </div>
        </div>

        {/* EQUAL Split Participant Selector */}
        {splitType === 'equal' && (
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
                Included Members ({selectedUserIds.length})
              </label>
              {parsedTotal > 0 && (
                <span className="text-xs text-emerald-400 font-mono-amount font-semibold">
                  ~ ₹{equalPerPerson} / person
                </span>
              )}
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {members.map((m) => {
                const isSelected = selectedUserIds.includes(m.user_id);
                return (
                  <button
                    key={m.user_id}
                    type="button"
                    onClick={() => toggleUser(m.user_id)}
                    className={`flex items-center justify-between p-2.5 rounded-xl text-xs border transition-all ${
                      isSelected
                        ? 'bg-slate-800 border-emerald-500/60 text-slate-100'
                        : 'bg-slate-900/40 border-slate-800/80 text-slate-500'
                    }`}
                  >
                    <span className="truncate">{m.user?.name || 'Member'}</span>
                    {isSelected && <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0" />}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* CUSTOM Split Input Table */}
        {splitType === 'custom' && (
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
                Custom Amount Per Member
              </label>
              <span
                className={`text-xs font-mono-amount font-semibold ${
                  Math.abs(customTotalSum - parsedTotal) < 0.01
                    ? 'text-emerald-400'
                    : 'text-amber-400'
                }`}
              >
                Sum: ₹{customTotalSum.toFixed(2)} / ₹{parsedTotal.toFixed(2)}
              </span>
            </div>

            <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
              {members.map((m) => (
                <div
                  key={m.user_id}
                  className="flex items-center justify-between gap-3 p-2 rounded-xl bg-slate-900/60 border border-slate-800"
                >
                  <span className="text-xs font-medium text-slate-200 truncate">
                    {m.user?.name || 'Member'}
                  </span>

                  <input
                    type="number"
                    step="0.01"
                    placeholder="0.00"
                    value={customShares[m.user_id] || ''}
                    onChange={(e) => handleCustomShareChange(m.user_id, e.target.value)}
                    className="w-28 px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-xs font-mono-amount text-slate-100 focus:outline-none focus:border-emerald-500"
                  />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Modal Actions */}
        <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-800"
          >
            Cancel
          </button>

          <button
            type="submit"
            disabled={loading || parsedTotal <= 0 || !description.trim()}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-slate-950 font-bold text-xs shadow-md shadow-emerald-500/20"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Receipt className="w-4 h-4" />}
            <span>Log Expense</span>
          </button>
        </div>
      </form>
    </Modal>
  );
};
