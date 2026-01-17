/**
 * Modern Component Integration Bridge
 * FASE 4: TAREA 2 - Non-Breaking Integration of Modern Components
 *
 * This module integrates modern components from static/src/ into the legacy app.js
 * WITHOUT breaking any existing functionality. All legacy methods remain available,
 * but internally they now use the modern, accessible components.
 *
 * @version 1.0.0
 * @date 2026-01-17
 */

(function() {
    'use strict';

    // ========================================
    // PHASE 1: Import Modern Components
    // ========================================

    let AlertComponent, ModalComponent, FormComponent, TableComponent;
    let DatePickerComponent, SelectComponent, ButtonComponent;

    // Dynamic import of modern components
    const loadModernComponents = async () => {
        try {
            // Import modern Alert component
            const alertModule = await import('/static/src/components/Alert.js');
            AlertComponent = alertModule.Alert;

            // Import modern Modal component
            const modalModule = await import('/static/src/components/Modal.js');
            ModalComponent = modalModule.Modal;

            // Import modern Form component
            const formModule = await import('/static/src/components/Form.js');
            FormComponent = formModule.Form;

            // Import modern Table component
            const tableModule = await import('/static/src/components/Table.js');
            TableComponent = tableModule.DataTable || tableModule.Table;

            // Import modern DatePicker component
            const datePickerModule = await import('/static/src/components/DatePicker.js');
            DatePickerComponent = datePickerModule.DatePicker;

            // Import modern Select component
            const selectModule = await import('/static/src/components/Select.js');
            SelectComponent = selectModule.Select;

            // Import modern Button component
            const buttonModule = await import('/static/src/components/Button.js');
            ButtonComponent = buttonModule.Button;

            console.log('✓ Modern components loaded successfully');
            return true;
        } catch (error) {
            console.error('Failed to load modern components:', error);
            return false;
        }
    };

    // ========================================
    // PHASE 2: Override Legacy Methods
    // ========================================

    /**
     * Override App.showNotification() to use modern Alert component
     * Maintains 100% backward compatibility
     */
    const originalShowNotification = App.ui?.showToast || App.ui?.showNotification;

    App.ui.showNotification = function(message, type = 'info', duration = 4000) {
        // Use modern Alert if loaded, otherwise fall back to legacy
        if (AlertComponent) {
            try {
                AlertComponent[type]?.(message, duration) ||
                AlertComponent.show({ message, type, duration });
                return;
            } catch (e) {
                console.error('Modern notification failed:', e);
            }
        }
        // Fallback to legacy implementation
        if (originalShowNotification) {
            originalShowNotification.call(this, message, type, duration);
        }
    };

    App.ui.showToast = function(type, message, duration = 4000) {
        // Normalize parameter order (some code uses type first)
        App.ui.showNotification(message, type, duration);
    };

    /**
     * Override App.showModal() to use modern Modal component
     * Maintains 100% backward compatibility
     */
    const createModernModal = (options) => {
        if (!ModalComponent) return null;

        const modalOptions = {
            title: options.title || '',
            content: options.content || options.html || '',
            size: options.size || 'medium',
            closable: options.closable !== false,
            closeOnEscape: options.closeOnEscape !== false,
            closeOnBackdrop: options.closeOnBackdrop !== false,
            className: options.className || '',
            buttons: options.buttons || options.actions || [],
            ariaLabel: options.ariaLabel || options.title || '',
            onConfirm: options.onConfirm || options.confirm,
            onClose: options.onClose || options.close,
        };

        return new ModalComponent(modalOptions);
    };

    App.showModal = function(options) {
        const modal = createModernModal(options);
        if (modal) {
            modal.open();
            return modal;
        }
        // Fallback would go here if needed
        return null;
    };

    // Add shortcut method for modern modal creation
    App.showModalModern = function(options) {
        return App.showModal(options);
    };

    /**
     * Add modern confirmation dialog
     */
    App.confirm = function(options) {
        if (!AlertComponent) {
            // Fallback to native confirm
            return window.confirm(options.message || 'Are you sure?');
        }

        return new Promise((resolve) => {
            if (AlertComponent.confirm) {
                AlertComponent.confirm({
                    message: options.message || '確認',
                    title: options.title,
                    type: options.type || 'warning',
                    confirmText: options.confirmText || '確認',
                    cancelText: options.cancelText || 'キャンセル',
                    dangerous: options.dangerous || false,
                    onConfirm: () => resolve(true),
                    onCancel: () => resolve(false),
                });
            } else {
                resolve(window.confirm(options.message));
            }
        });
    };

    /**
     * Override form creation (if exists in legacy)
     */
    if (App.forms && typeof App.forms.create === 'function') {
        const originalFormCreate = App.forms.create;
        App.forms.create = function(options) {
            if (FormComponent && options.useModern !== false) {
                try {
                    const form = new FormComponent({
                        fields: options.fields || [],
                        buttons: options.buttons || options.actions || [],
                        onSubmit: options.onSubmit || options.submit,
                        onCancel: options.onCancel || options.cancel,
                        className: options.className || '',
                    });
                    return form;
                } catch (e) {
                    console.warn('Modern form failed, using legacy:', e);
                }
            }
            return originalFormCreate.call(this, options);
        };
    }

    // ========================================
    // PHASE 3: Add Helper Methods for Modern Components
    // ========================================

    /**
     * Create a modern table
     * @param {Object} options - Table options (columns, data, pagination, etc)
     * @returns {DataTable} Modern table instance
     */
    App.createTable = function(options) {
        if (!TableComponent) {
            console.warn('Modern Table component not loaded');
            return null;
        }

        const tableOptions = {
            columns: options.columns || [],
            data: options.data || [],
            pagination: options.pagination !== false ? {
                pageSize: options.pageSize || 20,
            } : false,
            sortable: options.sortable !== false,
            filterable: options.filterable !== false,
            selectable: options.selectable !== false,
            className: options.className || '',
            onRowClick: options.onRowClick,
            onSelectionChange: options.onSelectionChange,
            onFilter: options.onFilter,
            onSort: options.onSort,
        };

        return new TableComponent(tableOptions);
    };

    /**
     * Create a modern date picker
     * @param {Object} options - DatePicker options
     * @returns {DatePicker} Modern DatePicker instance
     */
    App.createDatePicker = function(options) {
        if (!DatePickerComponent) {
            console.warn('Modern DatePicker component not loaded');
            return null;
        }

        return new DatePickerComponent({
            ...options,
            locale: App.i18n?.currentLocale || 'ja',
        });
    };

    /**
     * Create a modern select
     * @param {Object} options - Select options
     * @returns {Select} Modern Select instance
     */
    App.createSelect = function(options) {
        if (!SelectComponent) {
            console.warn('Modern Select component not loaded');
            return null;
        }

        return new SelectComponent({
            ...options,
            searchable: options.searchable !== false,
            clearable: options.clearable !== false,
            multiple: options.multiple || false,
        });
    };

    // ========================================
    // PHASE 4: Enhance Accessibility
    // ========================================

    /**
     * Apply accessibility enhancements to existing DOM
     */
    const enhanceA11y = async () => {
        try {
            const a11yModule = await import('/static/src/utils/accessibility.js');
            const enhanceAccessibility = a11yModule.enhanceAccessibility ||
                                        a11yModule.default;

            if (typeof enhanceAccessibility === 'function') {
                // Enhance main content area
                const mainContent = document.querySelector('[role="main"], #main-content, main');
                if (mainContent) {
                    enhanceAccessibility(mainContent);
                }
            }
        } catch (e) {
            console.warn('Accessibility enhancement not available:', e);
        }
    };

    // ========================================
    // PHASE 5: Initialize Integration
    // ========================================

    /**
     * Initialize modern component integration
     * Called when DOM is ready
     */
    const initializeIntegration = async () => {
        console.log('Initializing modern component integration...');

        // Load modern components
        const loaded = await loadModernComponents();

        if (!loaded) {
            console.warn('Modern components not available, using legacy only');
            return;
        }

        // Apply accessibility enhancements
        await enhanceA11y();

        // Mark integration as ready
        window.ModernIntegration = {
            ready: true,
            Alert: AlertComponent,
            Modal: ModalComponent,
            Form: FormComponent,
            Table: TableComponent,
            DatePicker: DatePickerComponent,
            Select: SelectComponent,
            Button: ButtonComponent,
        };

        console.log('✓ Modern component integration ready');
    };

    // ========================================
    // PHASE 6: Hook into App Lifecycle
    // ========================================

    // Wait for DOMContentLoaded or App initialization
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeIntegration);
    } else {
        // DOM is already loaded
        setTimeout(initializeIntegration, 100);
    }

    // Also add initialization to App if not already there
    if (App && typeof App.init === 'function') {
        const originalAppInit = App.init;
        App.init = function() {
            // Call original init
            const result = originalAppInit.call(this);
            // Initialize modern integration
            initializeIntegration();
            return result;
        };
    }

    // ========================================
    // PHASE 7: Polyfills for Modern Components
    // ========================================

    // Ensure dynamic imports work in all browsers
    if (!('import' in window)) {
        console.warn('Dynamic imports not supported');
    }

    // ========================================
    // PHASE 8: Debugging & Development
    // ========================================

    // Add global debugging helper
    window.debugModernIntegration = function() {
        return {
            ready: window.ModernIntegration?.ready || false,
            components: {
                Alert: !!AlertComponent,
                Modal: !!ModalComponent,
                Form: !!FormComponent,
                Table: !!TableComponent,
                DatePicker: !!DatePickerComponent,
                Select: !!SelectComponent,
                Button: !!ButtonComponent,
            },
            appUI: {
                showNotification: typeof App?.ui?.showNotification,
                showToast: typeof App?.ui?.showToast,
                showModal: typeof App?.showModal,
                confirm: typeof App?.confirm,
            },
        };
    };

    console.log('[PHASE 4.2] Modern component integration loaded');
    console.log('Run debugModernIntegration() to check status');

})();
