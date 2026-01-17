/**
 * Notifications Page Module
 * Centro de notificaciones del sistema
 * @version 1.0.0
 */

import { API_BASE_URL } from '../config/constants.js';

// ========================================
// STATE
// ========================================

let isInitialized = false;
let notifications = [];
let unreadCount = 0;

// ========================================
// INITIALIZATION
// ========================================

/**
 * Initialize notifications
 */
export function init() {
    if (isInitialized) return;

    // Start polling for unread count
    startPolling();

    isInitialized = true;
}

// ========================================
// DATA LOADING
// ========================================

/**
 * Load all notifications
 */
export async function loadNotifications() {
    try {
        const res = await fetch(`${API_BASE_URL}/notifications`);
        const json = await res.json();

        notifications = json.notifications || [];
        renderNotificationsList();

        return notifications;
    } catch (e) {
        console.error('Failed to load notifications:', e);
        return [];
    }
}

/**
 * Get unread count
 * @returns {Promise<number>}
 */
export async function getUnreadCount() {
    try {
        const res = await fetch(`${API_BASE_URL}/notifications/unread-count`);
        const json = await res.json();

        unreadCount = json.count || 0;
        updateUnreadBadge();

        return unreadCount;
    } catch (e) {
        console.error('Failed to get unread count:', e);
        return 0;
    }
}

// ========================================
// ACTIONS
// ========================================

/**
 * Mark notification as read
 * @param {number} notificationId
 */
export async function markAsRead(notificationId) {
    try {
        const res = await fetch(`${API_BASE_URL}/notifications/${notificationId}/read`, {
            method: 'PATCH'
        });

        if (res.ok) {
            // Update local state
            const notification = notifications.find(n => n.id === notificationId);
            if (notification) {
                notification.is_read = true;
            }

            unreadCount = Math.max(0, unreadCount - 1);
            updateUnreadBadge();
            renderNotificationsList();
        }
    } catch (e) {
        console.error('Failed to mark as read:', e);
    }
}

/**
 * Mark all notifications as read
 */
export async function markAllAsRead() {
    try {
        const res = await fetch(`${API_BASE_URL}/notifications/read-all`, {
            method: 'PATCH'
        });

        if (res.ok) {
            // Update local state
            notifications.forEach(n => n.is_read = true);
            unreadCount = 0;
            updateUnreadBadge();
            renderNotificationsList();

            showToast('success', 'All notifications marked as read');
        }
    } catch (e) {
        console.error('Failed to mark all as read:', e);
    }
}

/**
 * Delete a notification
 * @param {number} notificationId
 */
export async function deleteNotification(notificationId) {
    try {
        const res = await fetch(`${API_BASE_URL}/notifications/${notificationId}`, {
            method: 'DELETE'
        });

        if (res.ok) {
            const notification = notifications.find(n => n.id === notificationId);
            if (notification && !notification.is_read) {
                unreadCount = Math.max(0, unreadCount - 1);
            }

            notifications = notifications.filter(n => n.id !== notificationId);
            updateUnreadBadge();
            renderNotificationsList();
        }
    } catch (e) {
        console.error('Failed to delete notification:', e);
    }
}

// ========================================
// RENDERING
// ========================================

/**
 * Render notifications list
 */
