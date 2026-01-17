/**
 * Event Delegation Module
 * Centralized event handling using data attributes
 * Replaces inline onclick handlers with modern event delegation
 *
 * Usage: Add data-action="actionName" to elements
 * The module will automatically call App.actions[actionName] or nested methods
 *
 * Examples:
 *   data-action="theme.toggle" → App.theme.toggle()
 *   data-action="ui.switchView" data-view="dashboard" → App.ui.switchView('dashboard')
 *   data-action="data.sync" → App.data.sync()
 */

export class EventDelegation {
    constructor() {
        this.initialized = false;
        this.handlers = new Map();
    }

    /**
     * Initialize event delegation on document
     */
    init() {
        if (this.initialized) return;

        // Click events
        document.addEventListener('click', this.handleClick.bind(this));

        // Keyboard events for accessibility
        document.addEventListener('keydown', this.handleKeydown.bind(this));

        this.initialized = true;
        console.log('[EventDelegation] Initialized');
    }

    /**
     * Handle click events via delegation
     */
    handleClick(event) {
        const target = event.target.closest('[data-action]');
        if (!target) return;

        const action = target.dataset.action;
        if (!action) return;

        event.preventDefault();
        this.executeAction(action, target, event);
    }

    /**
     * Handle keyboard events for buttons
     */
    handleKeydown(event) {
        if (event.key !== 'Enter' && event.key !== ' ') return;

        const target = event.target;
        if (!target.hasAttribute('data-action')) return;

        // Prevent space from scrolling
        if (event.key === ' ') {
            event.preventDefault();
        }

        const action = target.dataset.action;
        this.executeAction(action, target, event);
    }

    /**
     * Execute an action by name
     * Supports dot notation: 'ui.switchView', 'theme.toggle'
     */
    executeAction(actionPath, element, event) {
        try {
            // Check for custom handler first
            if (this.handlers.has(actionPath)) {
                this.handlers.get(actionPath)(element, event);
                return;
            }

            // Navigate to the method in App object
            const parts = actionPath.split('.');
            let context = window.App;
            let method = null;

            for (let i = 0; i < parts.length; i++) {
                if (!context) break;

                if (i === parts.length - 1) {
                    method = context[parts[i]];
                } else {
                    context = context[parts[i]];
                }
            }

            if (typeof method !== 'function') {
                console.warn(`[EventDelegation] Method not found: App.${actionPath}`);
                return;
            }

            // Get arguments from data attributes
            const args = this.getArgsFromElement(element, actionPath);

            // Execute the method
            method.apply(context, args);

        } catch (error) {
            console.error(`[EventDelegation] Error executing ${actionPath}:`, error);
        }
    }

    /**
     * Extract arguments from element data attributes
     */
    getArgsFromElement(element, actionPath) {
        const args = [];

        // Common argument mappings
        const argMappings = {
            'ui.switchView': ['view'],
            'ui.filterByType': ['type'],
            'employeeTypes.switchTab': ['tab'],
            'editYukyu': ['employeeNum', 'year'],
            'showEmployeeDetails': ['employeeNum', 'year'],
            'requests.approve': ['id'],
            'requests.reject': ['id'],
            'requests.revert': ['id'],
            'compliance.loadDetails': ['employeeNum'],
            'analytics.loadPredictions': [],
            'calendar.loadEvents': [],
            'theme.toggle': [],
            'data.sync': [],
            'data.syncGenzai': [],
            'data.syncUkeoi': [],
            'data.syncStaff': [],
            'bulkEdit.openModal': [],
            'bulkEdit.clearSelection': [],
            'reports.showExportModal': [],
        };

        const mapping = argMappings[actionPath];
        if (mapping) {
            for (const attr of mapping) {
                const value = element.dataset[attr];
                if (value !== undefined) {
                    // Try to parse as JSON for objects/arrays/numbers
                    try {
                        args.push(JSON.parse(value));
                    } catch {
                        args.push(value);
                    }
                }
            }
        }

        return args;
    }

    /**
     * Register a custom handler for an action
     */
    registerHandler(actionPath, handler) {
        this.handlers.set(actionPath, handler);
    }

    /**
     * Remove a custom handler
     */
    unregisterHandler(actionPath) {
        this.handlers.delete(actionPath);
    }

    /**
     * Convert onclick attributes to data-action attributes
     * Utility for migration - can be called once to update DOM
     */
    migrateOnclickToDataAction() {
        const elementsWithOnclick = document.querySelectorAll('[onclick]');
        let migratedCount = 0;

        elementsWithOnclick.forEach(element => {
            const onclick = element.getAttribute('onclick');
            if (!onclick) return;

            // Parse common patterns
            const patterns = [
                // App.ui.switchView('dashboard')
                { regex: /App\.ui\.switchView\(['"]([^'"]+)['"]\)/, action: 'ui.switchView', arg: 'view' },
                // App.theme.toggle()
                { regex: /App\.theme\.toggle\(\)/, action: 'theme.toggle' },
                // App.data.sync()
                { regex: /App\.data\.sync\(\)/, action: 'data.sync' },
                // App.data.syncGenzai()
                { regex: /App\.data\.syncGenzai\(\)/, action: 'data.syncGenzai' },
                // App.data.syncUkeoi()
                { regex: /App\.data\.syncUkeoi\(\)/, action: 'data.syncUkeoi' },
                // App.ui.filterByType('type')
                { regex: /App\.ui\.filterByType\(['"]([^'"]+)['"]\)/, action: 'ui.filterByType', arg: 'type' },
                // App.employeeTypes.switchTab('tab')
                { regex: /App\.employeeTypes\.switchTab\(['"]([^'"]+)['"]\)/, action: 'employeeTypes.switchTab', arg: 'tab' },
                // App.bulkEdit.openModal()
                { regex: /App\.bulkEdit\.openModal\(\)/, action: 'bulkEdit.openModal' },
                // App.bulkEdit.clearSelection()
                { regex: /App\.bulkEdit\.clearSelection\(\)/, action: 'bulkEdit.clearSelection' },
                // App.reports.showExportModal()
                { regex: /App\.reports\.showExportModal\(\)/, action: 'reports.showExportModal' },
                // App.compliance.check5Day()
                { regex: /App\.compliance\.check5Day\(\)/, action: 'compliance.check5Day' },
                // App.compliance.loadAlerts()
                { regex: /App\.compliance\.loadAlerts\(\)/, action: 'compliance.loadAlerts' },
                // App.calendar.loadEvents()
                { regex: /App\.calendar\.loadEvents\(\)/, action: 'calendar.loadEvents' },
                // App.analytics.loadPredictions()
                { regex: /App\.analytics\.loadPredictions\(\)/, action: 'analytics.loadPredictions' },
            ];

            for (const pattern of patterns) {
                const match = onclick.match(pattern.regex);
                if (match) {
                    element.setAttribute('data-action', pattern.action);
                    if (pattern.arg && match[1]) {
                        element.setAttribute(`data-${pattern.arg}`, match[1]);
                    }
                    element.removeAttribute('onclick');
                    migratedCount++;
                    break;
                }
            }
        });

        console.log(`[EventDelegation] Migrated ${migratedCount} onclick handlers`);
        return migratedCount;
    }
}

// Singleton instance
export const eventDelegation = new EventDelegation();

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => eventDelegation.init());
} else {
    eventDelegation.init();
}

export default eventDelegation;
