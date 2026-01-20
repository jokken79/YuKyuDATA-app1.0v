/**
 * YuKyu Global State Management
 * @deprecated Use unified-state.js for new code
 * This file re-exports from unified-state.js for backward compatibility
 * @version 2.0.0 - Now delegates to UnifiedState
 */

import { getUnifiedState } from './unified-state.js';

// Get singleton instance - all state operations go through UnifiedState
const unifiedState = getUnifiedState();

// Legacy state object (proxy to unified state for direct access)
const state = unifiedState.getLegacyProxy();

/**
 * Get the current state (read-only copy)
 * @returns {Object} Current state
 */
export function getState() {
    return unifiedState.getSnapshot();
}

/**
 * Get a specific state property
 * @param {string} key - Property name
 * @returns {*} Property value
 */
export function getStateValue(key) {
    return unifiedState.get(key);
}

/**
 * Set state (partial update)
 * @param {Object} updates - Properties to update
 */
export function setState(updates) {
    unifiedState.set(updates);
}

/**
 * Set a specific state property
 * @param {string} key - Property name
 * @param {*} value - New value
 */
export function setStateValue(key, value) {
    unifiedState.set(key, value);
}

/**
 * Reset state to initial values
 */
export function resetState() {
    unifiedState.reset();
}

/**
 * Subscribe to state changes
 * @param {Function} callback - Called with (newState, prevState) on changes
 * @param {string[]} [keys] - Optional array of keys to watch
 * @returns {Function} Unsubscribe function
 */
export function subscribe(callback, keys = null) {
    return unifiedState.subscribe(callback, keys);
}

// ========================================
// DATA HELPERS - Delegate to UnifiedState
// ========================================

/**
 * Get employees filtered by current year
 * @returns {Array} Filtered employees
 */
export function getFilteredData() {
    return unifiedState.getFilteredData();
}

/**
 * Get factory statistics from current data
 * @returns {Array} Array of [factory, usedDays] sorted by usage
 */
export function getFactoryStats() {
    return unifiedState.getFactoryStats();
}

/**
 * Get next fetch request ID (for race condition prevention)
 * @returns {number} Request ID
 */
export function getNextFetchRequestId() {
    const current = unifiedState.get('_fetchRequestId') || 0;
    unifiedState.set('_fetchRequestId', current + 1);
    return current + 1;
}

/**
 * Check if a request ID is still current
 * @param {number} requestId - Request ID to check
 * @returns {boolean} True if request is still current
 */
export function isCurrentRequest(requestId) {
    return requestId === unifiedState.get('_fetchRequestId');
}

// ========================================
// COMPUTED GETTERS
// ========================================

/**
 * Get summary statistics for current data
 * @returns {Object} Statistics object
 */
export function getStatistics() {
    return unifiedState.getStatistics();
}

/**
 * Get employee type counts
 * @returns {Object} Counts by type
 */
export function getTypeCounts() {
    const data = unifiedState.getFilteredData();

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
