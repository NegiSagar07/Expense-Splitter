import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authApi } from '../api/authApi';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { Wallet, Sparkles, ArrowRight, ShieldCheck, Zap, AlertCircle, UserPlus } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const { login } = useAuth();
  const { success, error } = useToast();
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) return;

    setLoading(true);
    setErrorMessage(null);

    try {
      const res = await authApi.login(email.trim(), password);
      await login(res.access_token);
      success('Welcome Back!', 'Logged in successfully.');
      navigate('/');
    } catch (err: any) {
      console.error('Login error:', err);
      let msg = 'Invalid email or password';
      if (err.response?.data?.detail) {
        msg = err.response.data.detail;
      } else if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
        msg = 'Server request timed out. Render backend may be starting up — please try again in 15 seconds.';
      } else if (err.code === 'ERR_NETWORK' || !err.response) {
        msg = 'Unable to connect to backend server. Please verify backend service status.';
      }
      setErrorMessage(msg);
      error('Login Failed', msg);
    } finally {
      setLoading(false);
    }
  };

  const fillDemoAccount = (demoEmail: string) => {
    setEmail(demoEmail);
    setPassword('password123');
    setErrorMessage(null);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4 sm:p-6 lg:p-8 relative overflow-hidden">
      {/* Ambient gradient graphics */}
      <div className="absolute top-10 left-10 w-96 h-96 bg-emerald-200/40 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-10 right-10 w-96 h-96 bg-indigo-200/40 rounded-full blur-3xl pointer-events-none" />

      <div className="max-w-4xl w-full grid grid-cols-1 md:grid-cols-2 rounded-3xl bg-white border border-slate-200 shadow-2xl relative z-10 overflow-hidden">
        {/* Left Side: Hero Brand Showcase */}
        <div className="p-8 lg:p-10 bg-gradient-to-br from-indigo-900 via-slate-900 to-indigo-950 text-white flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-3 mb-8">
              <div className="w-11 h-11 rounded-xl bg-emerald-500 flex items-center justify-center shadow-lg shadow-emerald-500/30">
                <Wallet className="w-6 h-6 text-white font-bold" />
              </div>
              <span className="text-xl font-bold text-white tracking-tight">
                Expense<span className="text-emerald-400">Splitter</span>
              </span>
            </div>

            <h2 className="text-2xl lg:text-3xl font-extrabold leading-tight mb-4 text-white">
              Split group expenses effortlessly.
            </h2>
            <p className="text-sm text-slate-300 leading-relaxed mb-6">
              Track shared trips, rent, and group bills with automatic debt simplification and real-time balance calculations.
            </p>

            {/* Feature Pills */}
            <div className="space-y-3">
              <div className="flex items-center gap-3 p-3 rounded-xl bg-white/10 backdrop-blur-md border border-white/15">
                <Sparkles className="w-4 h-4 text-emerald-400 shrink-0" />
                <span className="text-xs text-slate-200 font-medium">
                  Greedy Net Debt Simplification Algorithm
                </span>
              </div>
              <div className="flex items-center gap-3 p-3 rounded-xl bg-white/10 backdrop-blur-md border border-white/15">
                <ShieldCheck className="w-4 h-4 text-indigo-300 shrink-0" />
                <span className="text-xs text-slate-200 font-medium">
                  Role-based Access & Super Admin Controls
                </span>
              </div>
              <div className="flex items-center gap-3 p-3 rounded-xl bg-white/10 backdrop-blur-md border border-white/15">
                <Zap className="w-4 h-4 text-cyan-300 shrink-0" />
                <span className="text-xs text-slate-200 font-medium">
                  Equal & Custom Split Engine with Remainder Protection
                </span>
              </div>
            </div>
          </div>

          {/* Quick Demo Fill Buttons */}
          <div className="mt-8 pt-6 border-t border-white/15">
            <span className="block text-[11px] font-bold uppercase tracking-wider text-slate-300 mb-2.5">
              Quick Seed Demo Accounts:
            </span>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => fillDemoAccount('alice@example.com')}
                className="px-3 py-1.5 rounded-lg bg-white/15 hover:bg-white/25 text-white text-xs border border-white/20 transition-all font-medium cursor-pointer"
              >
                Alice (Super Admin)
              </button>
              <button
                type="button"
                onClick={() => fillDemoAccount('bob@example.com')}
                className="px-3 py-1.5 rounded-lg bg-white/15 hover:bg-white/25 text-white text-xs border border-white/20 transition-all font-medium cursor-pointer"
              >
                Bob (Admin)
              </button>
              <button
                type="button"
                onClick={() => fillDemoAccount('charlie@example.com')}
                className="px-3 py-1.5 rounded-lg bg-white/15 hover:bg-white/25 text-white text-xs border border-white/20 transition-all font-medium cursor-pointer"
              >
                Charlie (Member)
              </button>
            </div>
          </div>
        </div>

        {/* Right Side: Login Form */}
        <div className="p-8 lg:p-10 flex flex-col justify-center bg-white">
          <div className="mb-6">
            <h3 className="text-2xl font-extrabold text-slate-900">Welcome Back</h3>
            <p className="text-xs text-slate-500 mt-1">
              Enter your registered email and password to sign in.
            </p>
          </div>

          {/* Prominent Error Banner */}
          {errorMessage && (
            <div className="mb-5 p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-900 text-xs font-medium space-y-2.5 shadow-2xs">
              <div className="flex items-start gap-2.5">
                <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                <span className="leading-relaxed font-semibold">{errorMessage}</span>
              </div>
              
              {errorMessage.toLowerCase().includes('account') && (
                <div className="pt-2 border-t border-rose-200/80 flex items-center justify-between">
                  <span className="text-[11px] text-rose-700 font-normal">Need an account?</span>
                  <Link
                    to="/register"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs shadow-xs transition-colors cursor-pointer"
                  >
                    <UserPlus className="w-3.5 h-3.5" />
                    <span>Create Account</span>
                  </Link>
                </div>
              )}
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                Email Address
              </label>
              <input
                type="email"
                required
                placeholder="alice@example.com"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  if (errorMessage) setErrorMessage(null);
                }}
                className="w-full px-4 py-2.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 placeholder-slate-400 text-sm focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                Password
              </label>
              <input
                type="password"
                required
                placeholder="••••••••"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  if (errorMessage) setErrorMessage(null);
                }}
                className="w-full px-4 py-2.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 placeholder-slate-400 text-sm focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 transition-all"
              />
            </div>

            <button
              type="submit"
              disabled={loading || !email || !password}
              className="w-full py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm transition-all shadow-md hover:shadow-lg flex items-center justify-center gap-2 active:scale-[0.99] disabled:opacity-50 mt-2 cursor-pointer"
            >
              <span>{loading ? 'Authenticating...' : 'Sign In'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          <p className="text-xs text-center text-slate-500 mt-6">
            Don't have an account?{' '}
            <Link to="/register" className="text-indigo-600 font-bold hover:underline">
              Create one now
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};
