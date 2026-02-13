import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';

const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const { isDark } = useTheme();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const usernameRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    usernameRef.current?.focus();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) {
      setError('ユーザー名とパスワードを入力してください');
      return;
    }

    setError('');
    setIsSubmitting(true);

    try {
      await login(username, password);
    } catch (err: any) {
      if (err.message?.includes('429') || err.message?.includes('Too many')) {
        setError('リクエストが多すぎます。しばらくお待ちください。');
      } else {
        setError(err.message || 'ログインに失敗しました');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className={`min-h-screen flex items-center justify-center p-4 transition-colors duration-300 ${
      isDark ? 'bg-[#050505]' : 'bg-slate-50'
    }`}>
      {/* Background effects */}
      <div className="fixed inset-0 z-0">
        <div className={`absolute inset-0 ${
          isDark
            ? 'bg-gradient-to-br from-blue-950/20 via-transparent to-cyan-950/20'
            : 'bg-gradient-to-br from-blue-50 via-white to-cyan-50'
        }`} />
      </div>

      <div className={`relative z-10 w-full max-w-md ${
        isDark
          ? 'bg-white/[0.03] border border-white/10'
          : 'bg-white/80 border border-slate-200'
      } backdrop-blur-xl rounded-2xl p-8 shadow-2xl`}>

        {/* Logo / Header */}
        <div className="text-center mb-8">
          <div className={`text-4xl font-black italic tracking-tighter mb-2 ${
            isDark ? 'text-white' : 'text-slate-900'
          }`}>
            <span className="text-cyan-500">YUKYU</span>PRO
          </div>
          <p className={`text-sm tracking-widest uppercase ${
            isDark ? 'text-white/40' : 'text-slate-400'
          }`}>
            有給休暇管理システム
          </p>
        </div>

        {/* Error message */}
        {error && (
          <div className="mb-6 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm text-center">
            {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label htmlFor="username" className={`block text-xs font-bold uppercase tracking-wider mb-2 ${
              isDark ? 'text-white/50' : 'text-slate-500'
            }`}>
              ユーザー名
            </label>
            <input
              ref={usernameRef}
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className={`w-full px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 ${
                isDark
                  ? 'bg-white/5 border border-white/10 text-white placeholder-white/20 focus:border-cyan-500/50 focus:bg-white/[0.07]'
                  : 'bg-slate-50 border border-slate-200 text-slate-900 placeholder-slate-400 focus:border-cyan-500 focus:bg-white'
              } outline-none`}
              placeholder="admin"
              autoComplete="username"
              disabled={isSubmitting}
            />
          </div>

          <div>
            <label htmlFor="password" className={`block text-xs font-bold uppercase tracking-wider mb-2 ${
              isDark ? 'text-white/50' : 'text-slate-500'
            }`}>
              パスワード
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={`w-full px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 ${
                isDark
                  ? 'bg-white/5 border border-white/10 text-white placeholder-white/20 focus:border-cyan-500/50 focus:bg-white/[0.07]'
                  : 'bg-slate-50 border border-slate-200 text-slate-900 placeholder-slate-400 focus:border-cyan-500 focus:bg-white'
              } outline-none`}
              placeholder="••••••••"
              autoComplete="current-password"
              disabled={isSubmitting}
            />
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className={`w-full py-3 rounded-lg text-sm font-black uppercase tracking-wider transition-all duration-200 ${
              isSubmitting
                ? 'opacity-50 cursor-not-allowed'
                : 'hover:scale-[1.02] active:scale-[0.98]'
            } ${
              isDark
                ? 'bg-cyan-500 text-black hover:bg-cyan-400'
                : 'bg-cyan-600 text-white hover:bg-cyan-500'
            }`}
          >
            {isSubmitting ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                ログイン中...
              </span>
            ) : 'ログイン'}
          </button>
        </form>

        {/* Footer */}
        <div className={`mt-8 text-center text-xs ${isDark ? 'text-white/20' : 'text-slate-300'}`}>
          UNS Corporation &copy; {new Date().getFullYear()}
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
