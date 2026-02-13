/**
 * Type Mapper - Transforms between backend (FastAPI) and frontend (React) data models
 */

import { Employee, LeaveRecord, AppData, PeriodHistory } from '../types';

// Backend response types
interface BackendEmployee {
  id?: string;
  employee_num: string;
  name: string;
  kana?: string;
  haken?: string;
  year?: number;
  granted?: number;
  used?: number;
  balance?: number;
  expired?: number;
  carry_over?: number;
  after_expiry?: number;
  status?: string;
  hire_date?: string;
  grant_date?: string;
  usage_rate?: number;
  [key: string]: any;
}

interface BackendLeaveRequest {
  id: string;
  emp_num: string;
  name?: string;
  start_date: string;
  end_date?: string;
  days_requested?: number;
  leave_type?: string;
  reason?: string;
  status: string; // PENDING, APPROVED, REJECTED
  approved_by?: string;
  created_at?: string;
  updated_at?: string;
  year?: number;
  [key: string]: any;
}

interface BackendUsageDetail {
  employee_num: string;
  name?: string;
  use_date: string;   // "YYYY-MM-DD"
  year: number;
  month: number;
  days_used: number;  // 1.0 or 0.5
  leave_type: string; // "full", "half_am", etc.
  [key: string]: any;
}

interface BackendLeaveRequestCreate {
  emp_num: string;
  name: string;
  start_date: string;
  end_date: string;
  days_requested: number;
  leave_type: string;
  reason?: string;
}

/**
 * Map a backend employee object to frontend Employee
 */
export function mapBackendEmployee(be: BackendEmployee): Employee {
  const granted = be.granted ?? 0;
  const used = be.used ?? 0;
  const expired = be.expired ?? 0;
  const bal = be.balance ?? (granted - used - expired);

  return {
    id: String(be.employee_num),
    name: be.name || '',
    nameKana: be.kana || undefined,
    client: be.haken || '',
    entryDate: be.hire_date || undefined,
    grantedTotal: granted,
    usedTotal: used,
    balance: bal,
    expiredCount: expired,
    carryOver: be.carry_over ?? undefined,
    remainingAfterExpiry: be.after_expiry ?? undefined,
    status: be.status || '在職中',
    lastSync: new Date().toISOString(),
    currentGrantedTotal: granted,
    currentUsedTotal: used,
    currentBalance: Math.min(Math.max(bal, 0), 40),
    currentExpiredCount: expired,
    historicalGrantedTotal: granted,
    historicalUsedTotal: used,
    historicalBalance: bal,
    historicalExpiredCount: expired,
  };
}

/**
 * Map a backend leave request to frontend LeaveRecord
 */
export function mapBackendLeaveRequest(be: BackendLeaveRequest): LeaveRecord {
  const isHalf = be.leave_type === 'half_am' || be.leave_type === 'half_pm' || be.leave_type === 'half';
  const days = be.days_requested ?? (isHalf ? 0.5 : 1);

  return {
    id: be.id,
    employeeId: String(be.emp_num),
    date: be.start_date,
    type: 'paid',
    duration: isHalf ? 'half' : 'full',
    note: be.reason || undefined,
    status: (be.status || 'PENDING').toLowerCase() as 'pending' | 'approved' | 'rejected',
    createdAt: be.created_at || new Date().toISOString(),
    approvedAt: be.updated_at || undefined,
    approvedBy: be.approved_by || undefined,
  };
}

/**
 * Map a frontend LeaveRecord to backend create format
 */
export function mapFrontendLeaveRequest(
  fe: { employeeId: string; date: string; type: string; duration: string; note?: string },
  employeeName: string
): BackendLeaveRequestCreate {
  const isHalf = fe.duration === 'half';

  return {
    emp_num: fe.employeeId,
    name: employeeName,
    start_date: fe.date,
    end_date: fe.date, // Single day request
    days_requested: isHalf ? 0.5 : 1,
    leave_type: isHalf ? 'half_am' : 'full_day',
    reason: fe.note || undefined,
  };
}

// Reverse lookup: granted days → elapsed months (労働基準法 第39条)
const GRANTED_TO_ELAPSED: Record<number, number> = {
  10: 6, 11: 18, 12: 30, 14: 42, 16: 54, 18: 66, 20: 78,
};

