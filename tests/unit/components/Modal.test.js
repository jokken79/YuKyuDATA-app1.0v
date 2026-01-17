/**
 * Tests for Modal Component
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
global.cancelAnimationFrame = (id) => clearTimeout(id);

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
const { Modal } = require('../../../static/src/components/Modal.js');

describe('Modal Component', () => {
  beforeEach(() => {
    // Clear document body
    document.body.innerHTML = '';
    // Clear active modals
    Modal.activeModals.clear();
    Modal.zIndexCounter = 10000;
  });

  afterEach(() => {
    // Close all modals
    Modal.closeAll();
  });

  describe('Constructor', () => {
    test('creates modal with default options', () => {
      const modal = new Modal();

      expect(modal.title).toBe('');
      expect(modal.content).toBe('');
      expect(modal.size).toBe('medium');
      expect(modal.closable).toBe(true);
      expect(modal.closeOnEscape).toBe(true);
      expect(modal.closeOnBackdrop).toBe(true);
      expect(modal.isOpen).toBe(false);
    });

    test('creates modal with custom title', () => {
      const modal = new Modal({ title: 'Test Title' });
      expect(modal.title).toBe('Test Title');
    });

    test('creates modal with custom content', () => {
      const modal = new Modal({ content: '<p>Test content</p>' });
      expect(modal.content).toBe('<p>Test content</p>');
    });

    test('creates modal with different sizes', () => {
      const sizes = ['small', 'medium', 'large', 'xlarge', 'fullscreen'];

      sizes.forEach(size => {
        const modal = new Modal({ size });
        expect(modal.size).toBe(size);
      });
    });

    test('respects closable option', () => {
      const closableModal = new Modal({ closable: true });
      const nonClosableModal = new Modal({ closable: false });

      expect(closableModal.closable).toBe(true);
      expect(nonClosableModal.closable).toBe(false);
    });

    test('sets custom id', () => {
      const modal = new Modal({ id: 'custom-modal-id' });
      expect(modal.id).toBe('custom-modal-id');
    });

    test('generates unique id when not provided', () => {
      const modal1 = new Modal();
      const modal2 = new Modal();

      expect(modal1.id).not.toBe(modal2.id);
      expect(modal1.id).toMatch(/^modal-\d+-[a-z0-9]+$/);
    });

    test('sets ariaLabel from title when not provided', () => {
      const modal = new Modal({ title: 'Dialog Title' });
      expect(modal.ariaLabel).toBe('Dialog Title');
    });

    test('uses custom ariaLabel when provided', () => {
      const modal = new Modal({ title: 'Title', ariaLabel: 'Custom Label' });
      expect(modal.ariaLabel).toBe('Custom Label');
    });
  });

  describe('open()', () => {
    test('opens modal and sets isOpen to true', () => {
      const modal = new Modal({ title: 'Test' });
      modal.open();

      expect(modal.isOpen).toBe(true);
    });

    test('adds modal to DOM', () => {
      const modal = new Modal({ title: 'Test' });
      modal.open();

      const backdrop = document.querySelector('.modal-backdrop');
      expect(backdrop).toBeTruthy();
    });

    test('adds modal to activeModals registry', () => {
      const modal = new Modal({ title: 'Test' });
      modal.open();

      expect(Modal.activeModals.has(modal.id)).toBe(true);
    });

    test('prevents body scroll', () => {
      const modal = new Modal({ title: 'Test' });
      modal.open();

      expect(document.body.style.overflow).toBe('hidden');
    });

    test('calls onOpen callback', () => {
      const onOpen = jest.fn();
      const modal = new Modal({ title: 'Test', onOpen });
      modal.open();

      expect(onOpen).toHaveBeenCalledWith(modal);
    });

    test('returns modal instance for chaining', () => {
      const modal = new Modal({ title: 'Test' });
      const result = modal.open();

      expect(result).toBe(modal);
    });

    test('does not re-open if already open', () => {
      const onOpen = jest.fn();
      const modal = new Modal({ title: 'Test', onOpen });

      modal.open();
      modal.open();

      expect(onOpen).toHaveBeenCalledTimes(1);
    });

    test('increments z-index for stacking', () => {
      const modal1 = new Modal({ title: 'Modal 1' });
      const modal2 = new Modal({ title: 'Modal 2' });

      modal1.open();
      const zIndex1 = parseInt(modal1.element.style.zIndex);

      modal2.open();
      const zIndex2 = parseInt(modal2.element.style.zIndex);

      expect(zIndex2).toBeGreaterThan(zIndex1);
    });

    test('dispatches modal:open event', (done) => {
      const modal = new Modal({ title: 'Test' });

      setTimeout(() => {
        modal.element.addEventListener('modal:open', (e) => {
          expect(e.detail.modal).toBe(modal);
          done();
        });
      }, 0);

      modal.open();
    });
  });

  describe('close()', () => {
    test('closes modal and sets isOpen to false', (done) => {
      const modal = new Modal({ title: 'Test' });
      modal.open();
      modal.close();

      setTimeout(() => {
        expect(modal.isOpen).toBe(false);
        done();
      }, 350);
    });

    test('removes modal from DOM', (done) => {
      const modal = new Modal({ title: 'Test' });
      modal.open();
      modal.close();

      setTimeout(() => {
        const backdrop = document.querySelector('.modal-backdrop');
        expect(backdrop).toBeFalsy();
        done();
      }, 350);
    });

    test('removes modal from activeModals registry', (done) => {
      const modal = new Modal({ title: 'Test' });
      modal.open();
      modal.close();

      setTimeout(() => {
        expect(Modal.activeModals.has(modal.id)).toBe(false);
        done();
      }, 350);
    });

    test('restores body scroll when last modal closes', (done) => {
      const modal = new Modal({ title: 'Test' });
      modal.open();
      modal.close();

      setTimeout(() => {
        expect(document.body.style.overflow).toBe('');
        done();
      }, 350);
    });

    test('calls onClose callback', (done) => {
      const onClose = jest.fn();
      const modal = new Modal({ title: 'Test', onClose });
      modal.open();
      modal.close();

      setTimeout(() => {
        expect(onClose).toHaveBeenCalledWith(modal);
        done();
      }, 350);
    });

    test('returns modal instance for chaining', () => {
      const modal = new Modal({ title: 'Test' });
      modal.open();
      const result = modal.close();

      expect(result).toBe(modal);
    });

    test('does nothing if not open', () => {
      const onClose = jest.fn();
      const modal = new Modal({ title: 'Test', onClose });

      modal.close();

      expect(onClose).not.toHaveBeenCalled();
    });
  });

  describe('ARIA Accessibility', () => {
    test('has role="dialog"', () => {
      const modal = new Modal({ title: 'Test' });
      modal.open();

      const dialogEl = document.querySelector('.modal');
      expect(dialogEl.getAttribute('role')).toBe('dialog');
    });

    test('has aria-modal="true"', () => {
      const modal = new Modal({ title: 'Test' });
      modal.open();

      const dialogEl = document.querySelector('.modal');
      expect(dialogEl.getAttribute('aria-modal')).toBe('true');
    });

    test('has aria-labelledby pointing to title', () => {
      const modal = new Modal({ title: 'Test', id: 'test-modal' });
      modal.open();

      const dialogEl = document.querySelector('.modal');
      expect(dialogEl.getAttribute('aria-labelledby')).toBe('test-modal-title');
    });

    test('has aria-describedby pointing to content', () => {
      const modal = new Modal({ title: 'Test', id: 'test-modal' });
      modal.open();

      const dialogEl = document.querySelector('.modal');
      expect(dialogEl.getAttribute('aria-describedby')).toBe('test-modal-content');
    });

    test('has aria-label when ariaLabel is set', () => {
      const modal = new Modal({ title: 'Test', ariaLabel: 'Custom label' });
      modal.open();

      const dialogEl = document.querySelector('.modal');
      expect(dialogEl.getAttribute('aria-label')).toBe('Custom label');
    });

    test('close button has aria-label', () => {
      const modal = new Modal({ title: 'Test', closable: true });
      modal.open();

      const closeBtn = document.querySelector('.modal-close');
      expect(closeBtn.getAttribute('aria-label')).toBeTruthy();
    });
  });

  describe('Keyboard Interaction', () => {
    test('closes on Escape key when closeOnEscape is true', (done) => {
      const modal = new Modal({ title: 'Test', closeOnEscape: true });
      modal.open();

      const event = new dom.window.KeyboardEvent('keydown', { key: 'Escape' });
      document.dispatchEvent(event);

      setTimeout(() => {
        expect(modal.isOpen).toBe(false);
        done();
      }, 350);
    });

    test('does not close on Escape when closeOnEscape is false', () => {
      const modal = new Modal({ title: 'Test', closeOnEscape: false });
      modal.open();

      const event = new dom.window.KeyboardEvent('keydown', { key: 'Escape' });
      document.dispatchEvent(event);

      expect(modal.isOpen).toBe(true);
    });

    test('does not close on Escape when closable is false', () => {
      const modal = new Modal({ title: 'Test', closable: false, closeOnEscape: true });
      modal.open();

      const event = new dom.window.KeyboardEvent('keydown', { key: 'Escape' });
      document.dispatchEvent(event);

      expect(modal.isOpen).toBe(true);
    });
  });

  describe('Content Management', () => {
    test('setContent updates content when open', () => {
      const modal = new Modal({ title: 'Test', content: 'Original' });
      modal.open();
      modal.setContent('Updated content');

      const body = document.querySelector('.modal-body');
      expect(body.innerHTML).toBe('Updated content');
    });

    test('setContent accepts HTMLElement', () => {
      const modal = new Modal({ title: 'Test' });
      modal.open();

      const div = document.createElement('div');
      div.textContent = 'Element content';
      modal.setContent(div);

      const body = document.querySelector('.modal-body');
      expect(body.textContent).toBe('Element content');
    });

    test('setTitle updates title when open', () => {
      const modal = new Modal({ title: 'Original' });
      modal.open();
      modal.setTitle('Updated title');

      const titleEl = document.querySelector('.modal-title');
      expect(titleEl.textContent).toBe('Updated title');
    });

    test('setLoading disables buttons', () => {
      const modal = new Modal({
        title: 'Test',
        onConfirm: () => {}
      });
      modal.open();
      modal.setLoading(true);

      const buttons = document.querySelectorAll('.modal-footer button');
      buttons.forEach(btn => {
        expect(btn.disabled).toBe(true);
      });
    });
  });

  describe('Buttons', () => {
    test('renders custom buttons', () => {
      const modal = new Modal({
        title: 'Test',
        buttons: [
          { text: 'Cancel', variant: 'ghost' },
          { text: 'Save', variant: 'primary' }
        ]
      });
      modal.open();

      const buttons = document.querySelectorAll('.modal-footer button');
      expect(buttons.length).toBe(2);
      expect(buttons[0].textContent).toBe('Cancel');
      expect(buttons[1].textContent).toBe('Save');
    });

    test('creates default buttons when onConfirm is set', () => {
      const modal = new Modal({
        title: 'Test',
        onConfirm: jest.fn()
      });
      modal.open();

      const buttons = document.querySelectorAll('.modal-footer button');
      expect(buttons.length).toBe(2);
    });

    test('calls onConfirm when confirm button clicked', () => {
      const onConfirm = jest.fn();
      const modal = new Modal({
        title: 'Test',
        onConfirm
      });
      modal.open();

      const confirmBtn = document.querySelector('.modal-footer .btn-primary');
      confirmBtn.click();

      expect(onConfirm).toHaveBeenCalledWith(modal);
    });
  });

  describe('Static Methods', () => {
    describe('Modal.alert()', () => {
      test('shows alert modal with message', async () => {
        const promise = Modal.alert('Test message', 'Alert Title');

        const modal = document.querySelector('.modal');
        expect(modal).toBeTruthy();
        expect(document.querySelector('.modal-title').textContent).toBe('Alert Title');
        expect(document.querySelector('.modal-body').textContent).toContain('Test message');

        // Click OK to close
        document.querySelector('.modal-footer button').click();

        await promise;
      });
    });

    describe('Modal.confirm()', () => {
      test('shows confirm modal and resolves true on confirm', async () => {
        const promise = Modal.confirm('Are you sure?', 'Confirm');

        expect(document.querySelector('.modal')).toBeTruthy();

        // Click confirm button
        const buttons = document.querySelectorAll('.modal-footer button');
        buttons[1].click(); // Second button is confirm

        const result = await promise;
        expect(result).toBe(true);
      });

      test('shows confirm modal and resolves false on cancel', async () => {
        const promise = Modal.confirm('Are you sure?', 'Confirm');

        // Click cancel button
        const buttons = document.querySelectorAll('.modal-footer button');
        buttons[0].click(); // First button is cancel

        const result = await promise;
        expect(result).toBe(false);
      });
    });

    describe('Modal.prompt()', () => {
      test('shows prompt modal with input', async () => {
        const promise = Modal.prompt('Enter name:', 'default value', 'Input');

        const input = document.querySelector('.modal input');
        expect(input).toBeTruthy();
        expect(input.value).toBe('default value');

        // Simulate input change and confirm
        input.value = 'new value';
        const buttons = document.querySelectorAll('.modal-footer button');
        buttons[1].click();

        const result = await promise;
        expect(result).toBe('new value');
      });

      test('returns null when cancelled', async () => {
        const promise = Modal.prompt('Enter name:');

        const buttons = document.querySelectorAll('.modal-footer button');
        buttons[0].click(); // Cancel

        const result = await promise;
        expect(result).toBe(null);
      });
    });

    describe('Modal.closeAll()', () => {
      test('closes all active modals', (done) => {
        const modal1 = new Modal({ title: 'Modal 1' });
        const modal2 = new Modal({ title: 'Modal 2' });

        modal1.open();
        modal2.open();

        Modal.closeAll();

        setTimeout(() => {
          expect(Modal.activeModals.size).toBe(0);
          done();
        }, 350);
      });
    });
  });

  describe('destroy()', () => {
    test('destroys modal and cleans up', (done) => {
      const modal = new Modal({ title: 'Test' });
      modal.open();
      modal.destroy();

      setTimeout(() => {
        expect(modal.element).toBe(null);
        expect(modal.backdrop).toBe(null);
        done();
      }, 350);
    });
  });
});
