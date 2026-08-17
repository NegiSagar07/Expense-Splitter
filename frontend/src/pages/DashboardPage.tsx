import React, { useState, useEffect, useMemo } from 'react';
import { Navbar } from '../components/common/Navbar';
import { GroupCard } from '../components/groups/GroupCard';
import { CreateGroupModal } from '../components/groups/CreateGroupModal';
import { JoinGroupModal } from '../components/groups/JoinGroupModal';
import { groupsApi } from '../api/groupsApi';
import { Group } from '../types';
import { useAuth } from '../context/AuthContext';
import { PlusCircle, UserPlus, Users, Sparkles, Loader2, Wallet, Search } from 'lucide-react';
import { motion } from 'framer-motion';

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [groups, setGroups] = useState<Group[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

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

  const filteredGroups = useMemo(() => {
    if (!searchQuery.trim()) return groups;
    return groups.filter((g) =>
      g.name.toLowerCase().includes(searchQuery.toLowerCase().trim()) ||
      g.id.toLowerCase().includes(searchQuery.toLowerCase().trim())
    );
  }, [groups, searchQuery]);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <Navbar
        onCreateGroupClick={() => setIsCreateModalOpen(true)}
        onJoinGroupClick={() => setIsJoinModalOpen(true)}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 lg:px-8 py-8">
        {/* Welcome Header */}
        <div className="mb-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl lg:text-3xl font-extrabold text-slate-900 flex items-center gap-2 tracking-tight">
              <span>Welcome back, {user?.name || 'Friend'}</span>
              <Sparkles className="w-6 h-6 text-emerald-600" />
            </h1>
            <p className="text-xs lg:text-sm text-slate-500 mt-1">
              Track shared trips, flat bills, and simplify net debts cleanly.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsCreateModalOpen(true)}
              className="flex items-center gap-2 px-4.5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-md transition-all hover:scale-[1.02] active:scale-[0.98] cursor-pointer"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Create Group</span>
            </button>

            <button
              onClick={() => setIsJoinModalOpen(true)}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white hover:bg-slate-100 text-slate-700 font-semibold text-xs border border-slate-200 transition-all hover:scale-[1.02] cursor-pointer"
            >
              <UserPlus className="w-4 h-4 text-indigo-600" />
              <span>Join Group</span>
            </button>
          </div>
        </div>

        {/* Quick Glance Metrics */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          <div className="bg-white rounded-2xl p-4.5 flex items-center gap-4 border border-slate-200/90 shadow-xs">
            <div className="w-12 h-12 rounded-xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600 shadow-2xs">
              <Users className="w-6 h-6" />
            </div>
            <div>
              <span className="block text-2xl font-extrabold text-slate-900 font-mono-amount leading-none">
                {groups.length}
              </span>
              <span className="block text-xs text-slate-500 font-semibold mt-1">Active Groups</span>
            </div>
          </div>

          <div className="bg-white rounded-2xl p-4.5 flex items-center gap-4 border border-slate-200/90 shadow-xs">
            <div className="w-12 h-12 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 shadow-2xs">
              <Wallet className="w-6 h-6" />
            </div>
            <div>
              <span className="block text-2xl font-extrabold text-slate-900 font-mono-amount leading-none">
                Greedy Debt
              </span>
              <span className="block text-xs text-slate-500 font-semibold mt-1">Net Simplification Engine</span>
            </div>
          </div>

          <div className="bg-white rounded-2xl p-4.5 flex items-center gap-4 border border-slate-200/90 shadow-xs">
            <div className="w-12 h-12 rounded-xl bg-violet-50 border border-violet-100 flex items-center justify-center text-violet-600 shadow-2xs">
              <Sparkles className="w-6 h-6" />
            </div>
            <div>
              <span className="block text-2xl font-extrabold text-slate-900 font-mono-amount leading-none">
                Equal & Custom
              </span>
              <span className="block text-xs text-slate-500 font-semibold mt-1">Split Modes</span>
            </div>
          </div>
        </div>

        {/* Search & Groups Section Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <span>Your Expense Groups</span>
            <span className="px-2.5 py-0.5 rounded-full text-xs bg-slate-200 text-slate-700 font-bold font-mono-amount">
              {filteredGroups.length}
            </span>
          </h3>

          <div className="relative w-full sm:w-64">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search groups..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-xl bg-white border border-slate-200 text-slate-900 text-xs placeholder-slate-400 focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20"
            />
          </div>
        </div>

        {/* Groups Grid */}
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="w-8 h-8 text-emerald-600 animate-spin" />
          </div>
        ) : filteredGroups.length === 0 ? (
          <div className="bg-white rounded-3xl p-12 text-center border border-slate-200 shadow-xs max-w-xl mx-auto my-8">
            <div className="w-16 h-16 rounded-2xl bg-slate-100 border border-slate-200 flex items-center justify-center text-emerald-600 mx-auto mb-4">
              <Users className="w-8 h-8" />
            </div>
            <h4 className="text-lg font-bold text-slate-900 mb-2">
              {searchQuery ? 'No matching groups found' : 'No Groups Yet'}
            </h4>
            <p className="text-xs text-slate-500 max-w-md mx-auto mb-6">
              {searchQuery
                ? `No group matches "${searchQuery}". Try a different keyword.`
                : 'Create a new group for your trips, room rent, or event bills, or join an existing group using a Group UUID.'}
            </p>
            <div className="flex items-center justify-center gap-3">
              <button
                onClick={() => setIsCreateModalOpen(true)}
                className="px-4.5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-md cursor-pointer"
              >
                Create First Group
              </button>
              <button
                onClick={() => setIsJoinModalOpen(true)}
                className="px-4 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs border border-slate-200 cursor-pointer"
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
            {filteredGroups.map((group) => (
              <GroupCard key={group.id} group={group} />
            ))}
          </motion.div>
        )}
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
