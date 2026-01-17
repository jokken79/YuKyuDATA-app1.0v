/**
 * Offline Storage Module
 * Provides IndexedDB-based offline data persistence for YuKyuDATA PWA
 * @module offline-storage
 */

const DB_NAME = 'YuKyuOfflineDB';
const DB_VERSION = 2;

// Store definitions
const STORES = {
    employees: { keyPath: 'id', indexes: ['employee_num', 'year', 'haken'] },
    genzai: { keyPath: 'id', indexes: ['employee_num', 'status'] },
    ukeoi: { keyPath: 'id', indexes: ['employee_num', 'status'] },
    staff: { keyPath: 'id', indexes: ['employee_num', 'status'] },
    leaveRequests: { keyPath: 'id', indexes: ['employee_num', 'status', 'created_at'] },
    usageDetails: { keyPath: 'id', indexes: ['employee_num', 'use_date'] },
    pendingSync: { keyPath: 'id', autoIncrement: true, indexes: ['type', 'timestamp'] },
    metadata: { keyPath: 'key' }
};

/**
 * OfflineStorage class - manages IndexedDB operations for offline support
 */
export class OfflineStorage {
    constructor() {
        /** @type {IDBDatabase|null} */
        this.db = null;
        this._initPromise = null;
        this._isOnline = navigator.onLine;

        // Set up online/offline listeners
        this._setupNetworkListeners();
    }

    /**
     * Initialize the IndexedDB database
     * @returns {Promise<IDBDatabase>}
     */
    async init() {
        if (this.db) return this.db;
        if (this._initPromise) return this._initPromise;

        this._initPromise = new Promise((resolve, reject) => {
            const request = indexedDB.open(DB_NAME, DB_VERSION);

            request.onerror = () => {
                console.error('[OfflineStorage] Failed to open database:', request.error);
                reject(request.error);
            };

            request.onsuccess = () => {
                this.db = request.result;
                // Database opened successfully
                resolve(this.db);
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                // Upgrading database schema

                // Create stores
                Object.entries(STORES).forEach(([storeName, config]) => {
                    if (!db.objectStoreNames.contains(storeName)) {
                        const storeOptions = {
                            keyPath: config.keyPath
                        };
                        if (config.autoIncrement) {
                            storeOptions.autoIncrement = true;
                        }
                        const store = db.createObjectStore(storeName, storeOptions);

                        // Create indexes
                        if (config.indexes) {
                            config.indexes.forEach(indexName => {
                                store.createIndex(indexName, indexName, { unique: false });
                            });
                        }

                        // Store created
                    }
                });
            };
        });

        return this._initPromise;
    }

    /**
     * Set up network status listeners
     * @private
     */
    _setupNetworkListeners() {
        window.addEventListener('online', () => {
            this._isOnline = true;
            // Connection restored
            this._dispatchNetworkEvent('online');
            this.syncPending();
        });

        window.addEventListener('offline', () => {
            this._isOnline = false;
            // Connection lost
            this._dispatchNetworkEvent('offline');
        });
    }

    /**
     * Dispatch custom network status event
     * @param {string} status - 'online' or 'offline'
     * @private
     */
    _dispatchNetworkEvent(status) {
        const event = new CustomEvent('yukyu-network-status', {
            detail: { status, timestamp: Date.now() }
        });
        window.dispatchEvent(event);
    }

    /**
     * Check if currently online
     * @returns {boolean}
     */
    isOnline() {
        return this._isOnline;
    }

    /**
     * Get a transaction for a store
     * @param {string} storeName - Store name
     * @param {IDBTransactionMode} mode - 'readonly' or 'readwrite'
     * @returns {Promise<IDBObjectStore>}
     * @private
     */
    async _getStore(storeName, mode = 'readonly') {
        await this.init();
        const tx = this.db.transaction(storeName, mode);
        return tx.objectStore(storeName);
    }

    // ==================== EMPLOYEES ====================

    /**
     * Save employees to IndexedDB
     * @param {Array} employees - Array of employee records
     * @param {number} year - Fiscal year
     * @returns {Promise<void>}
     */
    async saveEmployees(employees, year) {
        await this.init();
        const tx = this.db.transaction('employees', 'readwrite');
        const store = tx.objectStore('employees');

        // Clear old data for this year first
        const yearIndex = store.index('year');
        const yearRange = IDBKeyRange.only(year);
        const cursorRequest = yearIndex.openCursor(yearRange);

        await new Promise((resolve, reject) => {
            cursorRequest.onsuccess = (event) => {
                const cursor = event.target.result;
                if (cursor) {
                    cursor.delete();
                    cursor.continue();
                } else {
                    resolve();
                }
            };
            cursorRequest.onerror = () => reject(cursorRequest.error);
        });

        // Add new data
        for (const emp of employees) {
            await new Promise((resolve, reject) => {
                const req = store.put(emp);
                req.onsuccess = () => resolve();
                req.onerror = () => reject(req.error);
            });
        }

        // Update sync metadata
        await this.setMetadata('lastSync', Date.now());
        await this.setMetadata('employeesYear', year);

        // Employees saved for year
    }

