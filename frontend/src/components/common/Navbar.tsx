import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Wallet, LogOut, PlusCircle, User as UserIcon, UserPlus } from 'lucide-react';
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
    <header className="sticky top-0 z-40 w-full bg-white/85 backdrop-blur-md border-b border-slate-200/80 px-4 lg:px-8 py-3 shadow-xs">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Brand Logo */}
        <Link to="/" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 via-teal-600 to-indigo-600 flex items-center justify-center shadow-md shadow-emerald-500/20 group-hover:scale-105 transition-transform duration-200">
            <Wallet className="w-5 h-5 text-white font-bold" />
          </div>
          <div>
            <span className="text-lg font-extrabold text-slate-900 tracking-tight">
              Expense<span className="text-emerald-600">Splitter</span>
            </span>
            <span className="block text-[10px] uppercase tracking-wider text-slate-400 font-bold -mt-1">
              Smart Group Expenses
            </span>
          </div>
        </Link>

        {/* User Profile & Quick Actions */}
        {user && (
          <div className="flex items-center gap-3">
            {onCreateGroupClick && (
              <button
                onClick={onCreateGroupClick}
                className="hidden sm:flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs shadow-sm transition-all hover:shadow-md hover:scale-[1.02] active:scale-[0.98] cursor-pointer"
              >
                <PlusCircle className="w-4 h-4" />
                <span>New Group</span>
              </button>
            )}

            {onJoinGroupClick && (
              <button
                onClick={onJoinGroupClick}
                className="hidden sm:flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs border border-slate-200 transition-all hover:scale-[1.02] cursor-pointer"
              >
                <UserPlus className="w-4 h-4 text-slate-500" />
                <span>Join Group</span>
              </button>
            )}

            {/* Profile Pill */}
            <div className="flex items-center gap-3 pl-3 border-l border-slate-200">
              <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-indigo-50 to-emerald-50 border border-slate-200 flex items-center justify-center text-indigo-700 font-bold text-xs shadow-2xs">
                {user.name ? user.name.charAt(0).toUpperCase() : <UserIcon className="w-4 h-4" />}
              </div>
              <div className="hidden md:block text-left">
                <span className="block text-xs font-bold text-slate-900 leading-tight">
                  {user.name}
                </span>
                <span className="block text-[11px] text-slate-500 truncate max-w-[130px]">
                  {user.email}
                </span>
              </div>

              <button
                onClick={handleLogout}
                title="Logout"
                className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-xl transition-colors cursor-pointer ml-1"
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
