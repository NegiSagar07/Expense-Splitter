import React from 'react';
import { Expense } from '../../types';
import { StatusBadge } from '../common/Badge';
import { useAuth } from '../../context/AuthContext';
import { Receipt, Check, Trash2, Edit2, Lock, User as UserIcon } from 'lucide-react';

interface ExpenseCardProps {
  expense: Expense;
  onRespondShare: (expenseId: string, approve: boolean) => void;
  onDeleteExpense: (expenseId: string) => void;
  onEditExpense?: (expense: Expense) => void;
}

export const ExpenseCard: React.FC<ExpenseCardProps> = ({
  expense,
  onRespondShare,
  onDeleteExpense,
  onEditExpense,
}) => {
  const { user } = useAuth();
  const isOwner = user?.id === expense.owner_id;

  // Find caller's share status
  const myShare = expense.shares.find((s) => s.user_id === user?.id);

  const formattedDate = new Date(expense.created_at).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div
      className={`bg-white border border-slate-200/90 rounded-2xl p-5 relative overflow-hidden transition-all shadow-xs hover:shadow-md ${
        expense.is_deleted ? 'opacity-60 grayscale border-slate-300' : ''
      }`}
    >
      {/* Deleted / Locked badge */}
      {expense.is_deleted && (
        <div className="absolute top-0 right-0 bg-rose-100 text-rose-700 text-[10px] font-bold uppercase tracking-wider px-3 py-1 rounded-bl-xl border-l border-b border-rose-200">
          Soft Deleted (History Preserved)
        </div>
      )}

      {expense.owner_locked && !expense.is_deleted && (
        <div className="absolute top-0 right-0 bg-amber-100 text-amber-800 text-[10px] font-bold uppercase tracking-wider px-3 py-1 rounded-bl-xl border-l border-b border-amber-200 flex items-center gap-1">
          <Lock className="w-3 h-3 text-amber-700" /> Owner Left (Locked)
        </div>
      )}

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
        <div className="flex items-start gap-3.5">
          <div className="w-11 h-11 rounded-xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600 shrink-0 mt-0.5 shadow-2xs">
            <Receipt className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h4 className="text-base font-bold text-slate-900">{expense.description}</h4>
              <span className="px-2 py-0.5 rounded-full text-[10px] uppercase font-bold bg-slate-100 text-slate-600 border border-slate-200">
                {expense.split_type} split
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Paid by <span className="text-slate-900 font-semibold">{expense.owner?.name || 'Owner'}</span> • {formattedDate}
            </p>
          </div>
        </div>

        {/* Total Amount & Owner Actions */}
        <div className="flex items-center justify-between md:justify-end gap-4 shrink-0">
          <div className="text-left md:text-right">
            <span className="block text-[10px] uppercase font-bold tracking-wider text-slate-400">Total Amount</span>
            <span className="text-xl font-extrabold font-mono-amount text-emerald-600">
              ₹{parseFloat(expense.total_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </span>
          </div>

          {/* Owner action buttons */}
          {isOwner && !expense.is_deleted && !expense.owner_locked && (
            <div className="flex items-center gap-1 border-l border-slate-200 pl-3">
              {onEditExpense && (
                <button
                  onClick={() => onEditExpense(expense)}
                  title="Edit Expense"
                  className="p-2 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-xl transition-colors cursor-pointer"
                >
                  <Edit2 className="w-4 h-4" />
                </button>
              )}
              <button
                onClick={() => onDeleteExpense(expense.id)}
                title="Soft Delete Expense"
                className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-xl transition-colors cursor-pointer"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Participant Shares Breakdown */}
      <div className="pt-3 border-t border-slate-100">
        <span className="block text-[11px] font-bold text-slate-500 mb-2 uppercase tracking-wider">
          Participant Shares ({expense.shares.length})
        </span>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
          {expense.shares.map((share) => (
            <div
              key={share.id}
              className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 border border-slate-200 text-xs"
            >
              <div className="flex items-center gap-2 truncate">
                <div className="w-6 h-6 rounded-full bg-indigo-50 border border-indigo-100 flex items-center justify-center text-[10px] font-bold text-indigo-700">
                  {share.user?.name ? share.user.name.charAt(0).toUpperCase() : <UserIcon className="w-3 h-3" />}
                </div>
                <span className="truncate font-semibold text-slate-800">
                  {share.user_id === user?.id ? 'You' : share.user?.name || 'Member'}
                </span>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <span className="font-mono-amount font-bold text-slate-900">
                  ₹{parseFloat(share.amount).toFixed(2)}
                </span>
                <StatusBadge status={share.status} />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* My Share Action Bar */}
      {myShare && myShare.status === 'pending' && !expense.is_deleted && (
        <div className="mt-4 p-3 rounded-xl bg-amber-50 border border-amber-200 flex items-center justify-between">
          <span className="text-xs text-amber-900 font-semibold">
            Your share of ₹{parseFloat(myShare.amount).toFixed(2)} is pending approval.
          </span>

          <div className="flex items-center gap-2">
            <button
              onClick={() => onRespondShare(expense.id, true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs transition-all shadow-xs cursor-pointer"
            >
              <Check className="w-3.5 h-3.5" />
              <span>Approve</span>
            </button>

            <button
              onClick={() => onRespondShare(expense.id, false)}
              className="px-3 py-1.5 rounded-lg bg-white hover:bg-slate-100 text-rose-700 font-semibold text-xs border border-slate-200 transition-colors cursor-pointer"
            >
              Reject
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
