/**
 * Unified Bridge: Legacy ↔ Modern Component System
 *
 * Implements the Strangler Fig pattern for gradual frontend migration.
 * Allows modern components to coexist with legacy app.js system.
 *
 * @version 1.0.0
 * @pattern Strangler Fig - Modern system gradually "strangles" legacy
 */

/**
 * Component Registry
 * Stores modern components that can be rendered in legacy containers
 */
class ComponentRegistry {
    constructor() {
        this.components = new Map();
        this.componentMetadata = new Map();
    }

    /**
     * Register a modern component
     *
     * @param {string} name - Component name (e.g., 'Alert', 'Modal')
     * @param {Function} Component - Component class or factory function
     * @param {Object} metadata - Component metadata
     * @param {string} metadata.category - Component category ('core', 'form', 'data', 'layout')
     * @param {Array<string>} metadata.props - Expected props
     * @param {string} metadata.description - Component description
     */
    register(name, Component, metadata = {}) {
        if (typeof Component !== 'function') {
            throw new TypeError(`Component ${name} must be a function`);
        }

        this.components.set(name, Component);
        this.componentMetadata.set(name, {
            category: metadata.category || 'custom',
            props: metadata.props || [],
            description: metadata.description || '',
            registered: new Date().toISOString(),
        });

        console.log(`[ComponentRegistry] Registered: ${name} (${metadata.category || 'custom'})`);
    }

    /**
     * Get registered component
     * @param {string} name - Component name
     * @returns {Function|null} Component or null if not found
     */
    get(name) {
        return this.components.get(name) || null;
    }

    /**
     * Check if component is registered
     * @param {string} name - Component name
     * @returns {boolean}
     */
    has(name) {
        return this.components.has(name);
    }

    /**
     * Get all registered components
     * @returns {Array<{name, category, props, description}>}
     */
    getAll() {
        return Array.from(this.components.keys()).map(name => ({
            name,
            ...this.componentMetadata.get(name),
        }));
    }

    /**
     * Get components by category
     * @param {string} category - Category name
     * @returns {Array<string>} Component names in category
     */
    getByCategory(category) {
        return Array.from(this.componentMetadata.entries())
            .filter(([_, meta]) => meta.category === category)
            .map(([name, _]) => name);
    }
}

/**
 * State Synchronization Manager
 * Keeps state in sync between legacy and modern systems
 */
class StateSyncManager {
    constructor() {
        this.legacyState = window.App?.state || {};
        this.modernState = new Map();
        this.subscribers = new Map();
        this.syncLog = [];
    }

    /**
     * Set value in both systems
     *
     * @param {string} key - State key
     * @param {*} value - Value to set
     * @param {string} source - Source system ('legacy' or 'modern')
     */
    syncValue(key, value, source = 'modern') {
        const oldValue = this.modernState.get(key);

        // Update both systems
        this.modernState.set(key, value);
        if (window.App?.state) {
            window.App.state[key] = value;
        }

        // Log sync
        this.syncLog.push({
            key,
            oldValue,
            newValue: value,
            source,
            timestamp: new Date().toISOString(),
        });

        // Notify subscribers
        this._notifySubscribers(key, value, oldValue);
    }

    /**
     * Get synchronized value
     * @param {string} key - State key
     * @returns {*} Current value
     */
    getValue(key) {
        return this.modernState.get(key) ?? window.App?.state?.[key];
    }

    /**
     * Subscribe to state changes
     *
     * @param {string} key - State key
     * @param {Function} callback - Callback function (newValue, oldValue, key) => void
     * @returns {Function} Unsubscribe function
     */
    subscribe(key, callback) {
        if (!this.subscribers.has(key)) {
            this.subscribers.set(key, new Set());
        }
        this.subscribers.get(key).add(callback);

        // Return unsubscribe function
        return () => {
            this.subscribers.get(key).delete(callback);
        };
    }