    /**
     * Get employees from IndexedDB
     * @param {number|null} year - Filter by year (optional)
     * @returns {Promise<Array>}
     */
    async getEmployees(year = null) {
        const store = await this._getStore('employees');

        return new Promise((resolve, reject) => {
            let request;

            if (year) {
                const index = store.index('year');
                request = index.getAll(IDBKeyRange.only(year));
            } else {
                request = store.getAll();
            }

            request.onsuccess = () => resolve(request.result || []);
            request.onerror = () => reject(request.error);
        });
    }

    // ==================== GENZAI/UKEOI/STAFF ====================

    /**
     * Save registry data (genzai, ukeoi, or staff)
     * @param {string} type - 'genzai', 'ukeoi', or 'staff'
     * @param {Array} records - Array of records
     * @returns {Promise<void>}
     */
    async saveRegistry(type, records) {
        if (!['genzai', 'ukeoi', 'staff'].includes(type)) {
            throw new Error(`Invalid registry type: ${type}`);
        }

        await this.init();
        const tx = this.db.transaction(type, 'readwrite');
        const store = tx.objectStore(type);

        // Clear existing data
        await new Promise((resolve, reject) => {
            const req = store.clear();
            req.onsuccess = () => resolve();
            req.onerror = () => reject(req.error);
        });

        // Add new data
        for (const record of records) {
            await new Promise((resolve, reject) => {
                const req = store.put(record);
                req.onsuccess = () => resolve();
                req.onerror = () => reject(req.error);
            });
        }

        await this.setMetadata(`${type}LastSync`, Date.now());
        // Registry records saved
    }

    /**
     * Get registry data
     * @param {string} type - 'genzai', 'ukeoi', or 'staff'
     * @returns {Promise<Array>}
     */
    async getRegistry(type) {
        if (!['genzai', 'ukeoi', 'staff'].includes(type)) {
            throw new Error(`Invalid registry type: ${type}`);
        }

        const store = await this._getStore(type);

        return new Promise((resolve, reject) => {
            const request = store.getAll();
            request.onsuccess = () => resolve(request.result || []);
            request.onerror = () => reject(request.error);
        });
    }

    // ==================== LEAVE REQUESTS ====================

    /**
     * Save leave requests
     * @param {Array} requests - Array of leave request records
     * @returns {Promise<void>}
     */
    async saveLeaveRequests(requests) {
        await this.init();
        const tx = this.db.transaction('leaveRequests', 'readwrite');
        const store = tx.objectStore('leaveRequests');

        // Clear and repopulate
        await new Promise((resolve, reject) => {
            const req = store.clear();
            req.onsuccess = () => resolve();
            req.onerror = () => reject(req.error);
        });

        for (const request of requests) {
            await new Promise((resolve, reject) => {
                const req = store.put(request);
                req.onsuccess = () => resolve();
                req.onerror = () => reject(req.error);
            });
        }

        await this.setMetadata('leaveRequestsLastSync', Date.now());
        // Leave requests saved
    }

