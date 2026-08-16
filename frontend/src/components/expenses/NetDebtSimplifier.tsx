import React from 'react';
import { GroupBalanceResponse } from '../../types';
import { ArrowRight, Sparkles, CheckCircle2, User as UserIcon } from 'lucide-react';
import confetti from 'canvas-confetti';
import { useToast } from '../../context/ToastContext';

interface NetDebtSimplifierProps {
  balanceData: GroupBalanceResponse;
}

export const NetDebtSimplifier: React.FC<NetDebtSimplifierProps> = ({ balanceData }) => {
  const { success } = useToast();

  const handleCelebrateSettle = (debtorName: string, creditorName: string, amount: string) => {
    confetti({
      particleCount: 70,
      spread: 60,
      origin: { y: 0.7 },
    });
    success('Debt Settled!', `${debtorName} paid ₹${amount} to ${creditorName}.`);
  };

  const { net_debts, user_balances } = balanceData;

  return (
    <div className="space-y-6">
      {/* Debt Simplification Summary Header */}
      <div className="glass-panel rounded-2xl p-5 relative overflow-hidden">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-100">Simplified Net Debts (FR16)</h3>
              <p className="text-xs text-slate-400">
                Minimum transactions required to settle all group obligations.
              </p>
            </div>
          </div>
        </div>

        {/* Net Debt Cards List */}
        {net_debts.length === 0 ? (
          <div className="p-8 text-center rounded-xl bg-slate-900/40 border border-slate-800">
            <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto mb-2 opacity-80" />
            <h4 className="text-sm font-bold text-slate-200">All Settled Up!</h4>
            <p className="text-xs text-slate-400 mt-1">No pending debts found in this group.</p>
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
                  className="flex items-center justify-between p-4 rounded-xl glass-panel-hover bg-slate-900/60 border border-slate-800"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-full bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-rose-300 font-bold text-xs">
                      {dName.charAt(0)}
                    </div>

                    <ArrowRight className="w-4 h-4 text-slate-500 shrink-0" />

                    <div className="w-9 h-9 rounded-full bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-300 font-bold text-xs">
                      {cName.charAt(0)}
                    </div>

                    <div className="text-left">
                      <p className="text-xs font-semibold text-slate-200">
                        <span className="text-rose-400 font-bold">{dName}</span> owes{' '}
                        <span className="text-emerald-400 font-bold">{cName}</span>
                      </p>
                      <p className="text-[11px] text-slate-400">Direct Settlement</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <span className="text-lg font-bold font-mono-amount text-amber-400">
                      ₹{amtStr}
                    </span>

                    <button
                      onClick={() => handleCelebrateSettle(dName, cName, amtStr)}
                      className="px-3 py-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 font-semibold text-xs border border-emerald-500/30 transition-all active:scale-95"
                    >
                      Settle
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Member Balance Breakdown Grid */}
      <div className="glass-panel rounded-2xl p-5">
        <h4 className="text-sm font-bold text-slate-200 mb-3 uppercase tracking-wider">
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
                className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between"
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 font-bold text-sm">
                    {ub.user?.name ? ub.user.name.charAt(0) : <UserIcon className="w-4 h-4" />}
                  </div>
                  <div>
                    <span className="block text-xs font-bold text-slate-200">
                      {ub.user?.name || 'Member'}
                    </span>
                    <span className="block text-[10px] text-slate-400 font-mono-amount">
                      Paid ₹{parseFloat(ub.total_paid).toFixed(2)} • Owed ₹
                      {parseFloat(ub.total_owed).toFixed(2)}
                    </span>
                  </div>
                </div>

                <div className="text-right">
                  <span
                    className={`block text-base font-bold font-mono-amount ${
                      isCreditor
                        ? 'text-emerald-400'
                        : isDebtor
                        ? 'text-rose-400'
                        : 'text-slate-400'
                    }`}
                  >
                    {isCreditor ? '+' : ''}₹{net.toFixed(2)}
                  </span>
                  <span className="block text-[10px] uppercase font-semibold text-slate-500">
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
