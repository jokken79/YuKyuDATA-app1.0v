/**
 * Unified State Management
 * Dual API: Modern subscribe pattern + Legacy App.state proxy compatibility
 * @version 1.0.0
 */

export class UnifiedState {
    constructor(initialState = {}) {
        // Core state properties (matches App.state structure)
        this._state = {
            data: initialState.data ?? [],
            year: initialState.year ?? null,
            availableYears: initialState.availableYears ?? [],
            currentView: initialState.currentView ?? 'dashboard',
            typeFilter: initialState.typeFilter ?? 'all',
            theme: initialState.theme ?? 'dark',
            charts: initialState.charts ?? {},
            isLoading: initialState.isLoading ?? false,
            fallbackWarnedYear: initialState.fallbackWarnedYear ?? null,
            _fetchRequestId: initialState._fetchRequestId ?? 0
        };

        // Subscribers: Map<id, { callback, keys, manager }>
        this._subscribers = new Map();
        this._subscriberId = 0;

        // History for debugging
        this._history = [];
        this._maxHistorySize = 50;

        // Create legacy proxy for backward compatibility
        this._legacyProxy = this._createLegacyProxy();
    }

    /**
     * Create a proxy object for legacy App.state compatibility
     * @private
     * @returns {Proxy} Proxy that delegates to unified state
     */
    _createLegacyProxy() {
        return new Proxy({}, {
            get: (target, prop) => {
                if (prop === 'toJSON') {
                    return () => ({ ...this._state });
                }
                return this._state[prop];
            },
            set: (target, prop, value) => {
                this.set(prop, value);
                return true;
            },
            has: (target, prop) => {
                return prop in this._state;
            },
            ownKeys: () => {
                return Object.keys(this._state);
            },
            getOwnPropertyDescriptor: (target, prop) => {
                return {
                    configurable: true,
                    enumerable: true
                };
            }
        });
    }

    /**
     * Get the legacy proxy (for App.state = unifiedState.getLegacyProxy())
     * @returns {Proxy} Legacy-compatible proxy object
     */
    getLegacyProxy() {
        return this._legacyProxy;
    }

    /**
     * Get current state snapshot
     * @returns {Object} Current state object
     */
    getSnapshot() {
        return { ...this._state };
    }

    /**
     * Get a specific state value
     * @param {string} key - Property name
     * @returns {*} Property value
     */
    get(key) {
        return this._state[key];
    }

    /**
     * Set state with partial update
     * @param {string|Object} key - Property name or object with multiple properties
     * @param {*} [value] - Value (if key is string)
     */
    set(key, value) {
        const prevState = { ...this._state };

        if (typeof key === 'object') {
            // Batch update
            Object.assign(this._state, key);
        } else {
            // Single property update
            if (this._state[key] === value) {
                return; // No change, don't notify subscribers
            }
            this._state[key] = value;
        }

        // Record in history
        this._recordHistory(key, prevState, { ...this._state });

        // Notify subscribers
        this._notifySubscribers(prevState, { ...this._state }, key);
    }

    /**
     * Reset state to initial values
     * @param {Object} initialState - Initial state values
     */
    reset(initialState = {}) {
        const prevState = { ...this._state };

        this._state = {
            data: initialState.data ?? [],
            year: initialState.year ?? null,
            availableYears: initialState.availableYears ?? [],
            currentView: initialState.currentView ?? 'dashboard',
            typeFilter: initialState.typeFilter ?? 'all',
            theme: initialState.theme ?? 'dark',
            charts: initialState.charts ?? {},
            isLoading: initialState.isLoading ?? false,
            fallbackWarnedYear: initialState.fallbackWarnedYear ?? null,
            _fetchRequestId: initialState._fetchRequestId ?? 0
        };

        this._recordHistory('reset', prevState, { ...this._state });
        this._notifySubscribers(prevState, { ...this._state }, '*');
    }

    /**
     * Modern API: Subscribe to state changes
     * @param {Function} callback - Called with (newState, prevState, changedKeys)
     * @param {string[]} [keys] - Optional array of keys to watch
     * @param {string} [managerName] - Optional manager name for debugging
     * @returns {Function} Unsubscribe function
     */
    subscribe(callback, keys = null, managerName = null) {
        const id = ++this._subscriberId;
        this._subscribers.set(id, {
            callback,
            keys,
            manager: managerName
        });

        // Return unsubscribe function
        return () => {
            this._subscribers.delete(id);
        };
    }