    /**
     * Notify all subscribers of a key change
     * @private
     */
    _notifySubscribers(key, newValue, oldValue) {
        const subscribers = this.subscribers.get(key);
        if (subscribers) {
            subscribers.forEach(callback => {
                try {
                    callback(newValue, oldValue, key);
                } catch (error) {
                    console.error(`[StateSyncManager] Subscriber error for key "${key}":`, error);
                }
            });
        }
    }

    /**
     * Get sync log
     * @param {number} limit - Max entries to return
     * @returns {Array} Sync log entries
     */
    getSyncLog(limit = 50) {
        return this.syncLog.slice(-limit);
    }

    /**
     * Clear sync log
     */
    clearSyncLog() {
        this.syncLog = [];
    }
}

/**
 * Migration Tracker
 * Tracks which features use legacy vs modern systems
 */
class MigrationTracker {
    constructor() {
        this.features = new Map();
        this.pageViews = [];
        this.componentUsage = new Map();
        this.startTime = Date.now();
    }

    /**
     * Register a feature
     *
     * @param {string} featureName - Feature name (e.g., 'employee_list', 'leave_requests')
     * @param {string} system - System used ('legacy', 'modern', 'hybrid')
     * @param {Object} details - Additional details
     */
    registerFeature(featureName, system, details = {}) {
        this.features.set(featureName, {
            system,
            details,
            firstUsed: new Date().toISOString(),
            usageCount: 0,
        });

        console.log(`[MigrationTracker] Feature "${featureName}" registered as ${system}`);
    }

    /**
     * Track component usage
     *
     * @param {string} componentName - Component name
     * @param {string} system - System ('legacy' or 'modern')
     */
    trackComponentUsage(componentName, system) {
        const key = `${componentName}:${system}`;
        const count = this.componentUsage.get(key) || 0;
        this.componentUsage.set(key, count + 1);
    }

    /**
     * Track page view
     *
     * @param {string} pageName - Page name
     * @param {string} system - System used ('legacy' or 'modern')
     */
    trackPageView(pageName, system) {
        this.pageViews.push({
            page: pageName,
            system,
            timestamp: new Date().toISOString(),
        });
    }

    /**
     * Get migration statistics
     * @returns {Object} Statistics object
     */
    getStatistics() {
        const stats = {
            features: Object.fromEntries(this.features),
            componentUsage: Object.fromEntries(this.componentUsage),
            pageViews: this.pageViews,
            systems: {
                legacy: 0,
                modern: 0,
                hybrid: 0,
            },
            uptime: {
                milliseconds: Date.now() - this.startTime,
                seconds: Math.floor((Date.now() - this.startTime) / 1000),
                minutes: Math.floor((Date.now() - this.startTime) / 60000),
            },
        };

        // Count system usage
        this.features.forEach(feature => {
            if (feature.system === 'legacy') stats.systems.legacy++;
            else if (feature.system === 'modern') stats.systems.modern++;
            else if (feature.system === 'hybrid') stats.systems.hybrid++;
        });

        return stats;
    }

    /**
     * Get migration progress percentage
     * @returns {number} Percentage of features migrated (0-100)
     */
    getMigrationProgress() {
        if (this.features.size === 0) return 0;

        const modern = Array.from(this.features.values())
            .filter(f => f.system === 'modern' || f.system === 'hybrid').length;

        return Math.round((modern / this.features.size) * 100);
    }

