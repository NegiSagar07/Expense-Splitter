import React, { useState, useEffect } from 'react';
import { Navbar } from '../components/common/Navbar';
import { GroupCard } from '../components/groups/GroupCard';
import { CreateGroupModal } from '../components/groups/CreateGroupModal';
import { JoinGroupModal } from '../components/groups/JoinGroupModal';
import { groupsApi } from '../api/groupsApi';
import { Group } from '../types';
import { useAuth } from '../context/AuthContext';
import { PlusCircle, UserPlus, Users, Sparkles, Loader2, Wallet } from 'lucide-react';
import { motion } from 'framer-motion';

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [groups, setGroups] = useState<Group[]>([]);
  const [loading, setLoading] = useState(true);

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isJoinModalOpen, setIsJoinModalOpen] = useState(false);

  const fetchGroups = async () => {
    setLoading(true);
    try {
      const data = await groupsApi.listGroups();
      setGroups(data);
    } catch {
      setGroups([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGroups();
  }, []);

  const handleGroupCreated = (newGroup: Group) => {
    setGroups((prev) => [newGroup, ...prev]);
  };

  return (
    <div className="min-h-screen bg-[#090d16] flex flex-col">
      <Navbar
        onCreateGroupClick={() => setIsCreateModalOpen(true)}
        onJoinGroupClick={() => setIsJoinModalOpen(true)}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 lg:px-8 py-8">
        {/* Welcome Header */}
        <div className="mb-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl lg:text-3xl font-extrabold text-slate-100 flex items-center gap-2">
              <span>Welcome back, {user?.name || 'Friend'}</span>
              <Sparkles className="w-6 h-6 text-emerald-400" />
            </h1>
            <p className="text-xs lg:text-sm text-slate-400 mt-1">
              Manage your group expenses, review pending shares, and settle balances cleanly.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsCreateModalOpen(true)}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs shadow-lg shadow-emerald-500/20 transition-all hover:scale-[1.02] active:scale-[0.98]"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Create New Group</span>
            </button>

            <button
              onClick={() => setIsJoinModalOpen(true)}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs border border-slate-700 transition-all hover:scale-[1.02]"
            >
              <UserPlus className="w-4 h-4 text-teal-400" />
              <span>Join Group</span>
            </button>
          </div>
        </div>

        {/* Quick Glance Metrics */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          <div className="glass-panel rounded-2xl p-4 flex items-center gap-4 border border-slate-800">
            <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <Users className="w-6 h-6" />
            </div>
            <div>
              <span className="block text-2xl font-extrabold text-slate-100 font-mono-amount">
                {groups.length}
              </span>
              <span className="block text-xs text-slate-400 font-medium">Active Groups</span>
            </div>
          </div>

          <div className="glass-panel rounded-2xl p-4 flex items-center gap-4 border border-slate-800">
            <div className="w-12 h-12 rounded-xl bg-teal-500/10 border border-teal-500/20 flex items-center justify-center text-teal-400">
              <Wallet className="w-6 h-6" />
            </div>
            <div>
              <span className="block text-2xl font-extrabold text-slate-100 font-mono-amount">
                FR16
              </span>
              <span className="block text-xs text-slate-400 font-medium">Net Debt Simplification</span>
            </div>
          </div>

          <div className="glass-panel rounded-2xl p-4 flex items-center gap-4 border border-slate-800">
            <div className="w-12 h-12 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
              <Sparkles className="w-6 h-6" />
            </div>
            <div>
              <span className="block text-2xl font-extrabold text-slate-100 font-mono-amount">
                Equal & Custom
              </span>
              <span className="block text-xs text-slate-400 font-medium">Split Calculation</span>
            </div>
          </div>
        </div>

        {/* Groups Section */}
        <div>
          <h3 className="text-base font-bold text-slate-200 mb-4 flex items-center gap-2">
            <span>Your Expense Groups</span>
            <span className="px-2 py-0.5 rounded-full text-xs bg-slate-800 text-slate-400 font-mono-amount">
              {groups.length}
            </span>
          </h3>

          {loading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="w-8 h-8 text-emerald-400 animate-spin" />
            </div>
          ) : groups.length === 0 ? (
            <div className="glass-panel rounded-3xl p-12 text-center border border-slate-800 max-w-xl mx-auto my-8">
              <div className="w-16 h-16 rounded-2xl bg-slate-800/80 border border-slate-700 flex items-center justify-center text-emerald-400 mx-auto mb-4">
                <Users className="w-8 h-8" />
              </div>
              <h4 className="text-lg font-bold text-slate-100 mb-2">No Groups Yet</h4>
              <p className="text-xs text-slate-400 max-w-md mx-auto mb-6">
                Create a new group for your trips, room rent, or event bills, or join an existing group with a Group UUID.
              </p>
              <div className="flex items-center justify-center gap-3">
                <button
                  onClick={() => setIsCreateModalOpen(true)}
                  className="px-4 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs shadow-md"
                >
                  Create First Group
                </button>
                <button
                  onClick={() => setIsJoinModalOpen(true)}
                  className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-xs border border-slate-700"
                >
                  Join via ID
                </button>
              </div>
            </div>
          ) : (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"
            >
              {groups.map((group) => (
                <GroupCard key={group.id} group={group} />
              ))}
            </motion.div>
          )}
        </div>
      </main>

      {/* Modals */}
      <CreateGroupModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onGroupCreated={handleGroupCreated}
      />

      <JoinGroupModal
        isOpen={isJoinModalOpen}
        onClose={() => setIsJoinModalOpen(false)}
      />
    </div>
  );
};
