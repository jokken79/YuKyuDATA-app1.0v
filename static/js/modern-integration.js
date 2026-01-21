/**
 * Modern Integration Adapter
 * Bridges legacy App.ui methods with ModernUI library
 * Version: 20260117
 */

(function () {
    console.log('🚀 Initializing Modern Integration Adapter...');

    class ModernIntegrationAdapter {
        constructor() {
            this.ready = false;
            this.components = {
                Alert: false,
                Modal: false,
                Form: false,
                Table: false
            };
            this.init();
        }

        init() {
            // Wait for ModernUI and App to be available
            const checkDependencies = setInterval(() => {
                if (window.ModernUI && window.App) {
                    clearInterval(checkDependencies);
                    this.setupAdapter();
                }
            }, 100);
        }

        setupAdapter() {
            console.log('✅ Dependencies found. Setting up adapter...');

            // 1. Map Notification System
            if (window.App.ui) {
                // Backend 'showNotification' often used 'alert' or custom logic. 
                // We map it to ModernUI.Toast
                const originalShowNotification = window.App.ui.showNotification;

                window.App.ui.showNotification = (message, type = 'info', duration = 3000) => {
                    // Convert legacy types if needed
                    const modernType = this.mapNotificationType(type);

                    // Use ModernUI Toast
                    if (window.ModernUI.Toast) {
                        window.ModernUI.Toast.show({
                            message: message,
                            type: modernType,
                            duration: duration
                        });
                        console.debug(`[Integration] Notification shown: ${message} (${type})`);
                    } else {
                        // Fallback
                        console.warn('[Integration] ModernUI.Toast not found, using legacy fallback');
                        if (originalShowNotification) originalShowNotification(message, type);
                    }
                };

                // Map specific overrides if they exist in App.ui
                window.App.ui.showToast = (type, message) => {
                    window.App.ui.showNotification(message, type);
                };
            }

            // 2. Map Modal System
            // Legacy might use App.showModal(options)
            window.App.showModal = (options) => {
                if (window.ModernUI.Dialog) {
                    // Map legacy modal options to ModernUI Dialog options
                    // Legacy: { title, content, buttons: [{text, action}] }
                    // ModernUI: { title, message, ... }

                    // Since ModernUI.Dialog is more of a Confirm/Alert system, 
                    // we might need to adapt complex modals differently. 
                    // For now, let's map simple content modals.

                    return window.ModernUI.Dialog.show({
                        title: options.title || 'Modal',
                        message: options.content || '',
                        type: options.type || 'info',
                        // You might need to map buttons manually if ModernUI supports custom buttons beyond confirm/cancel
                        // ModernUI.Dialog seems to match Confirm/Alert structure. 
                        confirmText: options.confirmText || 'OK',
                        cancelText: options.cancelText || 'Cancel',
                        showCancel: options.showCancel !== false
                    });
                }
            };

            // 3. Map Confirm Dialog
            window.App.confirm = (options) => {
                if (window.ModernUI.Dialog) {
                    return window.ModernUI.Dialog.show({
                        title: options.title || 'Confirm',
                        message: options.message || 'Are you sure?',
                        type: options.type || 'warning',
                        confirmText: 'Yes',
                        cancelText: 'No'
                    }).then(result => result.confirmed);
                }
                return Promise.resolve(confirm(options.message || 'Are you sure?'));
            };

            // 4. Update Status for Test Suite
            this.components = {
                Alert: !!window.ModernUI.Toast,
                Modal: !!window.ModernUI.Dialog,
                Form: true, // Placeholder if no specific form lib
                Table: !!window.ModernUI.SkeletonLoader // improved tables
            };
            this.ready = true;

            // Expose globally
            window.ModernIntegration = this;

            console.log('✨ Modern Integration Ready');

            // Dispatch event for other listeners
            document.dispatchEvent(new CustomEvent('ModernIntegrationReady'));
        }

        mapNotificationType(type) {
            const map = {
                'success': 'success',
                'error': 'error',
                'warning': 'warning',
                'info': 'info',
                'danger': 'error'
            };
            return map[type] || 'info';
        }
    }

    // Initialize
    new ModernIntegrationAdapter();

    // Global Debug Helper for Test Page
    window.debugModernIntegration = () => {
        console.table(window.ModernIntegration.components);
        return window.ModernIntegration;
    };

})();