    /**
     * Generate migration report
     * @returns {string} Formatted migration report
     */
    generateReport() {
        const stats = this.getStatistics();
        const progress = this.getMigrationProgress();

        return `
╔════════════════════════════════════════════════════╗
║         MIGRATION STATUS REPORT                    ║
╚════════════════════════════════════════════════════╝

📊 Overall Progress: ${progress}%

🏢 Features by System:
  • Legacy:  ${stats.systems.legacy}
  • Modern:  ${stats.systems.modern}
  • Hybrid:  ${stats.systems.hybrid}

📱 Page Views: ${stats.pageViews.length}

⏱️  Uptime: ${stats.uptime.minutes}m ${stats.uptime.seconds % 60}s

🔄 Migration Velocity:
  • Features/hour: ${Math.round((this.features.size / (stats.uptime.milliseconds / 3600000)) * 100) / 100}
  • Last 10 features:
${Array.from(this.features.entries())
    .slice(-10)
    .map(([name, data]) => `    - ${name}: ${data.system}`)
    .join('\n')}
        `;
    }
}

/**
 * Unified Bridge
 * Main class that orchestrates component rendering and state management
 */
class UnifiedBridge {
    constructor() {
        this.componentRegistry = new ComponentRegistry();
        this.stateSync = new StateSyncManager();
        this.migrationTracker = new MigrationTracker();
        this.renderQueue = [];
        this.isProcessing = false;
    }

    // ==================== Component Management ====================

    /**
     * Register a modern component for use in legacy containers
     *
     * USAGE:
     * ```javascript
     * import { Alert } from '/static/src/components/index.js';
     *
     * bridge.registerModernComponent('Alert', Alert, {
     *   category: 'core',
     *   props: ['type', 'message', 'onClose'],
     *   description: 'Alert notification component'
     * });
     * ```
     *
     * @param {string} name - Component name
     * @param {Function} Component - Component factory
     * @param {Object} metadata - Component metadata
     */
    registerModernComponent(name, Component, metadata = {}) {
        this.componentRegistry.register(name, Component, metadata);
        this.migrationTracker.registerFeature(`component_${name}`, 'modern');
    }

    /**
     * Get all registered components
     * @returns {Array} List of registered components
     */
    getRegisteredComponents() {
        return this.componentRegistry.getAll();
    }

    // ==================== Rendering ====================

    /**
     * Render modern component in legacy container
     *
     * USAGE:
     * ```javascript
     * // In legacy app.js:
     * bridge.renderInLegacy('Alert', 'alert-container', {
     *   type: 'success',
     *   message: 'Operación completada',
     * });
     *
     * // HTML:
     * <div id="alert-container"></div>
     * ```
     *
     * @param {string} componentName - Registered component name
     * @param {string} containerId - Target container ID
     * @param {Object} props - Component props
     * @param {Object} options - Render options
     * @returns {Promise<void>}
     */
    async renderInLegacy(componentName, containerId, props = {}, options = {}) {
        return new Promise((resolve, reject) => {
            const task = {
                componentName,
                containerId,
                props,
                options: {
                    async: true,
                    clearContainer: true,
                    ...options,
                },
                resolve,
                reject,
                timestamp: Date.now(),
            };

            this.renderQueue.push(task);
            this._processRenderQueue();
        });
    }

    /**
     * Process render queue
     * @private
     */
    async _processRenderQueue() {
        if (this.isProcessing || this.renderQueue.length === 0) return;

        this.isProcessing = true;

        try {
            while (this.renderQueue.length > 0) {
                const task = this.renderQueue.shift();
                await this._executeRender(task);
            }
        } finally {
            this.isProcessing = false;
        }
    }

    /**
     * Execute single render task
     * @private
     */
    async _executeRender(task) {
        const {
            componentName,
            containerId,
            props,
            options,
            resolve,
            reject,
        } = task;

        try {
            // Validate component exists
            if (!this.componentRegistry.has(componentName)) {
                throw new Error(`Component "${componentName}" not registered`);
            }

            // Get container
            const container = document.getElementById(containerId);
            if (!container) {
                throw new Error(`Container "#${containerId}" not found in DOM`);
            }

            // Clear container if requested
            if (options.clearContainer) {
                container.innerHTML = '';
            }

            // Get component
            const Component = this.componentRegistry.get(componentName);

            // Render component
            const element = Component(props);

            // Append to container
            if (element instanceof HTMLElement) {
                container.appendChild(element);
            } else if (typeof element === 'string') {
                container.innerHTML = element;
            } else {
                throw new TypeError(`Component must return HTMLElement or string, got ${typeof element}`);
            }

            // Track usage
            this.migrationTracker.trackComponentUsage(componentName, 'modern');

            // Emit render event
            this._emitEvent('component-rendered', {
                componentName,
                containerId,
                timestamp: Date.now(),
                duration: Date.now() - task.timestamp,
            });

            resolve();
        } catch (error) {
            console.error(`[UnifiedBridge] Render error for ${componentName}:`, error);
            this._emitEvent('component-error', {
                componentName,
                containerId,
                error: error.message,
            });
            reject(error);
        }
    }

