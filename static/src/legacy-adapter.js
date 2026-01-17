/**
 * Legacy Adapter - YuKyuDATA
 * Permite usar los nuevos componentes de static/src/ desde app.js
 *
 * Este adapter crea un puente entre la arquitectura legacy (App global)
 * y los nuevos componentes modulares ES6.
 *
 * @module legacy-adapter
 * @version 1.0.0
 */

// Import modern components
import { Modal } from './components/Modal.js';
import { Alert } from './components/Alert.js';
import { DataTable } from './components/Table.js';
import { Form } from './components/Form.js';
import { Button, ButtonGroup } from './components/Button.js';
import { Badge, StatusBadge, CountBadge } from './components/Badge.js';
import { Card, StatCard } from './components/Card.js';
import { DatePicker } from './components/DatePicker.js';
import { Loader, Skeleton, showLoading, showFullPageLoading } from './components/Loader.js';
import { Tooltip, initTooltips, destroyAllTooltips } from './components/Tooltip.js';
import { Input, Textarea } from './components/Input.js';
import { Select } from './components/Select.js';
import { Pagination } from './components/Pagination.js';

/**
 * Wrapper class that provides backwards-compatible API
 * for using modern Modal with legacy code
 */
class LegacyModalWrapper {
    /**
     * Show a modal dialog (compatible with App.modal())
     * @param {Object} options - Modal options
     * @returns {Modal} Modal instance
     */
    static show(options = {}) {
        // Map legacy options to new Modal API
        const modalOptions = {
            title: options.title || '',
            content: options.body || options.content || '',
            size: options.size || 'medium',
            closable: options.closable !== false,
            closeOnBackdrop: options.closeOnOutsideClick !== false,
            closeOnEscape: options.closeOnEscape !== false,
            buttons: [],
            onClose: options.onClose,
            onOpen: options.onOpen
        };

        // Map legacy buttons
        if (options.buttons) {
            modalOptions.buttons = options.buttons.map(btn => ({
                text: btn.text || btn.label,
                variant: btn.class || btn.variant || 'ghost',
                action: btn.action,
                onClick: btn.onClick || btn.callback
            }));
        }

        // Handle legacy confirm/cancel pattern
        if (options.onConfirm) {
            modalOptions.onConfirm = options.onConfirm;
        }

        const modal = new Modal(modalOptions);
        modal.open();
        return modal;
    }

    /**
     * Show alert dialog (compatible with legacy)
     */
    static alert(message, title) {
        return Modal.alert(message, title);
    }

    /**
     * Show confirm dialog (compatible with legacy)
     */
    static confirm(message, title) {
        return Modal.confirm(message, title);
    }

    /**
     * Show prompt dialog (compatible with legacy)
     */
    static prompt(message, defaultValue, title) {
        return Modal.prompt(message, defaultValue, title);
    }

    /**
     * Close all modals
     */
    static closeAll() {
        Modal.closeAll();
    }
}

/**
 * Wrapper for Alert/Toast notifications
 */
class LegacyAlertWrapper {
    /**
     * Show success notification (compatible with App.showNotification)
     */
    static success(message, title = '') {
        return Alert.success(message, title);
    }

    /**
     * Show error notification
     */
    static error(message, title = '') {
        return Alert.error(message, title);
    }

    /**
     * Show warning notification
     */
    static warning(message, title = '') {
        return Alert.warning(message, title);
    }

    /**
     * Show info notification
     */
    static info(message, title = '') {
        return Alert.info(message, title);
    }

    /**
     * Show toast (generic method)
     */
    static toast(options) {
        // Map legacy showNotification options
        if (typeof options === 'string') {
            return Alert.info(options);
        }
        return Alert.toast({
            message: options.message || options.text,
            title: options.title,
            type: options.type || 'info',
            duration: options.duration || options.timeout || 4000
        });
    }

    /**
     * Show confirmation dialog
     */
    static confirm(options) {
        if (typeof options === 'string') {
            return Alert.confirm({ message: options });
        }
        return Alert.confirm(options);
    }

    /**
     * Dismiss all notifications
     */
    static dismissAll() {
        Alert.dismissAll();
    }
}

/**
 * Wrapper for DataTable
 */
class LegacyTableWrapper {
    constructor(container, options = {}) {
        const containerEl = typeof container === 'string' ? document.querySelector(container) : container;
        this.table = new DataTable(containerEl, {
            columns: options.columns || [],
            data: options.data || [],
            paginated: options.pagination !== false,
            pageSize: options.pageSize || options.perPage || 20,
            sortable: options.sortable !== false,
            selectable: options.selectable || false,
            onRowClick: options.onRowClick,
            onSelectionChange: options.onSelectionChange
        });
    }

    /**
     * Set table data
     */
    setData(data) {
        this.table.setData(data);
    }

