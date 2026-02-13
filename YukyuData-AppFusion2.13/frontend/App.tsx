
import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { Toaster } from 'react-hot-toast';
import toast from 'react-hot-toast';
import { motion, AnimatePresence } from 'framer-motion';
import { ThemeProvider, useTheme } from './contexts/ThemeContext';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import LoginPage from './components/LoginPage';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import ExcelSync from './components/ExcelSync';
import EmployeeList from './components/EmployeeList';
import LeaveRequest from './components/LeaveRequest';
import AccountingReports from './components/AccountingReports';
import ApplicationManagement from './components/ApplicationManagement';
import { DashboardSkeleton, EmployeeListSkeleton, ApplicationSkeleton, TableSkeleton } from './components/Skeleton';
import { api } from './services/apiService';
import { AppData } from './types';
import { useKeyboardShortcuts } from './hooks/useKeyboardShortcuts';

// Variantes de animación para transiciones de página
const pageVariants = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -20 }
};

const pageTransition = {
  type: 'tween',
  ease: 'easeInOut',
  duration: 0.25
};

// Inner App component that uses theme context
const AppContent: React.FC = () => {
  const { isDark } = useTheme();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [appData, setAppData] = useState<AppData>({
    employees: [],
    records: [],
    config: { companyName: 'UNS Corporation', fiscalYearStart: '04-01' }
  });
  const [isLoading, setIsLoading] = useState(true);

  // Load data from backend API on mount
  useEffect(() => {
    const loadFromBackend = async () => {
      try {
        const data = await api.loadData();
        setAppData(data);
      } catch (error) {
        console.error('Failed to load data from backend:', error);
        toast.error('データの読み込みに失敗しました');
      } finally {
        setIsLoading(false);
      }
    };
    loadFromBackend();
  }, []);

  // Show brief loading when switching tabs
  const handleTabChange = (tab: string) => {
    if (tab !== activeTab) {
      setIsLoading(true);
      setActiveTab(tab);
      setTimeout(() => setIsLoading(false), 300);
    }
  };

  const refreshData = useCallback(async () => {
    try {
      const data = await api.loadData();
      setAppData(data);
    } catch (error) {
      console.error('Failed to refresh data:', error);
    }
  }, []);

  // Atajos de teclado globales
  const shortcuts = useMemo(() => [
    {
      key: 'd',
      ctrl: true,
      action: () => handleTabChange('dashboard'),
      description: 'ダッシュボード'
    },
    {
      key: 'e',
      ctrl: true,
      action: () => handleTabChange('employees'),
      description: '社員一覧'
    },
    {
      key: 'n',
      ctrl: true,
      action: () => handleTabChange('leave-request'),
      description: '新規申請'
    },
    {
      key: 'a',
      ctrl: true,
      action: () => handleTabChange('applications'),
      description: '申請管理'
    },
    {
      key: 'r',
      ctrl: true,
      action: () => handleTabChange('reports'),
      description: 'レポート'
    },
    {
      key: 's',
      ctrl: true,
      action: () => handleTabChange('sync'),
      description: 'Excel同期'
    },
    {
      key: '/',
      ctrl: false,
      action: () => {
        toast('⌨️ ショートカット一覧\n\nCtrl+D: ダッシュボード\nCtrl+E: 社員一覧\nCtrl+N: 新規申請\nCtrl+A: 申請管理\nCtrl+R: レポート\nCtrl+S: Excel同期', {
          duration: 5000,
          style: { whiteSpace: 'pre-line' }
        });
      },
      description: 'ショートカット一覧'
    }
  ], []);

  useKeyboardShortcuts(shortcuts);

  const renderSkeleton = () => {
    switch (activeTab) {
      case 'dashboard':
        return <DashboardSkeleton />;
      case 'employees':
        return <EmployeeListSkeleton />;
      case 'applications':
        return <ApplicationSkeleton />;
      case 'reports':
        return (
          <div className="p-8 space-y-8">
            <TableSkeleton rows={8} columns={5} />
          </div>
        );
      default:
        return <DashboardSkeleton />;
    }
  };

  const renderContent = () => {
    if (isLoading) {
      return renderSkeleton();
    }

    switch (activeTab) {
      case 'dashboard':
        return <Dashboard data={appData} />;
      case 'sync':
        return <ExcelSync onSyncComplete={refreshData} />;
      case 'employees':
        return <EmployeeList employees={appData.employees} />;
      case 'reports':
        return <AccountingReports data={appData} />;
      case 'request':
        return <LeaveRequest data={appData} onSuccess={refreshData} />;
      case 'applications':
        return <ApplicationManagement data={appData} onUpdate={refreshData} />;
      default:
        return (
          <div className={`p-8 flex flex-col items-center justify-center h-full space-y-8 opacity-20`}>
            <div className={`text-8xl italic font-black tracking-tighter ${isDark ? 'text-white/10' : 'text-slate-200'}`}>UNS</div>
            <p className={`text-sm font-black tracking-[0.5em] uppercase ${isDark ? 'text-white/40' : 'text-slate-400'}`}>開発中のモジュールです</p>
          </div>
        );
    }
  };

  return (
    <div className={`flex h-screen selection:bg-blue-500/30 overflow-hidden font-['Plus_Jakarta_Sans','Noto_Sans_JP'] transition-colors duration-300 ${
      isDark ? 'bg-[#000000] text-white' : 'bg-slate-50 text-slate-900'
    }`}>
      {/* Noise Texture Overlay for that premium analog feel */}
      <div className={`fixed inset-0 pointer-events-none bg-[url('https://grainy-gradients.vercel.app/noise.svg')] z-50 ${isDark ? 'opacity-[0.02]' : 'opacity-[0.01]'}`}></div>

      <Sidebar activeTab={activeTab} setActiveTab={handleTabChange} />

      <main className={`flex-1 overflow-y-auto relative z-10 custom-scrollbar ${isDark ? '' : 'bg-slate-50'}`}>
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial="initial"
            animate="animate"
            exit="exit"
            variants={pageVariants}
            transition={pageTransition}
            className="min-h-screen"
          >
            {renderContent()}
          </motion.div>
        </AnimatePresence>
      </main>

      {/* React Hot Toast Notifications */}
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: isDark ? '#1a1a1a' : '#ffffff',
            color: isDark ? '#ffffff' : '#000000',
            border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.1)',
            fontWeight: 'bold',
            fontSize: '14px',
          },
          success: {
            iconTheme: {
              primary: '#22c55e',
              secondary: '#ffffff',
            },
          },
          error: {
            iconTheme: {
              primary: '#ef4444',
              secondary: '#ffffff',
            },
          },
        }}
      />

      <style>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 5px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: ${isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.1)'};
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: ${isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.2)'};
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(15px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fadeIn {
          animation: fadeIn 1s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }
      `}</style>
    </div>
  );
};

// Auth gate - shows login or app content
const AuthGate: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const { isDark } = useTheme();

  if (isLoading) {
    return (
      <div className={`flex items-center justify-center h-screen ${isDark ? 'bg-[#050505]' : 'bg-slate-50'}`}>
        <div className="animate-pulse">
          <div className={`text-4xl font-black italic tracking-tighter ${isDark ? 'text-white/20' : 'text-slate-200'}`}>
            <span className="text-cyan-500/40">YUKYU</span>PRO
          </div>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  return <AppContent />;
};

// Main App component wrapped with providers
const App: React.FC = () => {
  return (
    <ThemeProvider>
      <AuthProvider>
        <AuthGate />
      </AuthProvider>
    </ThemeProvider>
  );
};

export default App;
