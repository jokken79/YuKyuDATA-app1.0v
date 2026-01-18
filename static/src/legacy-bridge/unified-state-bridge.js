/**
 * Unified State Bridge
 * Bridges legacy App.state with modern UnifiedState
 * Maintains 100% backward compatibility
 * @version 1.0.0
 */

import { UnifiedState, getUnifiedState, resetUnifiedState } from '../store/unified-state.js';
import { PageCoordinator } from '../managers/PageCoordinator.js';

/**
 * Initialize unified state bridge
 * Call this once during app initialization
 *
 * Usage:
 *   import { initUnifiedStateBridge } from '/static/src/legacy-bridge/unified-state-bridge.js';
 *   initUnifiedStateBridge();
 *   // Now App.state is a proxy to unified state
 */
export function initUnifiedStateBridge() {
    // Get or create unified state instance
    const unifiedState = getUnifiedState();

    // Replace App.state with legacy proxy
    // This maintains 100% backward compatibility
    if (window.App) {
        window.App.state = unifiedState.getLegacyProxy();

        // Expose unified state methods on App for modern usage
        window.App._unifiedState = unifiedState;
        window.App._pageCoordinator = null;

        // Helper method to switch pages
        window.App.switchPageModern = async (pageName) => {
            if (!window.App._pageCoordinator) {
                window.App._pageCoordinator = new PageCoordinator(unifiedState);
            }
            await window.App._pageCoordinator.switchPage(pageName);
        };

        // Debug helper
        window.App._debugState = () => {
            console.group('Unified State Debug Info');
            console.log('Current State:', unifiedState.getSnapshot());
            console.log('Subscribers:', unifiedState.getSubscribers());
            console.log('History (last 5):', unifiedState.getHistory().slice(-5));
            console.log('Statistics:', unifiedState.getStatistics());
            console.groupEnd();
        };

        return unifiedState;
    }

    return unifiedState;
}

/**
 * Get unified state instance
 * @returns {UnifiedState} Unified state instance
 */
export function getAppUnifiedState() {
    if (window.App && window.App._unifiedState) {
        return window.App._unifiedState;
    }
    return getUnifiedState();
}

/**
 * Get page coordinator
 * @returns {PageCoordinator} Page coordinator instance
 */
export function getPageCoordinator() {
    if (!window.App) return null;

    if (!window.App._pageCoordinator) {
        const unifiedState = getAppUnifiedState();
        window.App._pageCoordinator = new PageCoordinator(unifiedState);
    }

    return window.App._pageCoordinator;
}

/**
 * Switch page using modern coordinator
 * Replaces legacy switchView() with modern manager-based approach
 *
 * Usage:
 *   await switchPageModern('dashboard');
 *   await switchPageModern('employees');
 *   await switchPageModern('requests');
 *   await switchPageModern('analytics');
 *   await switchPageModern('compliance');
 */
export async function switchPageModern(pageName) {
    const coordinator = getPageCoordinator();
    if (coordinator) {
        await coordinator.switchPage(pageName);
    }
}

/**
 * Subscribe to state changes with modern API
 * Returns a cleanup function
 *
 * Usage:
 *   const unsubscribe = subscribeToState((newState, prevState, changedKeys) => {
 *       console.log('State changed:', changedKeys);
 *   }, ['data', 'year']);
 *   // Later: unsubscribe();
 */
export function subscribeToState(callback, keys = null, managerName = 'CustomSubscriber') {
    const unifiedState = getAppUnifiedState();
    return unifiedState.subscribe(callback, keys, managerName);
}

/**
 * Set state value with modern API
 * Works with both string keys and object updates
 *
 * Usage:
 *   setStateValue('year', 2025);
 *   setStateValue({ year: 2025, typeFilter: 'all' });
 */
export function setStateValue(key, value = null) {
    const unifiedState = getAppUnifiedState();
    if (typeof key === 'object') {
        unifiedState.set(key);
    } else {
        unifiedState.set(key, value);
    }
}

/**
 * Get state snapshot with modern API
 * @returns {Object} Current state snapshot
 */
export function getStateSnapshot() {
    const unifiedState = getAppUnifiedState();
    return unifiedState.getSnapshot();
}

/**
 * Get filtered data
 * @returns {Array} Filtered employees by current year
 */
export function getFilteredData() {
    const unifiedState = getAppUnifiedState();
    return unifiedState.getFilteredData();
}

/**
 * Get statistics
 * @returns {Object} Statistics object
 */
export function getStatistics() {
    const unifiedState = getAppUnifiedState();
    return unifiedState.getStatistics();
}

/**
 * Setup event delegation for page switching
 * Converts data-view clicks to PageCoordinator calls
 *
 * Usage:
 *   setupPageSwitchingDelegation();
 *   // Now clicking .nav-item[data-view="employees"] triggers modern manager
 */
export function setupPageSwitchingDelegation() {
    document.addEventListener('click', async (e) => {
        const navItem = e.target.closest('.nav-item[data-view]');
        if (navItem) {
            const viewName = navItem.dataset.view;
            await switchPageModern(viewName);
            e.preventDefault();
        }
    });
}

/**
 * Cleanup and reset state
 * Useful for testing or app reset
 */
export function cleanupUnifiedState() {
    if (window.App && window.App._pageCoordinator) {
        window.App._pageCoordinator.cleanup();
        window.App._pageCoordinator = null;
    }
    resetUnifiedState();
    if (window.App) {
        delete window.App._unifiedState;
    }
}

/**
 * Create debug panel for development
 * Logs all state changes to console
 */
export function enableStateDebugLogging() {
    const unifiedState = getAppUnifiedState();

    unifiedState.subscribe((newState, prevState, changedKeys) => {
        console.group(`State Changed: ${changedKeys.join(', ')}`);
        changedKeys.forEach(key => {
            console.log(`  ${key}: ${prevState[key]} → ${newState[key]}`);
        });
        console.groupEnd();
    }, null, 'DebugLogger');
}

export default {
    initUnifiedStateBridge,
    getAppUnifiedState,
    getPageCoordinator,
    switchPageModern,
    subscribeToState,
    setStateValue,
    getStateSnapshot,
    getFilteredData,
    getStatistics,
    setupPageSwitchingDelegation,
    cleanupUnifiedState,
    enableStateDebugLogging
};