    /**
     * Get selected rows
     */
    getSelected() {
        return this.table.getSelectedRows();
    }

    /**
     * Render the table
     */
    render() {
        return this.table.render();
    }

    /**
     * Destroy the table
     */
    destroy() {
        this.table.destroy();
    }
}

/**
 * Legacy Adapter class
 * Attaches modern components to the legacy App object
 */
export class LegacyAdapter {
    constructor(legacyApp) {
        this.legacyApp = legacyApp;
        this.initialized = false;
    }

    /**
     * Initialize the adapter
     * Attaches all modern components to App.components
     */
    init() {
        if (this.initialized) {
            console.warn('[LegacyAdapter] Already initialized');
            return;
        }

        if (!this.legacyApp) {
            console.error('[LegacyAdapter] Legacy App not provided');
            return;
        }

        // Create components namespace on App
        this.legacyApp.components = this.legacyApp.components || {};

        // Attach wrapped components
        this.legacyApp.components.Modal = LegacyModalWrapper;
        this.legacyApp.components.Alert = LegacyAlertWrapper;
        this.legacyApp.components.Table = LegacyTableWrapper;
        this.legacyApp.components.Toast = LegacyAlertWrapper; // Alias

        // Attach native components (no wrapper needed)
        this.legacyApp.components.Form = Form;
        this.legacyApp.components.Button = Button;
        this.legacyApp.components.ButtonGroup = ButtonGroup;
        this.legacyApp.components.Badge = Badge;
        this.legacyApp.components.StatusBadge = StatusBadge;
        this.legacyApp.components.CountBadge = CountBadge;
        this.legacyApp.components.Card = Card;
        this.legacyApp.components.StatCard = StatCard;
        this.legacyApp.components.DatePicker = DatePicker;
        this.legacyApp.components.Loader = Loader;
        this.legacyApp.components.Skeleton = Skeleton;
        this.legacyApp.components.Tooltip = Tooltip;
        this.legacyApp.components.Input = Input;
        this.legacyApp.components.Textarea = Textarea;
        this.legacyApp.components.Select = Select;
        this.legacyApp.components.Pagination = Pagination;

        // Attach utility functions
        this.legacyApp.components.showLoading = showLoading;
        this.legacyApp.components.showFullPageLoading = showFullPageLoading;
        this.legacyApp.components.initTooltips = initTooltips;
        this.legacyApp.components.destroyAllTooltips = destroyAllTooltips;

        // Override legacy methods if they exist (optional)
        this._overrideLegacyMethods();

        this.initialized = true;
        console.log('[LegacyAdapter] Modern components attached to App.components');
    }

    /**
     * Override legacy methods to use new components
     * @private
     */
    _overrideLegacyMethods() {
        const app = this.legacyApp;

        // Store original methods for fallback
        const originals = {
            showNotification: app.showNotification,
            showModal: app.showModal,
            showConfirm: app.showConfirm
        };

        // Override showNotification
        if (typeof app.showNotification === 'function' || !app.showNotification) {
            app.showNotification = (message, type = 'info', duration = 4000) => {
                // Use modern Alert component
                switch (type) {
                    case 'success':
                        return Alert.success(message, '', duration);
                    case 'error':
                        return Alert.error(message, '', duration);
                    case 'warning':
                        return Alert.warning(message, '', duration);
                    default:
                        return Alert.info(message, '', duration);
                }
            };
        }

        // Override showModal if not defined or is legacy
        if (!app.showModal || app.showModal.toString().includes('legacy')) {
            app.showModal = (options) => {
                return LegacyModalWrapper.show(options);
            };
        }

        // Override showConfirm
        if (!app.showConfirm) {
            app.showConfirm = async (message, title = 'Confirm') => {
                return Alert.confirm({ message, title });
            };
        }
    }

    /**
     * Get the original Modal class for advanced usage
     */
    getModalClass() {
        return Modal;
    }

    /**
     * Get the original Alert class for advanced usage
     */
    getAlertClass() {
        return Alert;
    }

    /**
     * Get the original DataTable class for advanced usage
     */
    getDataTableClass() {
        return DataTable;
    }
}

// Export individual wrappers for direct use
export { LegacyModalWrapper, LegacyAlertWrapper, LegacyTableWrapper };

// Export native components for convenience
export {
    Modal,
    Alert,
    DataTable,
    Form,
    Button,
    ButtonGroup,
    Badge,
    StatusBadge,
    CountBadge,
    Card,
    StatCard,
    DatePicker,
    Loader,
    Skeleton,
    showLoading,
    showFullPageLoading,
    Tooltip,
    initTooltips,
    destroyAllTooltips,
    Input,
    Textarea,
    Select,
    Pagination
};

// Default export
export default LegacyAdapter;
