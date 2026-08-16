import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Wallet, LogOut, PlusCircle, User as UserIcon } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface NavbarProps {
  onCreateGroupClick?: () => void;
  onJoinGroupClick?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onCreateGroupClick, onJoinGroupClick }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="sticky top-0 z-40 w-full glass-panel border-b border-slate-800/80 px-4 lg:px-8 py-3.5">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Brand Logo */}
        <Link to="/" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 via-teal-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-emerald-500/20 group-hover:scale-105 transition-transform duration-200">
            <Wallet className="w-5 h-5 text-slate-950 font-bold" />
          </div>
          <div>
            <span className="text-lg font-bold bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
              Expense<span className="text-emerald-400 font-extrabold">Splitter</span>
            </span>
            <span className="block text-[10px] uppercase tracking-wider text-slate-400 font-semibold -mt-1">
              Group Money Engine
            </span>
          </div>
        </Link>

        {/* User profile & Actions */}
        {user && (
          <div className="flex items-center gap-3">
            {onCreateGroupClick && (
              <button
                onClick={onCreateGroupClick}
                className="hidden sm:flex items-center gap-2 px-3.5 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold text-xs transition-all shadow-md shadow-emerald-500/20 hover:scale-[1.02] active:scale-[0.98]"
              >
                <PlusCircle className="w-4 h-4" />
                <span>New Group</span>
              </button>
            )}

            {onJoinGroupClick && (
              <button
                onClick={onJoinGroupClick}
                className="hidden sm:flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-xs border border-slate-700 transition-all hover:scale-[1.02]"
              >
                <span>Join Group</span>
              </button>
            )}

            {/* Profile Pill */}
            <div className="flex items-center gap-2.5 pl-3 border-l border-slate-800">
              <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-emerald-400 font-bold text-xs">
                {user.name ? user.name.charAt(0).toUpperCase() : <UserIcon className="w-4 h-4" />}
              </div>
              <div className="hidden md:block text-left">
                <span className="block text-xs font-semibold text-slate-200 leading-tight">
                  {user.name}
                </span>
                <span className="block text-[10px] text-slate-400 truncate max-w-[120px]">
                  {user.email}
                </span>
              </div>

              <button
                onClick={handleLogout}
                title="Logout"
                className="p-2 text-slate-400 hover:text-rose-400 hover:bg-slate-800/80 rounded-lg transition-colors ml-1"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </header>
  );
};