function renderNotificationsList() {
    const container = document.getElementById('notifications-list');
    if (!container) return;

    if (notifications.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">BELL</div>
                <div class="empty-text">No notifications</div>
            </div>
        `;
        return;
    }

    container.innerHTML = notifications.map(n => renderNotificationItem(n)).join('');
    attachNotificationListeners();
}

/**
 * Render single notification item
 * @param {Object} notification
 * @returns {string} HTML string
 */
function renderNotificationItem(notification) {
    const isUnread = !notification.is_read;
    const safeTitle = escapeHtml(notification.title);
    const safeMessage = escapeHtml(notification.message);
    const safeTime = formatTime(notification.created_at);

    const typeIcon = getTypeIcon(notification.type);
    const typeClass = getTypeClass(notification.type);

    return `
        <div class="notification-item ${isUnread ? 'unread' : ''}" data-id="${notification.id}">
            <div class="notification-icon ${typeClass}">
                ${typeIcon}
            </div>
            <div class="notification-content">
                <div class="notification-title">${safeTitle}</div>
                <div class="notification-message">${safeMessage}</div>
                <div class="notification-time">${safeTime}</div>
            </div>
            <div class="notification-actions">
                ${isUnread ? `
                    <button class="btn btn-ghost btn-sm mark-read-btn" data-id="${notification.id}" title="Mark as read">
                        CHECK
                    </button>
                ` : ''}
                <button class="btn btn-ghost btn-sm delete-btn" data-id="${notification.id}" title="Delete">
                    X
                </button>
            </div>
        </div>
    `;
}

/**
 * Attach event listeners to notification items
 */
function attachNotificationListeners() {
    document.querySelectorAll('.mark-read-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const id = parseInt(btn.dataset.id);
            markAsRead(id);
        });
    });

    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const id = parseInt(btn.dataset.id);
            deleteNotification(id);
        });
    });

    // Click on item to mark as read
    document.querySelectorAll('.notification-item.unread').forEach(item => {
        item.addEventListener('click', () => {
            const id = parseInt(item.dataset.id);
            markAsRead(id);
        });
    });
}

/**
 * Update unread badge in UI
 */
function updateUnreadBadge() {
    const badge = document.getElementById('notification-badge');
    if (badge) {
        if (unreadCount > 0) {
            badge.textContent = unreadCount > 99 ? '99+' : unreadCount;
            badge.style.display = 'flex';
        } else {
            badge.style.display = 'none';
        }
    }

    // Also update sidebar badge if exists
    const sidebarBadge = document.getElementById('sidebar-notification-badge');
    if (sidebarBadge) {
        if (unreadCount > 0) {
            sidebarBadge.textContent = unreadCount;
            sidebarBadge.style.display = 'inline-flex';
        } else {
            sidebarBadge.style.display = 'none';
        }
    }
}

// ========================================
// DROPDOWN
// ========================================

/**
 * Toggle notifications dropdown
 */
export function toggleDropdown() {
    const dropdown = document.getElementById('notifications-dropdown');
    if (!dropdown) return;

    const isOpen = dropdown.classList.contains('open');

    if (isOpen) {
        closeDropdown();
    } else {
        openDropdown();
    }
}

/**
 * Open dropdown
 */
export function openDropdown() {
    const dropdown = document.getElementById('notifications-dropdown');
    if (dropdown) {
        dropdown.classList.add('open');
        loadNotifications(); // Refresh
    }
}

/**
 * Close dropdown
 */
export function closeDropdown() {
    const dropdown = document.getElementById('notifications-dropdown');
    if (dropdown) {
        dropdown.classList.remove('open');
    }
}

// ========================================
// POLLING
// ========================================

let pollInterval = null;

/**
 * Start polling for unread count
 */
function startPolling() {
    // Initial fetch
    getUnreadCount();

    // Poll every 60 seconds
    pollInterval = setInterval(() => {
        getUnreadCount();
    }, 60000);
}

/**
 * Stop polling
 */
function stopPolling() {
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
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

function formatTime(timestamp) {
    if (!timestamp) return '';

    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;

    // Less than 1 hour
    if (diff < 3600000) {
        const minutes = Math.floor(diff / 60000);
        return `${minutes}m ago`;
    }

    // Less than 24 hours
    if (diff < 86400000) {
        const hours = Math.floor(diff / 3600000);
        return `${hours}h ago`;
    }

    // Less than 7 days
    if (diff < 604800000) {
        const days = Math.floor(diff / 86400000);
        return `${days}d ago`;
    }

    // Format as date
    return date.toLocaleDateString();
}

function getTypeIcon(type) {
    switch (type) {
        case 'success': return 'OK';
        case 'warning': return '!';
        case 'error': return 'X';
        case 'info':
        default: return 'i';
    }
}

function getTypeClass(type) {
    switch (type) {
        case 'success': return 'type-success';
        case 'warning': return 'type-warning';
        case 'error': return 'type-error';
        case 'info':
        default: return 'type-info';
    }
}

function showToast(type, message) {
    if (window.App?.ui?.showToast) {
        window.App.ui.showToast(type, message);
    }
}

/**
 * Get current notifications
 * @returns {Array}
 */
export function getNotifications() {
    return [...notifications];
}

/**
 * Get current unread count
 * @returns {number}
 */
export function getCurrentUnreadCount() {
    return unreadCount;
}

/**
 * Cleanup
 */
export function cleanup() {
    stopPolling();
    notifications = [];
    unreadCount = 0;
}

// Export default
export default {
    init,
    loadNotifications,
    getUnreadCount,
    markAsRead,
    markAllAsRead,
    deleteNotification,
    toggleDropdown,
    openDropdown,
    closeDropdown,
    getNotifications,
    getCurrentUnreadCount,
    cleanup
};
