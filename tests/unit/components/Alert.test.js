/**
 * Tests for Alert Component (Toast/Confirm)
 * YuKyuDATA Design System
 */

const { JSDOM } = require('jsdom');

// Setup DOM environment before imports
const dom = new JSDOM('<!DOCTYPE html><html><head></head><body></body></html>', {
  url: 'http://localhost'
});
global.document = dom.window.document;
global.window = dom.window;
global.HTMLElement = dom.window.HTMLElement;
global.requestAnimationFrame = (cb) => setTimeout(cb, 0);

// Mock escapeHtml
jest.mock('../../../static/js/modules/utils.js', () => ({
  escapeHtml: (str) => {
    if (str === null || str === undefined) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }
}));

// Import after mocks
const { Alert } = require('../../../static/src/components/Alert.js');

describe('Alert Component', () => {
  beforeEach(() => {
    document.body.innerHTML = '';
    // Clear static state
    Alert.containers.clear();
    Alert.activeToasts.clear();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
    Alert.dismissAll();
  });

  describe('Toast Notifications', () => {
    describe('Basic Toast', () => {
      test('creates toast element', () => {
        Alert.toast({ message: 'Test message' });
        jest.advanceTimersByTime(10);

        const toast = document.querySelector('.toast');
        expect(toast).toBeTruthy();
      });

      test('displays message', () => {
        Alert.toast({ message: 'Hello World' });
        jest.advanceTimersByTime(10);

        const message = document.querySelector('.toast-message');
        expect(message.textContent).toBe('Hello World');
      });

      test('displays title when provided', () => {
        Alert.toast({ message: 'Message', title: 'Title' });
        jest.advanceTimersByTime(10);

        const title = document.querySelector('.toast-title');
        expect(title).toBeTruthy();
        expect(title.textContent).toBe('Title');
      });

      test('returns toast ID', () => {
        const id = Alert.toast({ message: 'Test' });

        expect(id).toBeTruthy();
        expect(id).toMatch(/^toast-\d+-[a-z0-9]+$/);
      });

      test('escapes HTML in message', () => {
        Alert.toast({ message: '<script>alert(1)</script>' });
        jest.advanceTimersByTime(10);

        const message = document.querySelector('.toast-message');
        expect(message.innerHTML).not.toContain('<script>');
        expect(message.textContent).toContain('<script>');
      });
    });

    describe('Toast Types', () => {
      const types = ['success', 'error', 'warning', 'info'];

      types.forEach(type => {
        test(`creates ${type} toast`, () => {
          Alert.toast({ message: 'Test', type });
          jest.advanceTimersByTime(10);

          const toast = document.querySelector('.toast');
          expect(toast.classList.contains(type)).toBe(true);
        });
      });

      test('defaults to info type', () => {
        Alert.toast({ message: 'Test' });
        jest.advanceTimersByTime(10);

        const toast = document.querySelector('.toast');
        expect(toast.classList.contains('info')).toBe(true);
      });
    });

    describe('Toast Positions', () => {
      const positions = ['top-right', 'top-left', 'bottom-right', 'bottom-left', 'top-center', 'bottom-center'];

      positions.forEach(position => {
        test(`positions toast at ${position}`, () => {
          Alert.toast({ message: 'Test', position });
          jest.advanceTimersByTime(10);

          const container = document.querySelector('.toast-container');
          expect(container.classList.contains(position)).toBe(true);
        });
      });

      test('defaults to top-right position', () => {
        Alert.toast({ message: 'Test' });
        jest.advanceTimersByTime(10);

        const container = document.querySelector('.toast-container');
        expect(container.classList.contains('top-right')).toBe(true);
      });
    });

    describe('Toast Duration', () => {
      test('auto-dismisses after duration', () => {
        Alert.toast({ message: 'Test', duration: 3000 });
        jest.advanceTimersByTime(10);

        expect(document.querySelector('.toast')).toBeTruthy();

        jest.advanceTimersByTime(3500);

        const toast = document.querySelector('.toast.show');
        expect(toast).toBeFalsy();
      });

      test('persists when duration is 0', () => {
        Alert.toast({ message: 'Test', duration: 0 });
        jest.advanceTimersByTime(10);

        expect(document.querySelector('.toast')).toBeTruthy();

        jest.advanceTimersByTime(10000);

        expect(document.querySelector('.toast')).toBeTruthy();
      });

      test('shows progress bar for timed toasts', () => {
        Alert.toast({ message: 'Test', duration: 4000 });
        jest.advanceTimersByTime(10);

        const progress = document.querySelector('.toast-progress');
        expect(progress).toBeTruthy();
      });

      test('hides progress bar when duration is 0', () => {
        Alert.toast({ message: 'Test', duration: 0 });
        jest.advanceTimersByTime(10);

        const progress = document.querySelector('.toast-progress');
        expect(progress).toBeFalsy();
      });
    });

    describe('Toast Close Button', () => {
      test('shows close button when closable', () => {
        Alert.toast({ message: 'Test', closable: true });
        jest.advanceTimersByTime(10);

        const closeBtn = document.querySelector('.toast-close');
        expect(closeBtn).toBeTruthy();
      });

      test('hides close button when not closable', () => {
        Alert.toast({ message: 'Test', closable: false });
        jest.advanceTimersByTime(10);

        const closeBtn = document.querySelector('.toast-close');
        expect(closeBtn).toBeFalsy();
      });

      test('closes toast on close button click', () => {
        Alert.toast({ message: 'Test', duration: 0, closable: true });
        jest.advanceTimersByTime(10);

        const closeBtn = document.querySelector('.toast-close');
        closeBtn.click();

        jest.advanceTimersByTime(500);

        expect(document.querySelector('.toast')).toBeFalsy();
      });
    });

    describe('Toast Callbacks', () => {
      test('calls onClose when toast closes', () => {
        const onClose = jest.fn();
        Alert.toast({ message: 'Test', duration: 1000, onClose });
        jest.advanceTimersByTime(10);

        jest.advanceTimersByTime(1500);

        expect(onClose).toHaveBeenCalled();
      });
    });

    describe('Toast Action Button', () => {
      test('renders action button', () => {
        Alert.toast({
          message: 'Test',
          action: { text: 'Undo', onClick: jest.fn() }
        });
        jest.advanceTimersByTime(10);

        const actionBtn = document.querySelector('.toast-action-btn');
        expect(actionBtn).toBeTruthy();
        expect(actionBtn.textContent).toBe('Undo');
      });

      test('calls action onClick', () => {
        const onClick = jest.fn();
        Alert.toast({
          message: 'Test',
          action: { text: 'Undo', onClick },
          duration: 0
        });
        jest.advanceTimersByTime(10);

        const actionBtn = document.querySelector('.toast-action-btn');
        actionBtn.click();

        expect(onClick).toHaveBeenCalled();
      });

      test('closes toast after action click', () => {
        Alert.toast({
          message: 'Test',
          action: { text: 'Undo', onClick: jest.fn() },
          duration: 0
        });
        jest.advanceTimersByTime(10);

        const actionBtn = document.querySelector('.toast-action-btn');
        actionBtn.click();

        jest.advanceTimersByTime(500);

        expect(document.querySelector('.toast')).toBeFalsy();
      });
    });

    describe('ARIA Accessibility', () => {
      test('toast has role="alert"', () => {
        Alert.toast({ message: 'Test' });
        jest.advanceTimersByTime(10);

        const toast = document.querySelector('.toast');
        expect(toast.getAttribute('role')).toBe('alert');
      });

      test('toast has aria-atomic="true"', () => {
        Alert.toast({ message: 'Test' });
        jest.advanceTimersByTime(10);

        const toast = document.querySelector('.toast');
        expect(toast.getAttribute('aria-atomic')).toBe('true');
      });

      test('container has role="region"', () => {
        Alert.toast({ message: 'Test' });
        jest.advanceTimersByTime(10);

        const container = document.querySelector('.toast-container');
        expect(container.getAttribute('role')).toBe('region');
      });

      test('container has aria-live="polite"', () => {
        Alert.toast({ message: 'Test' });
        jest.advanceTimersByTime(10);

        const container = document.querySelector('.toast-container');
        expect(container.getAttribute('aria-live')).toBe('polite');
      });

      test('close button has aria-label', () => {
        Alert.toast({ message: 'Test', closable: true });
        jest.advanceTimersByTime(10);

        const closeBtn = document.querySelector('.toast-close');
        expect(closeBtn.getAttribute('aria-label')).toBeTruthy();
      });
    });
  });

  describe('Shorthand Methods', () => {
    test('Alert.success() creates success toast', () => {
      Alert.success('Success message', 'Success');
      jest.advanceTimersByTime(10);

      const toast = document.querySelector('.toast');
      expect(toast.classList.contains('success')).toBe(true);
    });

    test('Alert.error() creates error toast', () => {
      Alert.error('Error message', 'Error');
      jest.advanceTimersByTime(10);

      const toast = document.querySelector('.toast');
      expect(toast.classList.contains('error')).toBe(true);
    });

    test('Alert.warning() creates warning toast', () => {
      Alert.warning('Warning message', 'Warning');
      jest.advanceTimersByTime(10);

      const toast = document.querySelector('.toast');
      expect(toast.classList.contains('warning')).toBe(true);
    });

    test('Alert.info() creates info toast', () => {
      Alert.info('Info message', 'Info');
      jest.advanceTimersByTime(10);

      const toast = document.querySelector('.toast');
      expect(toast.classList.contains('info')).toBe(true);
    });
  });

  describe('Toast Management', () => {
    describe('dismiss()', () => {
      test('dismisses specific toast by ID', () => {
        const id = Alert.toast({ message: 'Test', duration: 0 });
        jest.advanceTimersByTime(10);

        expect(document.querySelector('.toast')).toBeTruthy();

        Alert.dismiss(id);
        jest.advanceTimersByTime(500);

        expect(document.querySelector('.toast')).toBeFalsy();
      });
    });

    describe('dismissAll()', () => {
      test('dismisses all active toasts', () => {
        Alert.toast({ message: 'Toast 1', duration: 0 });
        Alert.toast({ message: 'Toast 2', duration: 0 });
        Alert.toast({ message: 'Toast 3', duration: 0 });
        jest.advanceTimersByTime(10);

        expect(document.querySelectorAll('.toast').length).toBe(3);

        Alert.dismissAll();
        jest.advanceTimersByTime(500);

        expect(document.querySelectorAll('.toast').length).toBe(0);
      });
    });

    test('tracks active toasts', () => {
      Alert.toast({ message: 'Test 1', duration: 0 });
      Alert.toast({ message: 'Test 2', duration: 0 });
      jest.advanceTimersByTime(10);

      expect(Alert.activeToasts.size).toBe(2);
    });
  });

  describe('Confirm Dialog', () => {
    describe('Basic Confirm', () => {
      test('creates confirm overlay', async () => {
        Alert.confirm({ message: 'Are you sure?' });
        jest.advanceTimersByTime(10);

        const overlay = document.querySelector('.confirm-overlay');
        expect(overlay).toBeTruthy();
      });

      test('displays message', async () => {
        Alert.confirm({ message: 'Delete this item?' });
        jest.advanceTimersByTime(10);

        const message = document.querySelector('#confirm-message');
        expect(message.textContent).toBe('Delete this item?');
      });

      test('displays title', async () => {
        Alert.confirm({ message: 'Test', title: 'Confirm Action' });
        jest.advanceTimersByTime(10);

        const title = document.querySelector('#confirm-title');
        expect(title.textContent).toBe('Confirm Action');
      });

      test('escapes HTML in message', async () => {
        Alert.confirm({ message: '<script>alert(1)</script>' });
        jest.advanceTimersByTime(10);

        const message = document.querySelector('#confirm-message');
        expect(message.innerHTML).not.toContain('<script>');
      });
    });

    describe('Confirm Buttons', () => {
      test('displays confirm and cancel buttons', async () => {
        Alert.confirm({ message: 'Test' });
        jest.advanceTimersByTime(10);

        const confirmBtn = document.querySelector('[data-action="confirm"]');
        const cancelBtn = document.querySelector('[data-action="cancel"]');

        expect(confirmBtn).toBeTruthy();
        expect(cancelBtn).toBeTruthy();
      });

      test('uses custom button text', async () => {
        Alert.confirm({
          message: 'Test',
          confirmText: '削除',
          cancelText: '戻る'
        });
        jest.advanceTimersByTime(10);

        const confirmBtn = document.querySelector('[data-action="confirm"]');
        const cancelBtn = document.querySelector('[data-action="cancel"]');

        expect(confirmBtn.textContent).toBe('削除');
        expect(cancelBtn.textContent).toBe('戻る');
      });
    });

    describe('Confirm Resolution', () => {
      test('resolves true when confirm clicked', async () => {
        jest.useRealTimers();

        const promise = Alert.confirm({ message: 'Test' });

        await new Promise(r => setTimeout(r, 10));

        const confirmBtn = document.querySelector('[data-action="confirm"]');
        confirmBtn.click();

        const result = await promise;
        expect(result).toBe(true);
      });

      test('resolves false when cancel clicked', async () => {
        jest.useRealTimers();

        const promise = Alert.confirm({ message: 'Test' });

        await new Promise(r => setTimeout(r, 10));

        const cancelBtn = document.querySelector('[data-action="cancel"]');
        cancelBtn.click();

        const result = await promise;
        expect(result).toBe(false);
      });

      test('resolves false when backdrop clicked', async () => {
        jest.useRealTimers();

        const promise = Alert.confirm({ message: 'Test' });

        await new Promise(r => setTimeout(r, 10));

        const overlay = document.querySelector('.confirm-overlay');
        overlay.click();

        const result = await promise;
        expect(result).toBe(false);
      });

      test('resolves false when Escape pressed', async () => {
        jest.useRealTimers();

        const promise = Alert.confirm({ message: 'Test' });

        await new Promise(r => setTimeout(r, 10));

        const event = new dom.window.KeyboardEvent('keydown', { key: 'Escape' });
        document.dispatchEvent(event);

        const result = await promise;
        expect(result).toBe(false);
      });
    });

    describe('Confirm Types', () => {
      test('applies info type', async () => {
        Alert.confirm({ message: 'Test', type: 'info' });
        jest.advanceTimersByTime(10);

        const icon = document.querySelector('.confirm-icon');
        expect(icon.classList.contains('info')).toBe(true);
      });

      test('applies warning type', async () => {
        Alert.confirm({ message: 'Test', type: 'warning' });
        jest.advanceTimersByTime(10);

        const icon = document.querySelector('.confirm-icon');
        expect(icon.classList.contains('warning')).toBe(true);
      });

      test('applies danger type', async () => {
        Alert.confirm({ message: 'Test', dangerous: true });
        jest.advanceTimersByTime(10);

        const icon = document.querySelector('.confirm-icon');
        expect(icon.classList.contains('danger')).toBe(true);
      });
    });

    describe('Dangerous Confirm', () => {
      test('uses danger styling', async () => {
        Alert.confirm({ message: 'Test', dangerous: true });
        jest.advanceTimersByTime(10);

        const confirmBtn = document.querySelector('[data-action="confirm"]');
        expect(confirmBtn.classList.contains('confirm-btn-danger')).toBe(true);
      });
    });

    describe('ARIA Accessibility', () => {
      test('overlay has role="dialog"', async () => {
        Alert.confirm({ message: 'Test' });
        jest.advanceTimersByTime(10);

        const overlay = document.querySelector('.confirm-overlay');
        expect(overlay.getAttribute('role')).toBe('dialog');
      });

      test('overlay has aria-modal="true"', async () => {
        Alert.confirm({ message: 'Test' });
        jest.advanceTimersByTime(10);

        const overlay = document.querySelector('.confirm-overlay');
        expect(overlay.getAttribute('aria-modal')).toBe('true');
      });

      test('overlay has aria-labelledby', async () => {
        Alert.confirm({ message: 'Test' });
        jest.advanceTimersByTime(10);

        const overlay = document.querySelector('.confirm-overlay');
        expect(overlay.getAttribute('aria-labelledby')).toBe('confirm-title');
      });

      test('overlay has aria-describedby', async () => {
        Alert.confirm({ message: 'Test' });
        jest.advanceTimersByTime(10);

        const overlay = document.querySelector('.confirm-overlay');
        expect(overlay.getAttribute('aria-describedby')).toBe('confirm-message');
      });

      test('focuses confirm button on open', async () => {
        jest.useRealTimers();

        Alert.confirm({ message: 'Test' });

        await new Promise(r => setTimeout(r, 50));

        const confirmBtn = document.querySelector('[data-action="confirm"]');
        expect(document.activeElement).toBe(confirmBtn);
      });
    });
  });

  describe('confirmDanger()', () => {
    test('creates dangerous confirm dialog', async () => {
      Alert.confirmDanger('Delete item?', 'Warning');
      jest.advanceTimersByTime(10);

      const icon = document.querySelector('.confirm-icon.danger');
      expect(icon).toBeTruthy();
    });

    test('uses danger button styling', async () => {
      Alert.confirmDanger('Delete?');
      jest.advanceTimersByTime(10);

      const confirmBtn = document.querySelector('.confirm-btn-danger');
      expect(confirmBtn).toBeTruthy();
    });
  });

  describe('Multiple Toast Containers', () => {
    test('creates separate containers for different positions', () => {
      Alert.toast({ message: 'Top Right', position: 'top-right' });
      Alert.toast({ message: 'Bottom Left', position: 'bottom-left' });
      jest.advanceTimersByTime(10);

      const containers = document.querySelectorAll('.toast-container');
      expect(containers.length).toBe(2);
    });

    test('reuses containers for same position', () => {
      Alert.toast({ message: 'Toast 1', position: 'top-right' });
      Alert.toast({ message: 'Toast 2', position: 'top-right' });
      jest.advanceTimersByTime(10);

      const containers = document.querySelectorAll('.toast-container.top-right');
      expect(containers.length).toBe(1);
    });

    test('stacks toasts in same container', () => {
      Alert.toast({ message: 'Toast 1', position: 'top-right', duration: 0 });
      Alert.toast({ message: 'Toast 2', position: 'top-right', duration: 0 });
      jest.advanceTimersByTime(10);

      const container = document.querySelector('.toast-container.top-right');
      expect(container.querySelectorAll('.toast').length).toBe(2);
    });
  });
});
