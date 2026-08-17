import React from 'react';
import { Link } from 'react-router-dom';
import { Group } from '../../types';
import { Users, ChevronRight, Calendar, Copy, Check } from 'lucide-react';
import { useState } from 'react';
import { useToast } from '../../context/ToastContext';

interface GroupCardProps {
  group: Group;
}

export const GroupCard: React.FC<GroupCardProps> = ({ group }) => {
  const [copied, setCopied] = useState(false);
  const { success } = useToast();

  const formattedDate = new Date(group.created_at).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });

  const handleCopyCode = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    navigator.clipboard.writeText(group.id);
    setCopied(true);
    success('Invite Code Copied!', 'Group ID copied to clipboard.');
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Link
      to={`/groups/${group.id}`}
      className="group block bg-white border border-slate-200 hover:border-indigo-300 rounded-2xl p-5 relative overflow-hidden transition-all duration-200 shadow-sm hover:shadow-xl hover:-translate-y-1"
    >
      {/* Top accent border line */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-emerald-500 via-teal-500 to-indigo-600 opacity-80 group-hover:opacity-100 transition-opacity" />

      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-50 to-emerald-50 border border-slate-200 flex items-center justify-center text-indigo-700 font-extrabold text-lg group-hover:scale-105 transition-transform shadow-2xs">
            {group.name.charAt(0).toUpperCase()}
          </div>
          <div>
            <h4 className="text-base font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">
              {group.name}
            </h4>
            <div className="flex items-center gap-1.5 text-xs text-slate-500 mt-1">
              <Calendar className="w-3.5 h-3.5 text-slate-400" />
              <span>Created {formattedDate}</span>
            </div>
          </div>
        </div>

        <div className="w-8 h-8 rounded-full bg-slate-50 border border-slate-200 flex items-center justify-center text-slate-400 group-hover:text-indigo-600 group-hover:bg-indigo-50 transition-all">
          <ChevronRight className="w-4 h-4" />
        </div>
      </div>

      <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-600">
        <span className="flex items-center gap-1.5 font-medium text-slate-700">
          <Users className="w-3.5 h-3.5 text-emerald-600" />
          <span>Active Group</span>
        </span>

        <button
          onClick={handleCopyCode}
          title="Copy Group Invite Code"
          className="flex items-center gap-1 font-mono text-[11px] bg-slate-100 hover:bg-slate-200 px-2 py-0.5 rounded-md text-slate-600 transition-colors cursor-pointer"
        >
          {copied ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3 text-slate-400" />}
          <span>{group.id.substring(0, 8)}...</span>
        </button>
      </div>
    </Link>
  );
};
