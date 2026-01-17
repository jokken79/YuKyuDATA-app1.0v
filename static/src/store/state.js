/**
 * YuKyu Global State Management
 * Estado global de la aplicacion con patron Observer
 * @version 1.0.0
 */

// Initial state
const initialState = {
    // Data
    data: [],
    availableYears: [],

    // Current selections
    year: null,
    currentView: 'dashboard',
    typeFilter: 'all',

    // Charts instances (managed externally)
    charts: {},

    // UI state
    isLoading: false,
    theme: 'dark',

    // Warnings
    fallbackWarnedYear: null,

    // Request tracking (prevent race conditions)
    _fetchRequestId: 0
};

// State container
let state = { ...initialState };

// Subscribers for state changes
const subscribers = new Map();
let subscriberId = 0;

/**
 * Get the current state (read-only copy)
 * @returns {Object} Current state
 */
export function getState() {
    return { ...state };
}

/**
 * Get a specific state property
 * @param {string} key - Property name
 * @returns {*} Property value
 */
export function getStateValue(key) {
    return state[key];
}

/**
 * Set state (partial update)
 * @param {Object} updates - Properties to update
 */
export function setState(updates) {
    const prevState = { ...state };
    state = { ...state, ...updates };

    // Notify subscribers
    notifySubscribers(prevState, state);
}

/**
 * Set a specific state property
 * @param {string} key - Property name
 * @param {*} value - New value
 */
export function setStateValue(key, value) {
    const prevState = { ...state };
    state[key] = value;

    // Notify subscribers
    notifySubscribers(prevState, state);
}

/**
 * Reset state to initial values
 */
export function resetState() {
    const prevState = { ...state };
    state = { ...initialState };
    notifySubscribers(prevState, state);
}

/**
 * Subscribe to state changes
 * @param {Function} callback - Called with (newState, prevState) on changes
 * @param {string[]} [keys] - Optional array of keys to watch (watches all if not provided)
 * @returns {Function} Unsubscribe function
 */
export function subscribe(callback, keys = null) {
    const id = ++subscriberId;
    subscribers.set(id, { callback, keys });

    // Return unsubscribe function
    return () => {
        subscribers.delete(id);
    };
}

/**
 * Notify all subscribers of state change
 * @param {Object} prevState - Previous state
 * @param {Object} newState - New state
 */
function notifySubscribers(prevState, newState) {
    subscribers.forEach(({ callback, keys }) => {
        // If watching specific keys, check if any changed
        if (keys) {
            const hasChange = keys.some(key => prevState[key] !== newState[key]);
            if (!hasChange) return;
        }

        try {
            callback(newState, prevState);
        } catch (error) {
            console.error('State subscriber error:', error);
        }
    });
}

// ========================================
// DATA HELPERS
// ========================================

/**
 * Get employees filtered by current year
 * @returns {Array} Filtered employees
 */
export function getFilteredData() {
    if (!state.year) return state.data;

    // Use loose equality to handle string/number differences
    const filtered = state.data.filter(e => !e.year || e.year == state.year);

    // Fallback: if selected year returns no data but we have data, return all
    if (filtered.length === 0 && state.data.length > 0) {
        console.warn(`No data for year ${state.year}, showing all records`);
        return state.data;
    }

    return filtered;
}

/**
 * Get factory statistics from current data
 * @returns {Array} Array of [factory, usedDays] sorted by usage
 */
export function getFactoryStats() {
    const stats = {};
    const data = getFilteredData();

    data.forEach(e => {
        const f = e.haken;
        // Filter invalid factory names
        if (!f || f === '0' || f === 'Unknown' || f.trim() === '' || f === 'null') return;
        if (!stats[f]) stats[f] = 0;
        stats[f] += e.used;
    });

    return Object.entries(stats).sort((a, b) => b[1] - a[1]);
}

/**
 * Get next fetch request ID (for race condition prevention)
 * @returns {number} Request ID
 */
export function getNextFetchRequestId() {
    state._fetchRequestId++;
    return state._fetchRequestId;
}

/**
 * Check if a request ID is still current
 * @param {number} requestId - Request ID to check
 * @returns {boolean} True if request is still current
 */
export function isCurrentRequest(requestId) {
    return requestId === state._fetchRequestId;
}

// ========================================
// COMPUTED GETTERS
// ========================================

/**
 * Get summary statistics for current data
 * @returns {Object} Statistics object
 */
export function getStatistics() {
    const data = getFilteredData();

    const total = data.length;
    const granted = data.reduce((sum, e) => sum + (parseFloat(e.granted) || 0), 0);
    const used = data.reduce((sum, e) => sum + (parseFloat(e.used) || 0), 0);
    const balance = data.reduce((sum, e) => sum + (parseFloat(e.balance) || 0), 0);
    const avgRate = granted > 0 ? Math.round((used / granted) * 100) : 0;

    return {
        total,
        granted,
        used,
        balance,
        avgRate
    };
}

/**
 * Get employee type counts
 * @returns {Object} Counts by type
 */
export function getTypeCounts() {
    const data = getFilteredData();

    return {
        all: data.length,
        haken: data.filter(e => e.employeeType === 'haken' || e.type === 'haken').length,
        ukeoi: data.filter(e => e.employeeType === 'ukeoi' || e.type === 'ukeoi').length,
        staff: data.filter(e => e.employeeType === 'staff' || e.type === 'staff').length
    };
}

// Export state object for direct access (use with caution)
export { state };

// Default export
export default {
    getState,
    getStateValue,
    setState,
    setStateValue,
    resetState,
    subscribe,
    getFilteredData,
    getFactoryStats,
    getNextFetchRequestId,
    isCurrentRequest,
    getStatistics,
    getTypeCounts
};
