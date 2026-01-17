/**
 * Settings Page Module
 * Configuracion del usuario y sistema
 * @version 1.0.0
 */

import { API_BASE_URL } from '../config/constants.js';

// ========================================
// STATE
// ========================================

let isInitialized = false;
let systemSnapshot = null;

// ========================================
// INITIALIZATION
// ========================================

/**
 * Initialize settings page
 */
export function init() {
    if (isInitialized) return;
    isInitialized = true;
}

// ========================================
// SYSTEM SNAPSHOT
// ========================================

/**
 * Load system snapshot
 */
export async function loadSnapshot() {
    try {
        const res = await fetch(`${API_BASE_URL}/system/snapshot`);
        const json = await res.json();

        if (json.snapshot) {
            systemSnapshot = json.snapshot;
            renderSnapshot(systemSnapshot);
            showToast('success', 'System snapshot updated');
        }
    } catch (e) {
        showToast('error', 'Failed to load snapshot');
    }
}

/**
 * Render system snapshot
 * @param {Object} snapshot
 */
function renderSnapshot(snapshot) {
    const updates = {
        'sys-db-size': snapshot.database_size_kb.toFixed(1) + ' KB',
        'sys-emp-count': snapshot.employees_count,
        'sys-health': snapshot.health_status
    };

    Object.entries(updates).forEach(([id, value]) => {
        const el = document.getElementById(id);
        if (el) {
            el.textContent = value;
            if (id === 'sys-health') {
                el.style.color = value === 'HEALTHY' ? 'var(--success)' : 'var(--danger)';
            }
        }
    });
}

/**
 * Get current snapshot
 * @returns {Object|null}
 */
export function getSnapshot() {
    return systemSnapshot;
}

// ========================================
// AUDIT LOG
// ========================================

/**
 * View audit log
 */
export async function viewAuditLog() {
    showLoading();

    try {
        const res = await fetch(`${API_BASE_URL}/system/audit-log?limit=50`);
        const json = await res.json();

        let content = '<div style="max-height: 400px; overflow-y: auto;">';

        if (json.entries && json.entries.length > 0) {
            content += json.entries.map(e => {
                const safeAction = escapeHtml(e.action);
                const safeEntityType = escapeHtml(e.entity_type);
                const safeEntityId = escapeHtml(e.entity_id || '-');
                const safeTimestamp = escapeHtml(e.timestamp?.slice(0, 19) || '');

                return `
                    <div style="padding: 0.5rem; background: rgba(255,255,255,0.03); margin-bottom: 0.25rem; border-radius: 4px; font-family: monospace; font-size: 0.8rem;">
                        <span style="color: var(--primary);">[${safeAction}]</span>
                        <span style="color: var(--muted);">${safeEntityType}/${safeEntityId}</span>
                        <span style="color: #64748b; float: right;">${safeTimestamp}</span>
                    </div>
                `;
            }).join('');
        } else {
            content += '<div style="text-align: center; padding: 2rem; color: var(--muted);">No audit log entries</div>';
        }

        content += '</div>';

        // Show in modal
        showModal('Audit Log', content);
    } catch (e) {
        showToast('error', 'Failed to load audit log');
    } finally {
        hideLoading();
    }
}

// ========================================
// BACKUP MANAGEMENT
// ========================================

/**
 * View backup list
 */
export async function viewBackups() {
    showLoading();

    try {
        const res = await fetch(`${API_BASE_URL}/system/backup/list`);
        const json = await res.json();

        const backups = json.backups || [];

        if (backups.length === 0) {
            showModal('Backups', '<div style="text-align: center; padding: 2rem; color: var(--muted);">No backups available</div>');
            return;
        }

        const listHtml = backups.map((b, idx) => `
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.75rem; background: rgba(255,255,255,0.05); border-radius: 8px; margin-bottom: 0.5rem;">
                <div>
                    <div style="font-weight: 600;">${escapeHtml(b.filename)}</div>
                    <div style="font-size: 0.8rem; color: var(--muted);">
                        ${escapeHtml(b.created_at)} | ${(b.size_kb / 1024).toFixed(2)} MB
                    </div>
                </div>
                <button class="btn btn-glass btn-sm backup-restore-btn" data-backup-index="${idx}">
                    Restore
                </button>
            </div>
        `).join('');

        const content = `
            <div style="max-height: 400px; overflow-y: auto;">
                ${listHtml}
            </div>
            <div style="margin-top: 1rem;">
                <button class="btn btn-primary backup-create-btn" style="width: 100%;">
                    Create New Backup
                </button>
            </div>
        `;

        showModal('Backups', content);

        // Attach listeners after modal is shown
        setTimeout(() => {
            document.querySelectorAll('.backup-restore-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    const idx = parseInt(btn.dataset.backupIndex, 10);
                    if (backups[idx]) {
                        restoreBackup(backups[idx].filename);
                    }
                });
            });

            document.querySelector('.backup-create-btn')?.addEventListener('click', () => {
                createBackup();
                closeModal();
            });
        }, 100);

    } catch (e) {
        showToast('error', 'Failed to load backups');
    } finally {
        hideLoading();
    }
}