    // ==================== State Management ====================

    /**
     * Synchronize state between systems
     *
     * USAGE:
     * ```javascript
     * // From modern code:
     * bridge.syncState('selectedYear', 2025);
     *
     * // Now accessible from legacy:
     * console.log(App.state.selectedYear); // 2025
     *
     * // Subscribe to changes:
     * const unsubscribe = bridge.onStateChange('selectedYear', (newVal, oldVal) => {
     *   console.log(`Year changed: ${oldVal} → ${newVal}`);
     * });
     * ```
     *
     * @param {string} key - State key
     * @param {*} value - Value to sync
     */
    syncState(key, value) {
        this.stateSync.syncValue(key, value, 'modern');
    }

    /**
     * Get state value from either system
     * @param {string} key - State key
     * @returns {*} Current value
     */
    getState(key) {
        return this.stateSync.getValue(key);
    }

    /**
     * Subscribe to state changes
     *
     * @param {string} key - State key
     * @param {Function} callback - Callback function
     * @returns {Function} Unsubscribe function
     */
    onStateChange(key, callback) {
        return this.stateSync.subscribe(key, callback);
    }

    /**
     * Get complete state snapshot
     * @returns {Object} Current state
     */
    getStateSnapshot() {
        return {
            legacy: window.App?.state || {},
            modern: Object.fromEntries(this.stateSync.modernState),
        };
    }

    // ==================== Migration Tracking ====================

    /**
     * Register feature migration status
     *
     * USAGE:
     * ```javascript
     * // Feature still using legacy:
     * bridge.registerFeature('employee_list', 'legacy');
     *
     * // Feature migrated to modern:
     * bridge.registerFeature('leave_requests', 'modern');
     *
     * // Feature using both (hybrid):
     * bridge.registerFeature('analytics', 'hybrid', {
     *   note: 'Dashboard uses modern, charts use legacy'
     * });
     * ```
     *
     * @param {string} featureName - Feature name
     * @param {string} system - System type ('legacy', 'modern', 'hybrid')
     * @param {Object} details - Additional details
     */
    registerFeature(featureName, system, details = {}) {
        this.migrationTracker.registerFeature(featureName, system, details);
    }

    /**
     * Track page view
     * @param {string} pageName - Page name
     * @param {string} system - System used
     */
    trackPageView(pageName, system = 'legacy') {
        this.migrationTracker.trackPageView(pageName, system);
    }

    /**
     * Get migration statistics
     * @returns {Object} Statistics
     */
    getMigrationStats() {
        return this.migrationTracker.getStatistics();
    }

    /**
     * Get migration progress (0-100)
     * @returns {number} Progress percentage
     */
    getMigrationProgress() {
        return this.migrationTracker.getMigrationProgress();
    }

    /**
     * Generate migration report
     * @returns {string} Formatted report
     */
    getMigrationReport() {
        return this.migrationTracker.generateReport();
    }

    /**
     * Export migration data
     * @returns {Object} JSON-serializable migration data
     */
    exportMigrationData() {
        return {
            timestamp: new Date().toISOString(),
            progress: this.getMigrationProgress(),
            stats: this.getMigrationStats(),
            stateSync: {
                legacyState: window.App?.state || {},
                modernState: Object.fromEntries(this.stateSync.modernState),
                syncLog: this.stateSync.getSyncLog(),
            },
        };
    }