    /**
     * Notify all subscribers of state changes
     * @private
     * @param {Object} prevState - Previous state
     * @param {Object} newState - New state
     * @param {string} changedKey - Key that changed (for history)
     */
    _notifySubscribers(prevState, newState, changedKey) {
        const changedKeys = [changedKey];

        // Detect which keys actually changed
        if (changedKey === '*') {
            changedKeys.splice(0, 1, ...Object.keys(newState));
        } else if (typeof changedKey === 'string' && changedKey !== '*') {
            changedKeys[0] = changedKey;
        }

        this._subscribers.forEach(({ callback, keys }, id) => {
            try {
                // Check if subscriber is interested in these changes
                if (keys && !keys.some(k => changedKeys.includes(k))) {
                    return;
                }

                callback(newState, prevState, changedKeys);
            } catch (error) {
                console.error(`State subscriber ${id} error:`, error);
            }
        });
    }

    /**
     * Record state change in history
     * @private
     * @param {string} action - Action name
     * @param {Object} prevState - Previous state
     * @param {Object} newState - New state
     */
    _recordHistory(action, prevState, newState) {
        this._history.push({
            timestamp: Date.now(),
            action,
            prevState,
            newState
        });

        // Keep history size bounded
        if (this._history.length > this._maxHistorySize) {
            this._history.shift();
        }
    }

    /**
     * Get state history (for debugging)
     * @returns {Array} History array
     */
    getHistory() {
        return [...this._history];
    }

    /**
     * Get subscriber info (for debugging)
     * @returns {Array} Array of subscriber info
     */
    getSubscribers() {
        const subs = [];
        this._subscribers.forEach(({ keys, manager }, id) => {
            subs.push({
                id,
                manager: manager || 'unknown',
                watchingKeys: keys || 'all'
            });
        });
        return subs;
    }

    /**
     * Clear all subscribers (useful for tests/cleanup)
     */
    clearSubscribers() {
        this._subscribers.clear();
    }

    /**
     * Get state statistics
     * @returns {Object} Statistics object
     */
    getStatistics() {
        const data = this._state.data;
        const total = data.length;
        const granted = data.reduce((sum, e) => sum + (parseFloat(e.granted) || 0), 0);
        const used = data.reduce((sum, e) => sum + (parseFloat(e.used) || 0), 0);
        const balance = data.reduce((sum, e) => sum + (parseFloat(e.balance) || 0), 0);
        const avgRate = granted > 0 ? Math.round((used / granted) * 100) : 0;

        return { total, granted, used, balance, avgRate };
    }

    /**
     * Get filtered data by current year
     * @returns {Array} Filtered employees
     */
    getFilteredData() {
        if (!this._state.year) return this._state.data;

        const filtered = this._state.data.filter(e => !e.year || e.year == this._state.year);
        if (filtered.length === 0 && this._state.data.length > 0) {
            return this._state.data;
        }
        return filtered;
    }

    /**
     * Get factory statistics
     * @returns {Array} Array of [factory, usedDays] sorted
     */
    getFactoryStats() {
        const stats = {};
        const data = this.getFilteredData();

        data.forEach(e => {
            const f = e.haken;
            if (!f || f === '0' || f === 'Unknown' || f.trim() === '' || f === 'null') return;
            if (!stats[f]) stats[f] = 0;
            stats[f] += e.used;
        });

        return Object.entries(stats).sort((a, b) => b[1] - a[1]);
    }
}

// Create singleton instance
let unifiedStateInstance = null;

/**
 * Get or create unified state singleton
 * @param {Object} [initialState] - Initial state (only used on first call)
 * @returns {UnifiedState} Singleton instance
 */
export function getUnifiedState(initialState = {}) {
    if (!unifiedStateInstance) {
        unifiedStateInstance = new UnifiedState(initialState);
    }
    return unifiedStateInstance;
}

/**
 * Reset singleton (useful for tests)
 */
export function resetUnifiedState() {
    unifiedStateInstance = null;
}

export default UnifiedState;
