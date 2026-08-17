import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Navbar } from '../components/common/Navbar';
import { ExpenseCard } from '../components/expenses/ExpenseCard';
import { CreateExpenseModal } from '../components/expenses/CreateExpenseModal';
import { NetDebtSimplifier } from '../components/expenses/NetDebtSimplifier';
import { MembersList } from '../components/groups/MembersList';
import { JoinRequestsModal } from '../components/groups/JoinRequestsModal';
import { AdminRequestsModal } from '../components/groups/AdminRequestsModal';
import { groupsApi } from '../api/groupsApi';
import { expensesApi } from '../api/expensesApi';
import { GroupDetail, Expense, GroupBalanceResponse, JoinRequest, AdminRequest, MemberRole } from '../types';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import {
  ArrowLeft,
  Receipt,
  Sparkles,
  Users,
  Copy,
  PlusCircle,
  Shield,
  UserPlus,
  Loader2,
} from 'lucide-react';

type TabType = 'expenses' | 'balances' | 'members';

export const GroupDetailPage: React.FC = () => {
  const { groupId } = useParams<{ groupId: string }>();
  const { user } = useAuth();
  const { success, error } = useToast();
  const navigate = useNavigate();

  const [group, setGroup] = useState<GroupDetail | null>(null);
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [balances, setBalances] = useState<GroupBalanceResponse | null>(null);
  const [joinRequests, setJoinRequests] = useState<JoinRequest[]>([]);
  const [adminRequests, setAdminRequests] = useState<AdminRequest[]>([]);

  const [activeTab, setActiveTab] = useState<TabType>('expenses');
  const [includeDeleted, setIncludeDeleted] = useState(false);
  const [loading, setLoading] = useState(true);

  // Modal states
  const [isCreateExpenseOpen, setIsCreateExpenseOpen] = useState(false);
  const [isJoinReqModalOpen, setIsJoinReqModalOpen] = useState(false);
  const [isAdminReqModalOpen, setIsAdminReqModalOpen] = useState(false);

  const fetchAllData = async (showLoader = false) => {
    if (!groupId) return;
    if (showLoader || !group) setLoading(true);
    try {
      const g = await groupsApi.getGroupDetail(groupId);
      setGroup(g);

      const exps = await expensesApi.listGroupExpenses(groupId, includeDeleted);
      setExpenses(exps);

      const bals = await groupsApi.getBalances(groupId);
      setBalances(bals);

      // Check if user is admin/super_admin to fetch request queues
      const myMem = g.members.find((m) => m.user_id === user?.id);
      if (myMem && (myMem.role === 'admin' || myMem.role === 'super_admin')) {
        try {
          const jReqs = await groupsApi.listJoinRequests(groupId);
          setJoinRequests(jReqs);
          const aReqs = await groupsApi.listAdminRequests(groupId);
          setAdminRequests(aReqs);
        } catch {
          // ignore queue fetch errors
        }
      }
    } catch (err: any) {
      error('Access Error', err.response?.data?.detail || 'Could not load group details.');
      navigate('/');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAllData(true);
  }, [groupId, includeDeleted]);

  const copyGroupId = () => {
    if (!groupId) return;
    navigator.clipboard.writeText(groupId);
    success('Copied to Clipboard!', 'Share this Group ID with friends to join.');
  };

  const handleRespondShare = async (expenseId: string, approve: boolean) => {
    try {
      await expensesApi.respondShare(expenseId, approve);
      success(approve ? 'Share Approved!' : 'Share Rejected!');
      fetchAllData(false);
    } catch (err: any) {
      error('Response Failed', err.response?.data?.detail || 'Unexpected error');
    }
  };

  const handleDeleteExpense = async (expenseId: string) => {
    if (!window.confirm('Are you sure you want to soft-delete this expense? History will be preserved.')) {
      return;
    }
    try {
      await expensesApi.deleteExpense(expenseId);
      success('Expense Soft-Deleted!', 'Expense removed from active balances.');
      fetchAllData(false);
    } catch (err: any) {
      error('Delete Failed', err.response?.data?.detail || 'Unexpected error');
    }
  };

  const handlePromoteMember = async (targetUserId: string) => {
    if (!groupId) return;
    try {
      await groupsApi.promoteMember(groupId, targetUserId);
      success('Member Promoted!', 'Target member is now an Admin.');
      fetchAllData(false);
    } catch (err: any) {
      error('Promotion Failed', err.response?.data?.detail || 'Unexpected error');
    }
  };

  const handleRemoveMember = async (targetUserId: string) => {
    if (!groupId) return;
    if (!window.confirm('Are you sure you want to remove this member from the group?')) return;
    try {
      await groupsApi.removeMember(groupId, targetUserId);
      success('Member Removed!');
      fetchAllData(false);
    } catch (err: any) {
      error('Removal Failed', err.response?.data?.detail || 'Unexpected error');
    }
  };

  const handleLeaveGroup = async () => {
    if (!groupId || !group || !user) return;
    const myMem = group.members.find((m) => m.user_id === user.id);
    let successorId: string | undefined = undefined;

    if (myMem?.role === 'super_admin') {
      const candidates = group.members.filter((m) => m.user_id !== user.id);
      if (candidates.length === 0) {
        error('Cannot Leave', 'You are the only member in this group.');
        return;
      }
      const choice = window.prompt(
        `As Super Admin you must designate a successor before leaving.\nEnter successor User ID:\n\n${candidates
          .map((c) => `${c.user?.name}: ${c.user_id}`)
          .join('\n')}`
      );
      if (!choice) return;
      successorId = choice.trim();
    } else {
      if (!window.confirm('Are you sure you want to leave this group?')) return;
    }

    try {
      await groupsApi.leaveGroup(groupId, successorId);
      success('Left Group Successfully.');
      navigate('/');
    } catch (err: any) {
      error('Leave Failed', err.response?.data?.detail || 'Unexpected error');
    }
  };

  const myMembership = group?.members.find((m) => m.user_id === user?.id);
  const myRole: MemberRole = myMembership?.role || 'member';

  if (loading && !group) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-emerald-600 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 lg:px-8 py-8">
        {/* Back Link */}
        <Link
          to="/"
          className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-900 transition-colors mb-4 font-semibold"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Dashboard</span>
        </Link>

        {/* Group Header Banner */}
        {group && (
          <div className="bg-white rounded-3xl p-6 lg:p-8 mb-8 border border-slate-200 shadow-xs relative overflow-hidden">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
              <div className="flex items-start gap-4">
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-500 to-emerald-600 flex items-center justify-center text-white font-extrabold text-2xl shadow-md shadow-emerald-500/20 shrink-0">
                  {group.name.charAt(0).toUpperCase()}
                </div>

                <div>
                  <h1 className="text-2xl font-extrabold text-slate-900">{group.name}</h1>
                  <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                    <button
                      onClick={copyGroupId}
                      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-mono border border-slate-200 transition-colors cursor-pointer"
                    >
                      <Copy className="w-3 h-3 text-indigo-600" />
                      <span>ID: {group.id.substring(0, 8)}...</span>
                    </button>

                    <span className="text-xs text-slate-500">
                      Created by {group.members.find((m) => m.user_id === group.created_by)?.user?.name || 'Owner'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Action Buttons & Admin Queue Badges */}
              <div className="flex items-center gap-3 flex-wrap">
                <button
                  onClick={() => setIsCreateExpenseOpen(true)}
                  className="flex items-center gap-2 px-4.5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-md transition-all hover:scale-[1.02] cursor-pointer"
                >
                  <PlusCircle className="w-4 h-4" />
                  <span>Log Expense</span>
                </button>

                {/* Queue triggers for admin */}
                {(myRole === 'admin' || myRole === 'super_admin') && (
                  <>
                    {joinRequests.length > 0 && (
                      <button
                        onClick={() => setIsJoinReqModalOpen(true)}
                        className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-amber-50 text-amber-800 border border-amber-200 text-xs font-bold shadow-2xs cursor-pointer"
                      >
                        <UserPlus className="w-4 h-4 text-amber-600" />
                        <span>Join Requests ({joinRequests.length})</span>
                      </button>
                    )}

                    {adminRequests.length > 0 && (
                      <button
                        onClick={() => setIsAdminReqModalOpen(true)}
                        className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-indigo-50 text-indigo-800 border border-indigo-200 text-xs font-bold shadow-2xs cursor-pointer"
                      >
                        <Shield className="w-4 h-4 text-indigo-600" />
                        <span>Admin Requests ({adminRequests.length})</span>
                      </button>
                    )}
                  </>
                )}
              </div>
            </div>

            {/* Tab Navigation */}
            <div className="flex items-center gap-2 mt-8 pt-6 border-t border-slate-100">
              <button
                onClick={() => setActiveTab('expenses')}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                  activeTab === 'expenses'
                    ? 'bg-emerald-50 text-emerald-800 border border-emerald-200 shadow-2xs'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                <Receipt className="w-4 h-4" />
                <span>Expenses ({expenses.length})</span>
              </button>

              <button
                onClick={() => setActiveTab('balances')}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                  activeTab === 'balances'
                    ? 'bg-emerald-50 text-emerald-800 border border-emerald-200 shadow-2xs'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                <Sparkles className="w-4 h-4" />
                <span>Net Balances & Debts</span>
              </button>

              <button
                onClick={() => setActiveTab('members')}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                  activeTab === 'members'
                    ? 'bg-emerald-50 text-emerald-800 border border-emerald-200 shadow-2xs'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                <Users className="w-4 h-4" />
                <span>Members ({group.members.length})</span>
              </button>
            </div>
          </div>
        )}

        {/* Tab Content */}

        {/* TAB 1: EXPENSES */}
        {activeTab === 'expenses' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider">
                Group Expenses History
              </h3>

              <label className="flex items-center gap-2 text-xs text-slate-600 font-semibold cursor-pointer">
                <input
                  type="checkbox"
                  checked={includeDeleted}
                  onChange={(e) => setIncludeDeleted(e.target.checked)}
                  className="rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
                />
                <span>Include Soft-Deleted</span>
              </label>
            </div>

            {expenses.length === 0 ? (
              <div className="bg-white rounded-3xl p-12 text-center border border-slate-200 shadow-xs">
                <Receipt className="w-10 h-10 text-slate-400 mx-auto mb-3" />
                <h4 className="text-base font-bold text-slate-900 mb-1">No Expenses Logged Yet</h4>
                <p className="text-xs text-slate-500 mb-4">
                  Log your first group expense to start splitting equal or custom shares.
                </p>
                <button
                  onClick={() => setIsCreateExpenseOpen(true)}
                  className="px-4.5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-md cursor-pointer"
                >
                  Log First Expense
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {expenses.map((exp) => (
                  <ExpenseCard
                    key={exp.id}
                    expense={exp}
                    onRespondShare={handleRespondShare}
                    onDeleteExpense={handleDeleteExpense}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB 2: NET BALANCES & DEBTS */}
        {activeTab === 'balances' && balances && groupId && (
          <NetDebtSimplifier
            groupId={groupId}
            balanceData={balances}
            onDebtSettled={() => fetchAllData(false)}
          />
        )}

        {/* TAB 3: MEMBERS */}
        {activeTab === 'members' && group && (
          <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-xs">
            <MembersList
              members={group.members}
              myRole={myRole}
              onPromoteMember={handlePromoteMember}
              onRemoveMember={handleRemoveMember}
              onLeaveGroup={handleLeaveGroup}
            />
          </div>
        )}
      </main>

      {/* Modals */}
      {group && (
        <CreateExpenseModal
          isOpen={isCreateExpenseOpen}
          onClose={() => setIsCreateExpenseOpen(false)}
          groupId={group.id}
          members={group.members}
          onExpenseCreated={() => fetchAllData(false)}
        />
      )}

      <JoinRequestsModal
        isOpen={isJoinReqModalOpen}
        onClose={() => setIsJoinReqModalOpen(false)}
        requests={joinRequests}
        onApprove={async (reqId) => {
          if (!groupId) return;
          await groupsApi.approveJoinRequest(groupId, reqId);
          success('Join Request Approved!');
          fetchAllData(false);
        }}
        onReject={async (reqId) => {
          if (!groupId) return;
          await groupsApi.rejectJoinRequest(groupId, reqId);
          success('Join Request Rejected.');
          fetchAllData(false);
        }}
      />

      <AdminRequestsModal
        isOpen={isAdminReqModalOpen}
        onClose={() => setIsAdminReqModalOpen(false)}
        requests={adminRequests}
        onApprove={async (reqId) => {
          if (!groupId) return;
          await groupsApi.approveAdminRequest(groupId, reqId);
          success('Admin Promotion Approved!');
          fetchAllData(false);
        }}
        onReject={async (reqId) => {
          if (!groupId) return;
          await groupsApi.rejectAdminRequest(groupId, reqId);
          success('Admin Request Rejected.');
          fetchAllData(false);
        }}
      />
    </div>
  );
};