    // ==================== Event System ====================

    /**
     * Register event listener for bridge events
     *
     * EVENTS:
     * - 'component-rendered': When component renders successfully
     * - 'component-error': When component render fails
     * - 'state-synced': When state is synchronized
     *
     * @param {string} eventType - Event type
     * @param {Function} listener - Event listener
     */
    on(eventType, listener) {
        if (!window._bridgeEventListeners) {
            window._bridgeEventListeners = new Map();
        }

        if (!window._bridgeEventListeners.has(eventType)) {
            window._bridgeEventListeners.set(eventType, new Set());
        }

        window._bridgeEventListeners.get(eventType).add(listener);
    }

    /**
     * Remove event listener
     * @param {string} eventType - Event type
     * @param {Function} listener - Event listener to remove
     */
    off(eventType, listener) {
        if (window._bridgeEventListeners?.has(eventType)) {
            window._bridgeEventListeners.get(eventType).delete(listener);
        }
    }

    /**
     * Emit event
     * @private
     */
    _emitEvent(eventType, data) {
        if (!window._bridgeEventListeners?.has(eventType)) return;

        window._bridgeEventListeners.get(eventType).forEach(listener => {
            try {
                listener(data);
            } catch (error) {
                console.error(`[UnifiedBridge] Event listener error:`, error);
            }
        });
    }

    // ==================== Debugging ====================

    /**
     * Enable debug mode
     * Logs all bridge operations to console
     */
    enableDebugMode() {
        this.on('component-rendered', (data) => {
            console.log(`[Bridge] Component rendered:`, data);
        });

        this.on('component-error', (data) => {
            console.error(`[Bridge] Component error:`, data);
        });

        this.stateSync.subscribe('*', (newVal, oldVal, key) => {
            console.log(`[Bridge] State changed: ${key} = ${newVal}`);
        });
    }

    /**
     * Get debug information
     * @returns {Object} Debug info
     */
    getDebugInfo() {
        return {
            components: {
                registered: this.componentRegistry.getAll().length,
                list: this.componentRegistry.getAll(),
            },
            state: this.getStateSnapshot(),
            migration: this.getMigrationStats(),
            renderQueue: {
                pending: this.renderQueue.length,
                processing: this.isProcessing,
            },
            uptime: Date.now() - this.migrationTracker.startTime,
        };
    }

    /**
     * Print debug info to console
     */
    printDebugInfo() {
        const info = this.getDebugInfo();
        console.group('[UnifiedBridge] Debug Information');
        console.table(info);
        console.groupEnd();
    }
}

/**
 * Singleton instance
 */
let bridgeInstance = null;

/**
 * Get or create unified bridge instance
 * @returns {UnifiedBridge} Bridge instance
 */
export function getUnifiedBridge() {
    if (!bridgeInstance) {
        bridgeInstance = new UnifiedBridge();
        window.UnifiedBridge = bridgeInstance; // Expose globally for legacy code
    }
    return bridgeInstance;
}

/**
 * Initialize bridge and expose to global scope
 *
 * USAGE:
 * ```javascript
 * // In your app initialization (e.g., index.html):
 * import { initBridge } from '/static/src/legacy-bridge/unified-bridge.js';
 *
 * initBridge();
 *
 * // Now available globally:
 * window.UnifiedBridge.renderInLegacy(...);
 * window.UnifiedBridge.syncState(...);
 * ```
 *
 * @returns {UnifiedBridge} Bridge instance
 */
export function initBridge() {
    const bridge = getUnifiedBridge();
    console.log('[UnifiedBridge] Initialized successfully');
    return bridge;
}

/**
 * Export as default
 */
export default {
    getUnifiedBridge,
    initBridge,
    UnifiedBridge,
};