/**
 * Create a new backup
 */
export async function createBackup() {
    showLoading();

    try {
        const res = await fetch(`${API_BASE_URL}/system/backup/create`, {
            method: 'POST'
        });
        const json = await res.json();

        if (json.status === 'success') {
            showToast('success', `Backup created: ${json.filename}`);
        } else {
            throw new Error(json.detail || 'Failed to create backup');
        }
    } catch (e) {
        showToast('error', e.message);
    } finally {
        hideLoading();
    }
}

/**
 * Restore a backup
 * @param {string} filename
 */
export async function restoreBackup(filename) {
    if (!confirm(`Are you sure you want to restore backup: ${filename}? This will overwrite current data.`)) {
        return;
    }

    showLoading();

    try {
        const res = await fetch(`${API_BASE_URL}/system/backup/restore`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename })
        });
        const json = await res.json();

        if (json.status === 'success') {
            showToast('success', 'Backup restored successfully');
            // Reload page to refresh data
            setTimeout(() => window.location.reload(), 1500);
        } else {
            throw new Error(json.detail || 'Failed to restore backup');
        }
    } catch (e) {
        showToast('error', e.message);
    } finally {
        hideLoading();
    }
}

// ========================================
// THEME SETTINGS
// ========================================

/**
 * Toggle theme
 */
export function toggleTheme() {
    if (window.App?.theme?.toggle) {
        window.App.theme.toggle();
    }
}

/**
 * Get current theme
 * @returns {string}
 */
export function getCurrentTheme() {
    return localStorage.getItem('yukyu-theme') || 'dark';
}

// ========================================
// LANGUAGE SETTINGS
// ========================================

/**
 * Set language
 * @param {string} locale
 */
export async function setLanguage(locale) {
    if (window.App?.i18n?.setLocale) {
        await window.App.i18n.setLocale(locale);
    }
}

/**
 * Get current language
 * @returns {string}
 */
export function getCurrentLanguage() {
    return localStorage.getItem('yukyu-locale') || 'ja';
}

// ========================================
// DATA MANAGEMENT
// ========================================

/**
 * Clear local cache
 */
export function clearCache() {
    // Clear localStorage (except theme and locale)
    const theme = localStorage.getItem('yukyu-theme');
    const locale = localStorage.getItem('yukyu-locale');

    localStorage.clear();

    if (theme) localStorage.setItem('yukyu-theme', theme);
    if (locale) localStorage.setItem('yukyu-locale', locale);

    // Clear IndexedDB if available
    if (window.indexedDB) {
        window.indexedDB.deleteDatabase('yukyu-offline');
    }

    showToast('success', 'Cache cleared');
}

/**
 * Export all data
 */
export async function exportAllData() {
    showLoading();

    try {
        const res = await fetch(`${API_BASE_URL}/export/all`, {
            method: 'POST'
        });
        const json = await res.json();

        if (json.status === 'success' && json.download_url) {
            window.open(json.download_url, '_blank');
            showToast('success', 'Data exported successfully');
        }
    } catch (e) {
        showToast('error', 'Failed to export data');
    } finally {
        hideLoading();
    }
}

// ========================================
// HELPERS
// ========================================

function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    const div = document.createElement('div');
    div.textContent = String(str);
    return div.innerHTML;
}

function showLoading() {
    if (window.App?.ui?.showLoading) {
        window.App.ui.showLoading();
    }
}

function hideLoading() {
    if (window.App?.ui?.hideLoading) {
        window.App.ui.hideLoading();
    }
}

function showToast(type, message) {
    if (window.App?.ui?.showToast) {
        window.App.ui.showToast(type, message);
    }
}

function showModal(title, content) {
    const modalTitle = document.getElementById('modal-title');
    const modalContent = document.getElementById('modal-content');
    const modal = document.getElementById('detail-modal');

    if (modalTitle) modalTitle.textContent = title;
    if (modalContent) modalContent.innerHTML = content;
    if (modal) modal.classList.add('active');
}

function closeModal() {
    const modal = document.getElementById('detail-modal');
    if (modal) modal.classList.remove('active');
}

/**
 * Cleanup
 */
export function cleanup() {
    systemSnapshot = null;
}

// Export default
export default {
    init,
    loadSnapshot,
    getSnapshot,
    viewAuditLog,
    viewBackups,
    createBackup,
    restoreBackup,
    toggleTheme,
    getCurrentTheme,
    setLanguage,
    getCurrentLanguage,
    clearCache,
    exportAllData,
    cleanup
};