const ELAPSED_TO_PERIOD_NAME: Record<number, string> = {
  6: '初回(6ヶ月)', 18: '1年6ヶ月', 30: '2年6ヶ月',
  42: '3年6ヶ月', 54: '4年6ヶ月', 66: '5年6ヶ月', 78: '6年6ヶ月',
};

/**
 * Build periodHistory from deduped backend rows, assigning usage dates to each period.
 */
function buildPeriodHistoryFromRows(
  rows: BackendEmployee[],
  usageDates: BackendUsageDetail[],
  hireDate?: string
): PeriodHistory[] {
  const now = new Date();
  const hire = hireDate ? new Date(hireDate) : null;

  // Sort by year ascending for chronological order
  const sorted = [...rows].sort((a, b) => (a.year ?? 0) - (b.year ?? 0));

  // Build periods first to determine date ranges
  const periods = sorted.map((row, index) => {
    const granted = row.granted ?? 0;
    const used = row.used ?? 0;
    const expired = row.expired ?? 0;
    const balance = granted - used;

    // Determine elapsed months from grant_date+hire_date or from granted amount
    let elapsedMonths = 0;
    const grantDateStr = row.grant_date;

    if (hire && grantDateStr && !grantDateStr.startsWith('row-')) {
      const gd = new Date(grantDateStr);
      const diffMs = gd.getTime() - hire.getTime();
      const diffMonths = Math.round(diffMs / (1000 * 60 * 60 * 24 * 30.44));
      const validValues = [6, 18, 30, 42, 54, 66, 78];
      elapsedMonths = validValues.reduce((prev, curr) =>
        Math.abs(curr - diffMonths) < Math.abs(prev - diffMonths) ? curr : prev
      );
    } else {
      elapsedMonths = GRANTED_TO_ELAPSED[granted] ?? 78;
    }

    const periodName = ELAPSED_TO_PERIOD_NAME[elapsedMonths] ?? `${Math.floor(elapsedMonths / 12)}年${elapsedMonths % 12}ヶ月`;

    let grantDate: Date;
    if (grantDateStr && !grantDateStr.startsWith('row-')) {
      grantDate = new Date(grantDateStr);
    } else if (hire) {
      grantDate = new Date(hire.getFullYear(), hire.getMonth() + elapsedMonths, hire.getDate());
    } else {
      grantDate = new Date(row.year ?? now.getFullYear(), 7, 1);
    }

    const expiryDate = new Date(grantDate.getFullYear() + 2, grantDate.getMonth(), grantDate.getDate());
    const isExpired = expired > 0 || now >= expiryDate;
    const isCurrentPeriod = !isExpired && index === sorted.length - 1;

    return {
      periodIndex: index,
      periodName,
      elapsedMonths,
      yukyuStartDate: grantDateStr || grantDate.toISOString().split('T')[0],
      grantDate,
      expiryDate,
      granted,
      used,
      balance,
      expired,
      carryOver: row.carry_over ?? undefined,
      isExpired,
      isCurrentPeriod,
      yukyuDates: [] as string[],
      source: 'excel' as const,
      syncedAt: new Date().toISOString(),
    };
  });

  // Assign usage dates to the correct period based on date range
  for (const detail of usageDates) {
    const useDate = new Date(detail.use_date);
    const isHalf = detail.days_used < 1;
    const dateStr = isHalf ? `${detail.use_date}:half` : detail.use_date;

    // Find the period this date belongs to (date falls between grantDate and expiryDate)
    let assigned = false;
    for (let i = periods.length - 1; i >= 0; i--) {
      const p = periods[i];
      if (useDate >= p.grantDate && useDate < p.expiryDate) {
        p.yukyuDates.push(dateStr);
        assigned = true;
        break;
      }
    }
    // Fallback: assign to the most recent period
    if (!assigned && periods.length > 0) {
      periods[periods.length - 1].yukyuDates.push(dateStr);
    }
  }

  // Sort dates within each period
  for (const p of periods) {
    p.yukyuDates.sort();
  }

  return periods;
}

/**
 * Aggregate multiple backend rows (one per grant period) into a single Employee.
 * The DB stores one row per (employee_num, year, grant_date), but the UI
 * should show one card per employee with totals.
 *
 * DEDUP: The DB may have duplicate rows for the same period (one with
 * grant_date=null and one with the actual date). We deduplicate by year,
 * preferring the row with a real grant_date.
 */
