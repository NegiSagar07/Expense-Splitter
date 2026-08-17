import React, { useState } from 'react';
import { GroupBalanceResponse, NetDebt } from '../../types';
import { groupsApi } from '../../api/groupsApi';
import { ArrowRight, Sparkles, CheckCircle2, User as UserIcon, Loader2 } from 'lucide-react';
import confetti from 'canvas-confetti';
import { useToast } from '../../context/ToastContext';

interface NetDebtSimplifierProps {
  groupId: string;
  balanceData: GroupBalanceResponse;
  onDebtSettled: () => void;
}

export const NetDebtSimplifier: React.FC<NetDebtSimplifierProps> = ({
  groupId,
  balanceData,
  onDebtSettled,
}) => {
  const { success, error } = useToast();
  const [settlingId, setSettlingId] = useState<string | null>(null);

  const handleSettle = async (debt: NetDebt) => {
    const dName = debt.debtor?.name || 'Member';
    const cName = debt.creditor?.name || 'Member';
    const amtNum = parseFloat(debt.amount);
    const key = `${debt.debtor_id}-${debt.creditor_id}`;

    setSettlingId(key);
    try {
      await groupsApi.settleDebt(groupId, debt.debtor_id, debt.creditor_id, amtNum);
      confetti({
        particleCount: 80,
        spread: 70,
        origin: { y: 0.7 },
      });
      success('Debt Settled!', `${dName} paid ₹${amtNum.toFixed(2)} to ${cName}.`);
      onDebtSettled();
    } catch (err: any) {
      error('Settlement Failed', err.response?.data?.detail || 'Could not record settlement.');
    } finally {
      setSettlingId(null);
    }
  };

  const { net_debts, user_balances } = balanceData;

  return (
    <div className="space-y-6">
      {/* Debt Simplification Summary Header */}
      <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600 shadow-2xs">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">Simplified Net Debts</h3>
              <p className="text-xs text-slate-500">
                Minimum transactions required to settle all group obligations.
              </p>
            </div>
          </div>
        </div>

        {/* Net Debt Cards List */}
        {net_debts.length === 0 ? (
          <div className="p-8 text-center rounded-xl bg-slate-50 border border-slate-200/80">
            <CheckCircle2 className="w-10 h-10 text-emerald-600 mx-auto mb-2" />
            <h4 className="text-sm font-bold text-slate-900">All Settled Up!</h4>
            <p className="text-xs text-slate-500 mt-1">No pending debts found in this group.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {net_debts.map((debt, idx) => {
              const dName = debt.debtor?.name || 'Member';
              const cName = debt.creditor?.name || 'Member';
              const amtStr = parseFloat(debt.amount).toFixed(2);

              return (
                <div
                  key={idx}
                  className="flex items-center justify-between p-4 rounded-xl bg-slate-50 border border-slate-200 hover:border-indigo-200 transition-all"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-full bg-rose-50 border border-rose-200 flex items-center justify-center text-rose-700 font-bold text-xs">
                      {dName.charAt(0).toUpperCase()}
                    </div>

                    <ArrowRight className="w-4 h-4 text-slate-400 shrink-0" />

                    <div className="w-9 h-9 rounded-full bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700 font-bold text-xs">
                      {cName.charAt(0).toUpperCase()}
                    </div>

                    <div className="text-left">
                      <p className="text-xs font-semibold text-slate-900">
                        <span className="text-rose-600 font-bold">{dName}</span> owes{' '}
                        <span className="text-emerald-700 font-bold">{cName}</span>
                      </p>
                      <p className="text-[11px] text-slate-500">Direct Settlement</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <span className="text-lg font-extrabold font-mono-amount text-amber-600">
                      ₹{amtStr}
                    </span>

                    <button
                      onClick={() => handleSettle(debt)}
                      disabled={settlingId === `${debt.debtor_id}-${debt.creditor_id}`}
                      className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white font-bold text-xs shadow-2xs transition-all active:scale-95 cursor-pointer"
                    >
                      {settlingId === `${debt.debtor_id}-${debt.creditor_id}` ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <span>Settle Debt</span>
                      )}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Member Balance Breakdown Grid */}
      <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs">
        <h4 className="text-sm font-bold text-slate-800 mb-3 uppercase tracking-wider">
          Individual Balance Totals (Approved Shares Only)
        </h4>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {user_balances.map((ub) => {
            const net = parseFloat(ub.net_balance);
            const isCreditor = net > 0;
            const isDebtor = net < 0;

            return (
              <div
                key={ub.user_id}
                className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between"
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-700 font-bold text-sm">
                    {ub.user?.name ? ub.user.name.charAt(0).toUpperCase() : <UserIcon className="w-4 h-4" />}
                  </div>
                  <div>
                    <span className="block text-xs font-bold text-slate-900">
                      {ub.user?.name || 'Member'}
                    </span>
                    <span className="block text-[11px] text-slate-500 font-mono-amount">
                      Paid ₹{parseFloat(ub.total_paid).toFixed(2)} • Owed ₹
                      {parseFloat(ub.total_owed).toFixed(2)}
                    </span>
                  </div>
                </div>

                <div className="text-right">
                  <span
                    className={`block text-base font-extrabold font-mono-amount ${
                      isCreditor
                        ? 'text-emerald-700'
                        : isDebtor
                        ? 'text-rose-600'
                        : 'text-slate-500'
                    }`}
                  >
                    {isCreditor ? '+' : ''}₹{net.toFixed(2)}
                  </span>
                  <span className="block text-[10px] uppercase font-bold text-slate-400">
                    {isCreditor ? 'Gets Back' : isDebtor ? 'Owes Total' : 'Settled'}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
