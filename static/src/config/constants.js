/**
 * YuKyu Application Constants
 * Configuracion centralizada de la aplicacion
 * @version 1.0.0
 */

// API Configuration
export const API_BASE_URL = '/api';

export const ENDPOINTS = {
    // Employees
    EMPLOYEES: '/employees',
    EMPLOYEES_SEARCH: '/employees/search',
    EMPLOYEES_BY_TYPE: '/employees/by-type',
    EMPLOYEE_LEAVE_INFO: (empNum) => `/employees/${empNum}/leave-info`,

    // Sync
    SYNC: '/sync',
    SYNC_GENZAI: '/sync-genzai',
    SYNC_UKEOI: '/sync-ukeoi',
    SYNC_STAFF: '/sync-staff',

    // Leave Requests
    LEAVE_REQUESTS: '/leave-requests',
    LEAVE_REQUEST_APPROVE: (id) => `/leave-requests/${id}/approve`,
    LEAVE_REQUEST_REJECT: (id) => `/leave-requests/${id}/reject`,
    LEAVE_REQUEST_REVERT: (id) => `/leave-requests/${id}/revert`,

    // Compliance
    COMPLIANCE_5DAY: (year) => `/compliance/5day-check/${year}`,
    COMPLIANCE_ALERTS: '/compliance/alerts',
    COMPLIANCE_LEDGER: (year) => `/compliance/annual-ledger/${year}`,
    COMPLIANCE_EXPORT: (year) => `/compliance/export-ledger/${year}`,

    // Analytics
    ANALYTICS_DASHBOARD: (year) => `/analytics/dashboard/${year}`,
    ANALYTICS_PREDICTIONS: (year) => `/analytics/predictions/${year}`,

    // Reports
    REPORTS_MONTHLY: (year, month) => `/reports/monthly/${year}/${month}`,
    REPORTS_MONTHLY_LIST: (year) => `/reports/monthly-list/${year}`,
    REPORTS_CUSTOM: '/reports/custom',

    // Calendar
    CALENDAR_EVENTS: '/calendar/events',

    // Yukyu
    YUKYU_KPI_STATS: (year) => `/yukyu/kpi-stats/${year}`,
    YUKYU_EMPLOYEE_SUMMARY: (empNum, year) => `/yukyu/employee-summary/${empNum}/${year}`,
    YUKYU_USAGE_DETAILS: '/yukyu/usage-details',
    YUKYU_RECALCULATE: (empNum, year) => `/yukyu/recalculate/${empNum}/${year}`,

    // System
    SYSTEM_SNAPSHOT: '/system/snapshot',
    SYSTEM_AUDIT_LOG: '/system/audit-log',
    SYSTEM_BACKUP_LIST: '/system/backup/list',
    SYSTEM_BACKUP_CREATE: '/system/backup/create',
    SYSTEM_BACKUP_RESTORE: '/system/backup/restore',

    // Factories
    FACTORIES: '/factories',

    // Notifications
    NOTIFICATIONS: '/notifications',
    NOTIFICATIONS_UNREAD: '/notifications/unread-count',

    // Health
    HEALTH: '/health',
    HEALTH_DETAILED: '/health/detailed',

    // Export
    EXPORT_EXCEL: '/export/excel'
};

// View names and titles mapping
export const VIEW_TITLES = {
    'dashboard': 'Dashboard',
    'employees': 'Employee List',
    'factories': 'Factory Analysis',
    'requests': 'Leave Request Application',
    'calendar': 'Leave Calendar',
    'compliance': 'Compliance',
    'analytics': 'Detailed Analysis',
    'reports': 'Monthly Reports (21st-20th)',
    'settings': 'System Settings'
};

// Views that contain charts (need resize handling)
export const VIEWS_WITH_CHARTS = ['dashboard', 'factories', 'analytics'];

// Chart colors
export const CHART_COLORS = {
    primary: '#00d4ff',
    secondary: '#ffd93d',
    success: '#22c55e',
    warning: '#eab308',
    danger: '#ef4444',
    info: '#3b82f6',
    // Gradient for charts
    gradient: [
        'rgba(0, 212, 255, 0.8)',
        'rgba(0, 212, 255, 0.6)',
        'rgba(0, 212, 255, 0.4)',
        'rgba(0, 212, 255, 0.2)'
    ],
    // Distribution chart
    distribution: {
        high: '#22c55e',    // 10+ days
        medium: '#2563eb',  // 5-10 days
        low: '#f59e0b',     // 1-5 days
        zero: '#ef4444'     // 0 days
    },
    // Employee types
    types: {
        haken: '#2563eb',   // Dispatch
        ukeoi: '#22c55e',   // Contract
        staff: '#f59e0b'    // Staff
    }
};

// Badge CSS classes
export const BADGE_CLASSES = {
    balance: {
        critical: 'badge-critical',  // < 0
        danger: 'badge-danger',      // < 5
        success: 'badge-success'     // >= 5
    },
    type: {
        haken: 'badge-info',
        ukeoi: 'badge-success',
        staff: 'badge-warning'
    }
};

// Type labels (Japanese)
export const TYPE_LABELS = {
    haken: 'Dispatch',
    ukeoi: 'Contract',
    staff: 'Staff'
};

// Leave type labels
export const LEAVE_TYPE_LABELS = {
    full: 'Full Day',
    half_am: 'Morning Half',
    half_pm: 'Afternoon Half',
    hourly: 'Hourly'
};

// Status labels for leave requests
export const REQUEST_STATUS = {
    PENDING: 'pending',
    APPROVED: 'approved',
    REJECTED: 'rejected',
    CANCELLED: 'cancelled'
};

// Animation durations (ms)
export const ANIMATION_DURATIONS = {
    fast: 150,
    normal: 300,
    slow: 500,
    ring: 1000,
    number: 1000,
    gauge: 1500
};

// Default pagination
export const PAGINATION = {
    defaultLimit: 50,
    maxLimit: 500
};

// Cache settings
export const CACHE = {
    ttl: 5 * 60 * 1000  // 5 minutes
};

// SVG constants
export const SVG = {
    ring: {
        radius: 34,
        circumference: 2 * Math.PI * 34  // ~213.6
    },
    gauge: {
        arcLength: Math.PI * 80  // ~251.2
    }
};

// Export default config object for convenience
export default {
    API_BASE_URL,
    ENDPOINTS,
    VIEW_TITLES,
    VIEWS_WITH_CHARTS,
    CHART_COLORS,
    BADGE_CLASSES,
    TYPE_LABELS,
    LEAVE_TYPE_LABELS,
    REQUEST_STATUS,
    ANIMATION_DURATIONS,
    PAGINATION,
    CACHE,
    SVG
};