    /**
     * Get leave requests
     * @param {string|null} status - Filter by status (optional)
     * @returns {Promise<Array>}
     */
    async getLeaveRequests(status = null) {
        const store = await this._getStore('leaveRequests');

        return new Promise((resolve, reject) => {
            let request;

            if (status) {
                const index = store.index('status');
                request = index.getAll(IDBKeyRange.only(status));
            } else {
                request = store.getAll();
            }

            request.onsuccess = () => resolve(request.result || []);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Add a leave request to pending sync queue (for offline submission)
     * @param {Object} requestData - Leave request data
     * @returns {Promise<number>} - Pending request ID
     */
    async addPendingLeaveRequest(requestData) {
        const store = await this._getStore('pendingSync', 'readwrite');

        return new Promise((resolve, reject) => {
            const pendingItem = {
                type: 'leaveRequest',
                action: 'create',
                data: requestData,
                timestamp: Date.now(),
                status: 'pending'
            };

            const req = store.add(pendingItem);
            req.onsuccess = () => {
                // Pending leave request added
                resolve(req.result);
            };
            req.onerror = () => reject(req.error);
        });
    }

    // ==================== USAGE DETAILS ====================

    /**
     * Save usage details
     * @param {Array} details - Array of usage detail records
     * @returns {Promise<void>}
     */
    async saveUsageDetails(details) {
        await this.init();
        const tx = this.db.transaction('usageDetails', 'readwrite');
        const store = tx.objectStore('usageDetails');

        // Clear and repopulate
        await new Promise((resolve, reject) => {
            const req = store.clear();
            req.onsuccess = () => resolve();
            req.onerror = () => reject(req.error);
        });

        for (const detail of details) {
            await new Promise((resolve, reject) => {
                const req = store.put(detail);
                req.onsuccess = () => resolve();
                req.onerror = () => reject(req.error);
            });
        }

        // Usage details saved
    }

    /**
     * Get usage details for an employee
     * @param {string} employeeNum - Employee number
     * @returns {Promise<Array>}
     */
    async getUsageDetails(employeeNum) {
        const store = await this._getStore('usageDetails');

        return new Promise((resolve, reject) => {
            const index = store.index('employee_num');
            const request = index.getAll(IDBKeyRange.only(employeeNum));

            request.onsuccess = () => resolve(request.result || []);
            request.onerror = () => reject(request.error);
        });
    }

    // ==================== PENDING SYNC ====================

    /**
     * Get all pending sync items
     * @returns {Promise<Array>}
     */
    async getPendingSync() {
        const store = await this._getStore('pendingSync');

        return new Promise((resolve, reject) => {
            const request = store.getAll();
            request.onsuccess = () => resolve(request.result || []);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Get pending sync count
     * @returns {Promise<number>}
     */
    async getPendingSyncCount() {
        const store = await this._getStore('pendingSync');

        return new Promise((resolve, reject) => {
            const request = store.count();
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Mark a pending item as synced (remove from queue)
     * @param {number} id - Pending item ID
     * @returns {Promise<void>}
     */
    async removePendingItem(id) {
        const store = await this._getStore('pendingSync', 'readwrite');

        return new Promise((resolve, reject) => {
            const request = store.delete(id);
            request.onsuccess = () => {
                // Pending item removed
                resolve();
            };
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Sync all pending items to server
     * @returns {Promise<{success: number, failed: number}>}
     */
    async syncPending() {
        if (!this._isOnline) {
            // Cannot sync - offline
            return { success: 0, failed: 0 };
        }

        const pendingItems = await this.getPendingSync();

        if (pendingItems.length === 0) {
            // No pending items to sync
            return { success: 0, failed: 0 };
        }

        // Syncing pending items

        let success = 0;
        let failed = 0;

        for (const item of pendingItems) {
            try {
                if (item.type === 'leaveRequest' && item.action === 'create') {
                    const response = await fetch('/api/leave-requests', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(item.data)
                    });

                    if (response.ok) {
                        await this.removePendingItem(item.id);
                        success++;
                    } else {
                        failed++;
                    }
                }
            } catch (error) {
                console.error('[OfflineStorage] Failed to sync item:', item.id, error);
                failed++;
            }
        }

        // Sync complete

        // Dispatch sync complete event
        window.dispatchEvent(new CustomEvent('yukyu-sync-complete', {
            detail: { success, failed }
        }));

        return { success, failed };
    }

    // ==================== METADATA ====================

    /**
     * Set a metadata value
     * @param {string} key - Metadata key
     * @param {any} value - Metadata value
     * @returns {Promise<void>}
     */
    async setMetadata(key, value) {
        const store = await this._getStore('metadata', 'readwrite');

        return new Promise((resolve, reject) => {
            const request = store.put({ key, value });
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Get a metadata value
     * @param {string} key - Metadata key
     * @returns {Promise<any>}
     */
    async getMetadata(key) {
        const store = await this._getStore('metadata');

        return new Promise((resolve, reject) => {
            const request = store.get(key);
            request.onsuccess = () => {
                resolve(request.result ? request.result.value : null);
            };
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Get last sync timestamp
     * @returns {Promise<Date|null>}
     */
    async getLastSync() {
        const timestamp = await this.getMetadata('lastSync');
        return timestamp ? new Date(timestamp) : null;
    }

    // ==================== CACHE MANAGEMENT ====================

    /**
     * Clear all offline data
     * @returns {Promise<void>}
     */
    async clearAll() {
        await this.init();

        const storeNames = Object.keys(STORES);
        const tx = this.db.transaction(storeNames, 'readwrite');

        for (const storeName of storeNames) {
            const store = tx.objectStore(storeName);
            await new Promise((resolve, reject) => {
                const req = store.clear();
                req.onsuccess = () => resolve();
                req.onerror = () => reject(req.error);
            });
        }

        // All data cleared
    }

    /**
     * Get storage statistics
     * @returns {Promise<Object>}
     */
    async getStats() {
        await this.init();

        const stats = {
            lastSync: await this.getLastSync(),
            isOnline: this._isOnline,
            stores: {}
        };

        for (const storeName of Object.keys(STORES)) {
            const store = await this._getStore(storeName);
            stats.stores[storeName] = await new Promise((resolve) => {
                const req = store.count();
                req.onsuccess = () => resolve(req.result);
                req.onerror = () => resolve(0);
            });
        }

        return stats;
    }

    /**
     * Check if data is stale (older than threshold)
     * @param {number} maxAgeMinutes - Maximum age in minutes
     * @returns {Promise<boolean>}
     */
    async isDataStale(maxAgeMinutes = 30) {
        const lastSync = await this.getLastSync();

        if (!lastSync) return true;

        const ageMs = Date.now() - lastSync.getTime();
        const maxAgeMs = maxAgeMinutes * 60 * 1000;

        return ageMs > maxAgeMs;
    }
}

// Singleton instance
export const offlineStorage = new OfflineStorage();

// Export for ES modules
export default offlineStorage;

/**
 * Network Status Manager - provides UI integration for online/offline status
 */
export class NetworkStatusManager {
    constructor() {
        this.indicator = null;
        this.toast = null;
        this._init();
    }

    _init() {
        // Create status indicator
        this._createIndicator();

        // Create toast container
        this._createToast();

        // Listen for network events
        window.addEventListener('yukyu-network-status', (e) => {
            this._updateIndicator(e.detail.status);
            this._showStatusToast(e.detail.status);
        });

        // Set initial status
        this._updateIndicator(navigator.onLine ? 'online' : 'offline');
    }

    _createIndicator() {
        // Check if indicator already exists
        if (document.getElementById('network-status-indicator')) return;

        this.indicator = document.createElement('div');
        this.indicator.id = 'network-status-indicator';
        this.indicator.className = 'network-status-indicator';
        this.indicator.innerHTML = `
            <span class="status-dot"></span>
            <span class="status-text">Online</span>
        `;

        // Add styles
        const style = document.createElement('style');
        style.textContent = `
            .network-status-indicator {
                position: fixed;
                top: 12px;
                right: 12px;
                display: flex;
                align-items: center;
                gap: 6px;
                padding: 6px 12px;
                background: rgba(30, 41, 59, 0.9);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.1);
                font-size: 12px;
                font-weight: 500;
                z-index: 9999;
                transition: all 0.3s ease;
                opacity: 0.8;
            }

            .network-status-indicator:hover {
                opacity: 1;
            }

            .network-status-indicator .status-dot {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                transition: background-color 0.3s ease;
            }

            .network-status-indicator.online .status-dot {
                background: #10b981;
                box-shadow: 0 0 8px rgba(16, 185, 129, 0.6);
            }

            .network-status-indicator.online .status-text {
                color: #10b981;
            }

            .network-status-indicator.offline .status-dot {
                background: #f59e0b;
                animation: pulse-offline 2s infinite;
            }

            .network-status-indicator.offline .status-text {
                color: #f59e0b;
            }

            @keyframes pulse-offline {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }

            .network-toast {
                position: fixed;
                bottom: 20px;
                left: 50%;
                transform: translateX(-50%) translateY(100px);
                padding: 12px 24px;
                border-radius: 12px;
                font-weight: 600;
                font-size: 14px;
                z-index: 10000;
                transition: transform 0.3s ease;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
            }

            .network-toast.show {
                transform: translateX(-50%) translateY(0);
            }

            .network-toast.online {
                background: linear-gradient(135deg, #10b981, #059669);
                color: white;
            }

            .network-toast.offline {
                background: linear-gradient(135deg, #f59e0b, #d97706);
                color: white;
            }
        `;

        document.head.appendChild(style);
        document.body.appendChild(this.indicator);
    }

    _createToast() {
        if (document.getElementById('network-toast')) return;

        this.toast = document.createElement('div');
        this.toast.id = 'network-toast';
        this.toast.className = 'network-toast';
        document.body.appendChild(this.toast);
    }

    _updateIndicator(status) {
        if (!this.indicator) return;

        this.indicator.classList.remove('online', 'offline');
        this.indicator.classList.add(status);

        const textEl = this.indicator.querySelector('.status-text');
        if (textEl) {
            textEl.textContent = status === 'online' ? 'Online' : 'Offline';
        }
    }

    _showStatusToast(status) {
        if (!this.toast) return;

        this.toast.classList.remove('online', 'offline', 'show');
        this.toast.classList.add(status);

        if (status === 'online') {
            this.toast.textContent = 'Connection restored';
        } else {
            this.toast.textContent = 'You are offline';
        }

        // Show toast
        setTimeout(() => this.toast.classList.add('show'), 10);

        // Hide after 3 seconds
        setTimeout(() => {
            this.toast.classList.remove('show');
        }, 3000);
    }
}

// Create network status manager on DOM ready
if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', () => {
        // Initialize offline storage
        offlineStorage.init().catch(console.error);

        // Initialize network status manager
        new NetworkStatusManager();
    });
}
