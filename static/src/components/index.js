/**
 * YuKyuDATA Design System - Components Library
 * Reusable vanilla JavaScript UI components
 *
 * @module components
 * @version 1.0.0
 *
 * @example
 * // Import individual components
 * import { Modal, Button, Alert } from './components/index.js';
 *
 * // Create a modal
 * const modal = new Modal({ title: 'Hello', content: 'World' });
 * modal.open();
 *
 * // Create a button
 * const btn = Button({ text: 'Click me', variant: 'primary' });
 * document.body.appendChild(btn);
 *
 * // Show a toast
 * Alert.success('Operation completed!');
 */

// Modal - Dialog windows with glass morphism
export { Modal } from './Modal.js';

// Table - Data table with sorting, pagination, selection
export { DataTable } from './Table.js';

// Form - Dynamic forms with validation
export { Form } from './Form.js';

// Button - Buttons with variants and states
export { Button, ButtonGroup, ButtonIcons } from './Button.js';

// Alert - Toast notifications and confirm dialogs
export { Alert } from './Alert.js';

// Badge - Status badges and labels
export {
  Badge,
  StatusBadge,
  CountBadge,
  BadgeGroup,
  EmployeeTypeBadge,
  STATUS_VARIANTS,
  EMPLOYEE_TYPE_VARIANTS
} from './Badge.js';

// DatePicker - Japanese date picker with fiscal year support
export { DatePicker } from './DatePicker.js';

// Loader - Loading spinners and skeleton screens
export {
  Loader,
  Skeleton,
  showLoading,
  showFullPageLoading
} from './Loader.js';

// Tooltip - Accessible tooltips
export {
  Tooltip,
  initTooltips,
  destroyAllTooltips
} from './Tooltip.js';

// Card - Glass morphism cards
export {
  Card,
  StatCard,
  CardGroup
} from './Card.js';

// Input - Input fields with validation
export { Input, Textarea } from './Input.js';

// Select - Dropdown select with search
export { Select } from './Select.js';

// Pagination - Pagination controls
export { Pagination } from './Pagination.js';

// UIStates - Loading, Empty, Error states
export {
  UIStates,
  createLoadingState,
  createEmptyState,
  createErrorState,
  createSkeleton
} from './UIStates.js';

/**
 * Initialize all data-attribute based components
 * Call this after DOM is ready to auto-initialize components
 *
 * @example
 * // In HTML:
 * // <button data-tooltip="Help text">Hover me</button>
 *
 * // In JS:
 * import { initComponents } from './components/index.js';
 * document.addEventListener('DOMContentLoaded', initComponents);
 */
export async function initComponents() {
  // Initialize tooltips from data attributes
  const elements = document.querySelectorAll('[data-tooltip]');
  if (elements.length > 0) {
    const { initTooltips } = await import('./Tooltip.js');
    initTooltips('[data-tooltip]');
  }

  console.log('[Components] Auto-initialized');
}

/**
 * Component library version
 */
export const VERSION = '1.0.0';
