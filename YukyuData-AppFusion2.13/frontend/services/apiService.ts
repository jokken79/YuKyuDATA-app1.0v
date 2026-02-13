/**
 * API Service - Replaces localStorage db.ts with backend API calls
 * Maintains the same public interface for minimal component changes
 */

import { apiClient } from './apiClient';
import { AppData, Employee, LeaveRecord } from '../types';
import {
  mapBackendEmployee,
  mapBackendLeaveRequest,
  mapFrontendLeaveRequest,
  mapToAppData,
  BackendEmployee,
  BackendLeaveRequest,
  BackendUsageDetail,
} from './typeMapper';

// Local cache key
const CACHE_KEY = 'yukyu_api_cache';

function getCachedData(): AppData | null {
  try {
    const raw = localStorage.getItem(CACHE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function setCachedData(data: AppData): void {
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify(data));
  } catch {
    // Ignore quota errors for cache
  }
}

export const api = {
  /**
   * Load all data from backend (employees + leave requests)
   * Falls back to cache if backend is unavailable
   */
  async loadData(year?: number): Promise<AppData> {
    try {
      // Fetch employees, leave requests, and usage details in parallel
      const yearParam = year ? `?year=${year}` : '';
      const [empResponse, leaveResponse, usageResponse] = await Promise.all([
        apiClient.fetch(`/employees${yearParam}`),
        apiClient.fetch('/leave-requests'),
        apiClient.fetch('/yukyu/usage-details'),
      ]);

      if (!empResponse.ok || !leaveResponse.ok) {
        throw new Error('API request failed');
      }

      const empData = await empResponse.json();
      const leaveData = await leaveResponse.json();
      const usageData = usageResponse.ok ? await usageResponse.json() : { data: [] };

      const employees: BackendEmployee[] = empData.data || [];
      const records: BackendLeaveRequest[] = leaveData.data || [];
      const usageDetails: BackendUsageDetail[] = usageData.data || [];

      const appData = mapToAppData(employees, records, usageDetails);

      // Cache the data for offline fallback
      setCachedData(appData);

      return appData;
    } catch (error) {
      console.warn('API unavailable, using cached data:', error);
      const cached = getCachedData();
      if (cached) {
        return cached;
      }
      return {
        employees: [],
        records: [],
        config: { companyName: 'UNS Corporation', fiscalYearStart: '04-01' },
      };
    }
  },

  /**
   * Get available years from backend
   */
  async getAvailableYears(): Promise<number[]> {
    try {
      const response = await apiClient.fetch('/employees');
      if (!response.ok) return [];
      const data = await response.json();
      return data.years || [];
    } catch {
      return [];
    }
  },

  /**
   * Create a new leave request
   */
  async addRecord(
    record: { employeeId: string; date: string; type: string; duration: string; note?: string },
    employeeName: string
  ): Promise<LeaveRecord | null> {
    try {
      const body = mapFrontendLeaveRequest(record, employeeName);
      const response = await apiClient.fetch('/leave-requests', {
        method: 'POST',
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || '申請に失敗しました');
      }

      const result = await response.json();
      // Return a mapped record with the new ID
      return {
        id: result.id || result.data?.id,
        employeeId: record.employeeId,
        date: record.date,
        type: record.type as 'paid' | 'unpaid' | 'special',
        duration: record.duration as 'full' | 'half',
        note: record.note,
        status: 'pending',
        createdAt: new Date().toISOString(),
      };
    } catch (error: any) {
      throw error;
    }
  },

  /**
   * Approve a single leave request
   */
  async approveRecord(
    recordId: string,
    approvedBy?: string
  ): Promise<{ success: boolean; error?: string; code?: string }> {
    try {
      const response = await apiClient.fetch(`/leave-requests/${recordId}/approve`, {
        method: 'PATCH',
        body: JSON.stringify({
          approved_by: approvedBy || 'システム',
          validate_limit: true,
        }),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        return {
          success: false,
          error: error.detail || '承認に失敗しました',
          code: error.code,
        };
      }

      return { success: true };
    } catch (error: any) {
      return { success: false, error: error.message || '承認に失敗しました' };
    }
  },

  /**
   * Reject a single leave request
   */
  async rejectRecord(recordId: string, reason?: string): Promise<boolean> {
    try {
      const response = await apiClient.fetch(`/leave-requests/${recordId}/reject`, {
        method: 'PATCH',
        body: JSON.stringify({
          rejection_reason: reason || '',
        }),
      });

      return response.ok;
    } catch {
      return false;
    }
  },

  /**
   * Approve multiple leave requests
   */
  async approveMultiple(
    recordIds: string[],
    approvedBy?: string
  ): Promise<{ succeeded: string[]; failed: Array<{ recordId: string; reason: string; code?: string }> }> {
    const results = {
      succeeded: [] as string[],
      failed: [] as Array<{ recordId: string; reason: string; code?: string }>,
    };

    // Process sequentially to respect backend validation
    for (const id of recordIds) {
      const result = await api.approveRecord(id, approvedBy);
      if (result.success) {
        results.succeeded.push(id);
      } else {
        results.failed.push({
          recordId: id,
          reason: result.error || 'Unknown error',
          code: result.code,
        });
      }
    }

    return results;
  },

  /**
   * Reject multiple leave requests
   */
  async rejectMultiple(recordIds: string[], reason?: string): Promise<number> {
    let count = 0;
    for (const id of recordIds) {
      const success = await api.rejectRecord(id, reason);
      if (success) count++;
    }
    return count;
  },

  /**
   * Delete a leave request (only pending)
   */
  async deleteRecord(recordId: string): Promise<boolean> {
    try {
      const response = await apiClient.fetch(`/leave-requests/${recordId}`, {
        method: 'DELETE',
      });
      return response.ok;
    } catch {
      return false;
    }
  },

  /**
   * Sync Excel file to backend
   */
  async syncExcel(file: File, type: 'yukyu' | 'shaintaicho'): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('type', type);

    const response = await apiClient.fetch('/data-management/upload', {
      method: 'POST',
      body: formData,
      // Don't set Content-Type - browser will set it with boundary for FormData
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'アップロードに失敗しました');
    }

    return response.json();
  },

  /**
   * Get dashboard stats from backend
   */
  async getDashboardStats(year: number): Promise<any> {
    try {
      const response = await apiClient.fetch(`/analytics/dashboard/${year}`);
      if (!response.ok) return null;
      return response.json();
    } catch {
      return null;
    }
  },

  /**
   * Get compliance check from backend
   */
  async getComplianceCheck(year: number): Promise<any> {
    try {
      const response = await apiClient.fetch(`/compliance/5day-check/${year}`);
      if (!response.ok) return null;
      return response.json();
    } catch {
      return null;
    }
  },
};
