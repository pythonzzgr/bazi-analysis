import React, { useState } from 'react';
import { User, Lock, Sparkles, ArrowRight, UserPlus, Clock, CheckCircle } from 'lucide-react';
import { login, register, type SessionUser } from '@/lib/auth';

interface Props {
  onAuth: (user: SessionUser) => void;
}

type Mode = 'login' | 'register';

export default function AuthPage({ onAuth }: Props) {
  const [mode, setMode] = useState<Mode>('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [pendingApproval, setPendingApproval] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);

    try {
      if (mode === 'login') {
        const result = await login(username, password);
        if (result.success && result.user) {
          onAuth(result.user);
        } else {
          setError(result.error || '로그인에 실패했습니다.');
        }
      } else {
        const result = await register(username, password, displayName);
        if (result.success && result.pendingApproval) {
          setPendingApproval(true);
        } else {
          setError(result.error || '회원가입에 실패했습니다.');
        }
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const switchMode = () => {
    setMode(mode === 'login' ? 'register' : 'login');
    setError('');
    setUsername('');
    setPassword('');
    setDisplayName('');
    setPendingApproval(false);
  };

  if (pendingApproval) {
    return (
      <div className="min-h-screen flex flex-col justify-center max-w-md mx-auto px-6 py-12">
        <div className="text-center mb-10">
          <div className="w-16 h-16 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center mx-auto mb-5">
            <Sparkles className="w-8 h-8 text-primary" />
          </div>
          <p className="text-sm font-semibold text-slate-400 tracking-widest uppercase mb-2">Destiny Compass</p>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white">사주 분석</h1>
        </div>

        <div className="glass-card rounded-3xl p-8 border border-slate-200 dark:border-slate-700 shadow-lg text-center">
          <div className="w-16 h-16 rounded-full bg-amber-50 dark:bg-amber-900/20 flex items-center justify-center mx-auto mb-5">
            <Clock className="w-8 h-8 text-amber-500" />
          </div>
          <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-3">가입 신청 완료</h2>
          <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed mb-2">
            관리자의 승인을 기다리고 있습니다.
          </p>
          <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed mb-6">
            승인이 완료되면 로그인하실 수 있습니다.
          </p>

          <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 mb-6">
            <CheckCircle className="w-4 h-4 text-emerald-500 shrink-0" />
            <div className="text-left">
              <p className="text-xs text-slate-400">가입 신청 아이디</p>
              <p className="text-sm font-semibold text-slate-700 dark:text-slate-200">{username}</p>
            </div>
          </div>

          <button
            onClick={switchMode}
            className="w-full h-12 rounded-xl bg-primary text-white text-sm font-bold shadow-[0_8px_16px_-4px_rgba(19,127,236,0.4)] hover:bg-primary/90 active:scale-[0.98] transition-all flex items-center justify-center gap-2"
          >
            로그인 화면으로
            <ArrowRight size={16} />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col justify-center max-w-md mx-auto px-6 py-12">
      {/* Branding */}
      <div className="text-center mb-10">
        <div className="w-16 h-16 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center mx-auto mb-5">
          <Sparkles className="w-8 h-8 text-primary" />
        </div>
        <p className="text-sm font-semibold text-slate-400 tracking-widest uppercase mb-2">Destiny Compass</p>
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white">사주 분석</h1>
      </div>

      {/* Auth Card */}
      <div className="glass-card rounded-3xl p-6 border border-slate-200 dark:border-slate-700 shadow-lg">
        <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-6 text-center">
          {mode === 'login' ? '로그인' : '회원가입'}
        </h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Display Name (회원가입 시만) */}
          {mode === 'register' && (
            <div className="relative">
              <div className="absolute left-4 top-1/2 -translate-y-1/2">
                <UserPlus className="w-4 h-4 text-slate-400" />
              </div>
              <input
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="이름 (표시용)"
                className="w-full pl-11 pr-4 py-3.5 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 outline-none text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:border-primary focus:ring-1 focus:ring-primary transition-all"
                required
              />
            </div>
          )}

          {/* Username */}
          <div className="relative">
            <div className="absolute left-4 top-1/2 -translate-y-1/2">
              <User className="w-4 h-4 text-slate-400" />
            </div>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="아이디"
              className="w-full pl-11 pr-4 py-3.5 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 outline-none text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:border-primary focus:ring-1 focus:ring-primary transition-all"
              required
              autoComplete="username"
            />
          </div>

          {/* Password */}
          <div className="relative">
            <div className="absolute left-4 top-1/2 -translate-y-1/2">
              <Lock className="w-4 h-4 text-slate-400" />
            </div>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="비밀번호"
              className="w-full pl-11 pr-4 py-3.5 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 outline-none text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:border-primary focus:ring-1 focus:ring-primary transition-all"
              required
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
            />
          </div>

          {/* Error */}
          {error && (
            <p className="text-xs text-red-500 text-center px-2">{error}</p>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full h-12 rounded-xl bg-primary text-white text-sm font-bold shadow-[0_8px_16px_-4px_rgba(19,127,236,0.4)] hover:bg-primary/90 active:scale-[0.98] transition-all disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {isSubmitting ? (
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <>
                {mode === 'login' ? '로그인' : '가입 신청'}
                <ArrowRight size={16} />
              </>
            )}
          </button>
        </form>

        {mode === 'register' && (
          <p className="mt-4 text-[11px] text-slate-400 text-center leading-relaxed">
            가입 신청 후 관리자 승인이 필요합니다
          </p>
        )}

        {/* Switch Mode */}
        <div className="mt-6 text-center">
          <button
            onClick={switchMode}
            className="text-xs text-slate-400 hover:text-primary transition-colors"
          >
            {mode === 'login'
              ? '계정이 없으신가요? 회원가입'
              : '이미 계정이 있으신가요? 로그인'}
          </button>
        </div>
      </div>
    </div>
  );
}
