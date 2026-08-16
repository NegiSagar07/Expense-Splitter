import React from 'react';
import { Link } from 'react-router-dom';
import { Group } from '../../types';
import { Users, ChevronRight, Calendar } from 'lucide-react';

interface GroupCardProps {
  group: Group;
}

export const GroupCard: React.FC<GroupCardProps> = ({ group }) => {
  const formattedDate = new Date(group.created_at).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });

  return (
    <Link
      to={`/groups/${group.id}`}
      className="group block glass-panel glass-panel-hover rounded-2xl p-5 relative overflow-hidden"
    >
      {/* Top accent glow */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-emerald-500 via-teal-400 to-cyan-500 opacity-80 group-hover:opacity-100 transition-opacity" />

      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-900/60 to-slate-800 border border-emerald-500/30 flex items-center justify-center text-emerald-400 font-bold text-lg group-hover:scale-105 transition-transform">
            {group.name.charAt(0).toUpperCase()}
          </div>
          <div>
            <h4 className="text-base font-bold text-slate-100 group-hover:text-emerald-400 transition-colors">
              {group.name}
            </h4>
            <div className="flex items-center gap-1.5 text-xs text-slate-400 mt-1">
              <Calendar className="w-3.5 h-3.5" />
              <span>Created {formattedDate}</span>
            </div>
          </div>
        </div>

        <div className="w-8 h-8 rounded-full bg-slate-800/80 border border-slate-700 flex items-center justify-center text-slate-400 group-hover:text-emerald-400 group-hover:bg-slate-800 transition-all">
          <ChevronRight className="w-4 h-4" />
        </div>
      </div>

      <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
        <span className="flex items-center gap-1.5 text-slate-300">
          <Users className="w-3.5 h-3.5 text-emerald-400" />
          <span>Active Group</span>
        </span>
        <span className="font-mono text-[11px] text-slate-400 truncate max-w-[140px]">
          ID: {group.id.substring(0, 8)}...
        </span>
      </div>
    </Link>
  );
};
