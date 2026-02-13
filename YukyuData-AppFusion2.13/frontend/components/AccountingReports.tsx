
import React, { useState, useMemo } from 'react';
import { AppData, Employee, LeaveRecord } from '../types';
import { exportToPDF } from '../services/exportService';
import { useTheme } from '../contexts/ThemeContext';
import { getDisplayName } from '../services/nameConverter';
import { getEmployeeBalance } from '../services/balanceCalculator';
import DigitalHanko from './DigitalHanko';

interface AccountingReportsProps {
  data: AppData;
}

const AccountingReports: React.FC<AccountingReportsProps> = ({ data }) => {
  const { isDark } = useTheme();
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth() + 1);
  const [cutoffDay, setCutoffDay] = useState<15 | 20>(20); // デフォルト20日締め（21日〜20日）
  const [exporting, setExporting] = useState(false);

  // 締め日に基づいた期間（Start Date / End Date）を計算
  // 20日締めの場合：前月21日〜当月20日
  // 15日締めの場合：前月16日〜当月15日
  const period = useMemo(() => {
    const end = new Date(selectedYear, selectedMonth - 1, cutoffDay);
    const start = new Date(selectedYear, selectedMonth - 2, cutoffDay + 1);
    return { start, end };
  }, [selectedYear, selectedMonth, cutoffDay]);

  // 期間内のデータを集計: records[] + employee.yukyuDates[] (承認済のみ)
  const reportData = useMemo(() => {
    // Helper: parsear fecha string como local (sin timezone UTC)
    const parseLocalDate = (dateStr: string): Date => {
      // Normalizar "/" → "-" para fechas importadas del Excel
      const normalized = dateStr.replace(/\//g, '-');
      const parts = normalized.split('-');
      return new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
    };

    const isInPeriod = (dateStr: string): boolean => {
      const d = parseLocalDate(dateStr);
      return d >= period.start && d <= period.end;
    };

    const summary: Record<string, { emp: Employee; days: { date: string; isHalf: boolean }[]; total: number; remaining: number }> = {};
    const addedDates = new Set<string>(); // Para evitar duplicados entre records y yukyuDates

    // 1. Incluir datos desde records[] (aprobaciones de la app)
    data.records.forEach(r => {
      if (r.type !== 'paid' || r.status !== 'approved') return;
      if (!isInPeriod(r.date)) return;

      const emp = data.employees.find(e => e.id === r.employeeId);
      if (!emp) return;

      // Normalizar fecha para dedup consistente (YYYY-MM-DD)
      const normalizedDate = r.date.replace(/\//g, '-');
      const dedupKey = `${r.employeeId}:${normalizedDate}`;
      if (addedDates.has(dedupKey)) return;
      addedDates.add(dedupKey);

      if (!summary[r.employeeId]) {
        const balance = getEmployeeBalance(emp);
        summary[r.employeeId] = { emp, days: [], total: 0, remaining: balance.remaining };
      }
      const isHalf = r.duration === 'half';
      summary[r.employeeId].days.push({ date: r.date, isHalf });
      summary[r.employeeId].total += isHalf ? 0.5 : 1;
    });

    // 2. Incluir datos desde yukyuDates[] (importados del Excel)
    data.employees.forEach(emp => {
      if (!emp.yukyuDates || emp.yukyuDates.length === 0) return;

      emp.yukyuDates.forEach(dateStr => {
        const isHalf = dateStr.endsWith(':half');
        const cleanDate = isHalf ? dateStr.replace(':half', '') : dateStr;

        if (!isInPeriod(cleanDate)) return;

        const dedupKey = `${emp.id}:${cleanDate}`;
        if (addedDates.has(dedupKey)) return;
        addedDates.add(dedupKey);

        if (!summary[emp.id]) {
          const balance = getEmployeeBalance(emp);
          summary[emp.id] = { emp, days: [], total: 0, remaining: balance.remaining };
        }
        summary[emp.id].days.push({ date: cleanDate, isHalf });
        summary[emp.id].total += isHalf ? 0.5 : 1;
      });
    });

    return Object.values(summary).sort((a, b) => a.emp.client.localeCompare(b.emp.client));
  }, [data, period]);

  const handleExport = async () => {
    setExporting(true);
    await exportToPDF('accounting-report-content', `yukyu_ledger_${selectedYear}_${selectedMonth}_cutoff${cutoffDay}.pdf`);
    setExporting(false);
  };

  return (
    <div className="p-4 md:p-8 lg:p-12 space-y-6 md:space-y-8 lg:space-y-12 animate-fadeIn max-w-[1600px] mx-auto relative">
      <div className={`absolute top-0 right-0 text-[18vw] font-black select-none pointer-events-none italic tracking-tighter uppercase hidden md:block ${isDark ? 'text-white/[0.01]' : 'text-slate-900/[0.02]'}`}>帳簿</div>

      <header className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4 md:gap-8 relative z-10">
        <div className="space-y-2 md:space-y-4">
          <div className="flex items-center gap-3 md:gap-6">
            <div className="h-8 md:h-14 w-1.5 md:w-2 bg-yellow-500 shadow-[0_0_20px_#eab308] animate-pulse"></div>
            <h2 className={`text-3xl md:text-5xl lg:text-7xl font-black italic tracking-tighter ${isDark ? 'aggressive-text' : 'text-slate-800'}`}>月次元帳</h2>
          </div>
          <p className={`font-black tracking-[0.2em] md:tracking-[0.4em] ml-4 md:ml-8 uppercase text-[10px] md:text-sm ${isDark ? 'text-white/70' : 'text-slate-500'}`}>
            財務会計・給与計算サポート
          </p>
        </div>

        <div className={`flex flex-wrap gap-2 md:gap-4 p-3 md:p-4 border w-full md:w-auto ${isDark ? 'bg-[#0a0a0a] border-white/20' : 'bg-white border-slate-200 shadow-sm'}`}>
          <div className="flex flex-col gap-2">
            <label className={`text-[9px] font-black tracking-widest uppercase italic ${isDark ? 'text-white/80' : 'text-slate-500'}`}>対象月</label>
            <div className="flex gap-2">
              <select
                value={selectedYear}
                onChange={(e) => setSelectedYear(Number(e.target.value))}
                className={`border text-xs font-black p-2 outline-none focus:border-yellow-500 ${isDark ? 'bg-black border-white/20 text-white' : 'bg-white border-slate-300 text-slate-800'}`}
              >
                {Array.from({ length: new Date().getFullYear() - 2023 + 1 }, (_, i) => 2024 + i).map(y => <option key={y} value={y}>{y}年</option>)}
              </select>
              <select
                value={selectedMonth}
                onChange={(e) => setSelectedMonth(Number(e.target.value))}
                className={`border text-xs font-black p-2 outline-none focus:border-yellow-500 ${isDark ? 'bg-black border-white/20 text-white' : 'bg-white border-slate-300 text-slate-800'}`}
              >
                {Array.from({length: 12}).map((_, i) => <option key={i+1} value={i+1}>{i+1}月</option>)}
              </select>
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <label className={`text-[9px] font-black tracking-widest uppercase italic ${isDark ? 'text-white/80' : 'text-slate-500'}`}>締日設定</label>
            <div className="flex gap-2">
              <button
                onClick={() => setCutoffDay(15)}
                className={`px-4 py-2 text-[10px] font-black italic border ${cutoffDay === 15 ? 'bg-yellow-500 text-black border-yellow-500' : isDark ? 'bg-transparent text-white/80 border-white/20' : 'bg-white text-slate-500 border-slate-300'}`}
              >
                15日締 (16-15)
              </button>
              <button
                onClick={() => setCutoffDay(20)}
                className={`px-4 py-2 text-[10px] font-black italic border ${cutoffDay === 20 ? 'bg-yellow-500 text-black border-yellow-500' : isDark ? 'bg-transparent text-white/80 border-white/20' : 'bg-white text-slate-500 border-slate-300'}`}
              >
                20日締 (21-20)
              </button>
            </div>
          </div>

          <button
            onClick={handleExport}
            disabled={exporting}
            className={`ml-0 md:ml-4 px-6 md:px-10 py-2 md:py-0 text-[10px] font-black tracking-widest italic hover:bg-yellow-500 transition-all w-full md:w-auto ${isDark ? 'bg-white text-black shadow-[0_0_20px_rgba(255,255,255,0.1)]' : 'bg-slate-800 text-white shadow-lg'}`}
          >
            {exporting ? '生成中...' : '帳簿PDF出力'}
          </button>
        </div>
      </header>

      <div id="accounting-report-content" className={`border p-4 md:p-8 lg:p-12 relative overflow-hidden ${isDark ? 'bg-[#050505] border-white/20' : 'bg-white border-slate-200 shadow-sm'}`}>
        <div className="absolute top-0 right-0 w-full h-1 bg-gradient-to-r from-transparent via-yellow-500 to-transparent opacity-50"></div>

        <div className="flex flex-col md:flex-row justify-between items-start gap-4 mb-8 md:mb-16">
          <div>
            <h3 className={`text-xl md:text-3xl lg:text-4xl font-black italic tracking-tighter ${isDark ? 'text-white' : 'text-slate-800'}`}>給与計算用 有給消化報告書</h3>
            <p className="text-[10px] md:text-sm font-bold text-yellow-500/80 mt-1 md:mt-2 italic tracking-wider md:tracking-widest uppercase">
              対象期間: {period.start.toLocaleDateString('ja-JP')} ～ {period.end.toLocaleDateString('ja-JP')}
            </p>
          </div>
          <div className="text-left md:text-right">
            <div className={`text-[9px] md:text-[10px] font-black tracking-[0.3em] md:tracking-[0.5em] uppercase ${isDark ? 'text-white/70' : 'text-slate-400'}`}>セキュリティレベル</div>
            <div className="text-xs font-black text-red-600 italic">機密財務データ</div>
          </div>
        </div>

        {reportData.length > 0 ? (
          <>
            {/* Mobile card view */}
            <div className="lg:hidden space-y-4">
              {reportData.map(({ emp, days, total, remaining }) => (
                <div key={emp.id} className={`p-4 rounded-xl border ${isDark ? 'bg-white/[0.02] border-white/10' : 'bg-slate-50 border-slate-200'}`}>
                  <div className="flex justify-between items-start mb-3">
                    <div className="min-w-0 flex-1">
                      <p className={`font-black text-base italic truncate ${isDark ? 'text-white' : 'text-slate-800'}`}>{getDisplayName(emp.name)}</p>
                      <p className={`text-[10px] ${isDark ? 'text-white/50' : 'text-slate-400'}`}>{emp.client} / <span className="text-blue-500">#{emp.id}</span></p>
                    </div>
                    <div className="text-right flex-shrink-0 ml-3">
                      <div className="text-2xl font-black italic text-yellow-500">{total}<span className="text-[10px] ml-0.5">日</span></div>
                      <div className={`text-xs font-bold ${remaining <= 5 ? 'text-red-500' : isDark ? 'text-white/40' : 'text-slate-400'}`}>残{remaining}日</div>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {days.map((d, idx) => (
                      <span key={`${d.date}-${idx}`} className={`px-2 py-0.5 border text-[9px] font-black italic rounded ${isDark ? 'bg-white/5 border-white/20 text-white/60' : 'bg-white border-slate-200 text-slate-600'}`}>
                        {d.date.split('-').slice(1).join('/')}{d.isHalf && <span className="ml-0.5 text-yellow-500">(半)</span>}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
              <div className={`p-4 rounded-xl text-center ${isDark ? 'bg-white/[0.02]' : 'bg-slate-50'}`}>
                <span className={`text-[10px] font-black tracking-widest uppercase italic ${isDark ? 'text-white/70' : 'text-slate-400'}`}>期間合計 </span>
                <span className={`text-2xl font-black italic ${isDark ? 'text-white' : 'text-slate-800'}`}>
                  {reportData.reduce((s, i) => s + i.total, 0)}<span className="text-xs ml-1">日数</span>
                </span>
              </div>
            </div>

            {/* Desktop table view */}
            <div className="hidden lg:block overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className={`border-b-2 text-[10px] font-black uppercase tracking-[0.3em] ${isDark ? 'border-white/20 text-white/80' : 'border-slate-200 text-slate-500'}`}>
                    <th className="py-6 px-4">派遣先 / 工場</th>
                    <th className="py-6 px-4">社員№</th>
                    <th className="py-6 px-4">氏名</th>
                    <th className="py-6 px-4 text-center">取得日</th>
                    <th className="py-6 px-4 text-right">合計日数</th>
                    <th className="py-6 px-4 text-right">残日数</th>
                  </tr>
                </thead>
                <tbody className={`divide-y ${isDark ? 'divide-white/5' : 'divide-slate-100'}`}>
                  {reportData.map(({ emp, days, total, remaining }) => (
                    <tr key={emp.id} className={`group transition-all ${isDark ? 'hover:bg-white/[0.02]' : 'hover:bg-slate-50'}`}>
                      <td className={`py-8 px-4 font-black text-xs italic ${isDark ? 'text-white/80' : 'text-slate-500'}`}>{emp.client}</td>
                      <td className="py-8 px-4 font-black text-sm tracking-widest text-blue-500">#{emp.id}</td>
                      <td className={`py-8 px-4 font-black text-xl italic group-hover:translate-x-1 transition-transform ${isDark ? 'text-white' : 'text-slate-800'}`}>{getDisplayName(emp.name)}</td>
                      <td className="py-8 px-4 text-center">
                        <div className="flex flex-wrap justify-center gap-2">
                          {days.map((d, idx) => (
                            <span key={`${d.date}-${idx}`} className={`px-3 py-1 border text-[9px] font-black italic ${isDark ? 'bg-white/5 border-white/20 text-white/60' : 'bg-slate-100 border-slate-200 text-slate-600'}`}>
                              {d.date.split('-').slice(1).join('/')}{d.isHalf && <span className="ml-0.5 text-yellow-500">(半)</span>}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="py-8 px-4 text-right">
                        <div className="text-4xl font-black italic text-yellow-500 drop-shadow-[0_0_10px_rgba(234,179,8,0.3)]">
                          {total}<span className={`text-xs ml-1 ${isDark ? 'text-white/80' : 'text-slate-400'}`}>日</span>
                        </div>
                      </td>
                      <td className="py-8 px-4 text-right">
                        <div className={`text-2xl font-black italic ${remaining <= 5 ? 'text-red-500' : isDark ? 'text-white/60' : 'text-slate-500'}`}>
                          {remaining}<span className={`text-xs ml-1 ${isDark ? 'text-white/80' : 'text-slate-400'}`}>日</span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className={isDark ? 'bg-white/[0.02]' : 'bg-slate-50'}>
                    <td colSpan={4} className={`py-8 px-4 text-right text-[10px] font-black tracking-widest uppercase italic ${isDark ? 'text-white/70' : 'text-slate-400'}`}>期間合計</td>
                    <td className={`py-8 px-4 text-right text-4xl font-black italic ${isDark ? 'text-white' : 'text-slate-800'}`}>
                      {reportData.reduce((s, i) => s + i.total, 0)}<span className="text-xs ml-1">日数</span>
                    </td>
                    <td></td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </>
        ) : (
          <div className={`py-16 md:py-32 flex flex-col items-center justify-center space-y-4 md:space-y-6 opacity-20 border-2 border-dashed ${isDark ? 'border-white/20' : 'border-slate-300'}`}>
            <div className="text-4xl md:text-8xl italic font-black">データなし</div>
            <p className="text-xs md:text-sm font-black tracking-[0.3em] md:tracking-[0.5em] uppercase text-center px-4">
              対象期間内に有給申請レコードは<br/>存在しません
            </p>
          </div>
        )}

        <div className={`mt-8 md:mt-20 flex flex-col md:flex-row justify-between items-start md:items-end gap-6 border-t pt-6 md:pt-10 ${isDark ? 'border-white/20' : 'border-slate-200'}`}>
           <div className="space-y-4">
              <div className="flex items-center gap-3">
                 <div className="w-3 h-3 bg-blue-500"></div>
                 <span className={`text-[10px] font-black tracking-widest uppercase ${isDark ? 'text-white/80' : 'text-slate-500'}`}>生成日時: {new Date().toLocaleString()}</span>
              </div>
              <div className="flex items-center gap-3">
                 <div className="w-3 h-3 bg-red-600"></div>
                 <span className={`text-[10px] font-black tracking-widest uppercase ${isDark ? 'text-white/80' : 'text-slate-500'}`}>認証: 社内限定</span>
              </div>
           </div>
           <div className="text-right">
              <p className={`text-[10px] font-black italic mb-3 ${isDark ? 'text-white/70' : 'text-slate-400'}`}>有給PROエンジン承認済</p>
              <div className="flex items-center justify-end gap-4">
                <DigitalHanko name="承認" size={56} variant="approval" />
                <DigitalHanko name="経理" size={56} variant="approval" />
              </div>
              <p className={`text-[8px] mt-2 ${isDark ? 'text-white/40' : 'text-slate-300'}`}>
                電子印鑑 / Digital Seal
              </p>
           </div>
        </div>
      </div>
    </div>
  );
};

export default AccountingReports;