function aggregateEmployeeRows(rows: BackendEmployee[], usageDates: BackendUsageDetail[]): Employee {
  // Step 1: Deduplicate by year - prefer rows with grant_date
  const byYear = new Map<number, BackendEmployee>();
  for (const row of rows) {
    const yr = row.year ?? 0;
    const existing = byYear.get(yr);
    if (!existing) {
      byYear.set(yr, row);
    } else {
      // Prefer the row WITH a real grant_date
      const existingHasDate = existing.grant_date && !existing.grant_date.startsWith('row-');
      const newHasDate = row.grant_date && !row.grant_date.startsWith('row-');
      if (newHasDate && !existingHasDate) {
        byYear.set(yr, row);
      } else if (newHasDate && existingHasDate) {
        // Both have dates - keep the one with more used (more complete data)
        if ((row.used ?? 0) > (existing.used ?? 0)) {
          byYear.set(yr, row);
        }
      }
    }
  }

  // Step 2: Find the most recent period for basic info
  const dedupedRows = Array.from(byYear.values());
  dedupedRows.sort((a, b) => (b.year ?? 0) - (a.year ?? 0));
  const latest = dedupedRows[0];

  // Step 3: Build periodHistory first (needed to determine active vs expired)
  const hireDate = latest.hire_date || undefined;
  const periodHistory = buildPeriodHistoryFromRows(dedupedRows, usageDates, hireDate);

  // Step 4: Calculate current (active only) vs historical (all) totals
  let histGranted = 0, histUsed = 0, histExpired = 0;
  let currGranted = 0, currUsed = 0;

  for (const p of periodHistory) {
    histGranted += p.granted;
    histUsed += p.used;
    histExpired += p.expired;
    if (!p.isExpired) {
      currGranted += p.granted;
      currUsed += p.used;
    }
  }

  const currBalance = currGranted - currUsed;
  const histBalance = histGranted - histUsed - histExpired;

  return {
    id: String(latest.employee_num),
    name: latest.name || '',
    nameKana: latest.kana || undefined,
    client: latest.haken || '',
    entryDate: hireDate,
    // Card displays CURRENT (active periods only)
    grantedTotal: currGranted,
    usedTotal: currUsed,
    balance: Math.min(Math.max(currBalance, 0), 40),
    expiredCount: histExpired,
    carryOver: latest.carry_over ?? undefined,
    remainingAfterExpiry: latest.after_expiry ?? undefined,
    status: latest.status || '在職中',
    lastSync: new Date().toISOString(),
    periodHistory,
    currentGrantedTotal: currGranted,
    currentUsedTotal: currUsed,
    currentBalance: Math.min(Math.max(currBalance, 0), 40),
    currentExpiredCount: histExpired,
    historicalGrantedTotal: histGranted,
    historicalUsedTotal: histUsed,
    historicalBalance: histBalance,
    historicalExpiredCount: histExpired,
  };
}

/**
 * Map arrays of backend employees and leave requests to AppData.
 * Aggregates multiple grant-period rows into one Employee per employee_num.
 * Distributes usage details (individual dates) into each employee's periods.
 */
export function mapToAppData(
  backendEmployees: BackendEmployee[],
  backendRecords: BackendLeaveRequest[],
  usageDetails: BackendUsageDetail[] = []
): AppData {
  // Group backend rows by employee_num
  const empGroups = new Map<string, BackendEmployee[]>();
  for (const be of backendEmployees) {
    const key = String(be.employee_num);
    const group = empGroups.get(key) || [];
    group.push(be);
    empGroups.set(key, group);
  }

  // Group usage details by employee_num
  const usageGroups = new Map<string, BackendUsageDetail[]>();
  for (const ud of usageDetails) {
    const key = String(ud.employee_num);
    const group = usageGroups.get(key) || [];
    group.push(ud);
    usageGroups.set(key, group);
  }

  // Aggregate each group into a single Employee with usage dates in periods
  const employees = Array.from(empGroups.entries()).map(([empNum, rows]) => {
    const empUsage = usageGroups.get(empNum) || [];
    return aggregateEmployeeRows(rows, empUsage);
  });

  return {
    employees,
    records: backendRecords.map(mapBackendLeaveRequest),
    config: {
      companyName: 'UNS Corporation',
      fiscalYearStart: '04-01',
    },
  };
}

export type { BackendEmployee, BackendLeaveRequest, BackendLeaveRequestCreate, BackendUsageDetail };
