/**
 * Tests for Button Component
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
global.HTMLButtonElement = dom.window.HTMLButtonElement;

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
const { Button, ButtonGroup, ButtonIcons } = require('../../../static/src/components/Button.js');

describe('Button Component', () => {
  beforeEach(() => {
    // Clear document body
    document.body.innerHTML = '';
  });

  describe('Basic Creation', () => {
    test('creates button element', () => {
      const button = Button({ text: 'Click me' });

      expect(button).toBeTruthy();
      expect(button.tagName).toBe('BUTTON');
    });

    test('sets button text', () => {
      const button = Button({ text: 'Test Button' });

      expect(button.textContent).toContain('Test Button');
    });

    test('sets button type', () => {
      const button = Button({ text: 'Submit', type: 'submit' });

      expect(button.type).toBe('submit');
    });

    test('defaults to type="button"', () => {
      const button = Button({ text: 'Test' });

      expect(button.type).toBe('button');
    });

    test('escapes HTML in text', () => {
      const button = Button({ text: '<script>alert(1)</script>' });

      expect(button.innerHTML).not.toContain('<script>');
      expect(button.textContent).toContain('<script>');
    });
  });

  describe('Variants', () => {
    const variants = ['primary', 'secondary', 'danger', 'success', 'warning', 'ghost', 'glass'];

    variants.forEach(variant => {
      test(`applies ${variant} variant class`, () => {
        const button = Button({ text: 'Test', variant });

        expect(button.classList.contains(`btn-${variant}`)).toBe(true);
      });
    });

    test('defaults to primary variant', () => {
      const button = Button({ text: 'Test' });

      expect(button.classList.contains('btn-primary')).toBe(true);
    });
  });

  describe('Sizes', () => {
    const sizes = ['small', 'medium', 'large'];

    sizes.forEach(size => {
      test(`applies ${size} size class`, () => {
        const button = Button({ text: 'Test', size });

        expect(button.classList.contains(`btn-${size}`)).toBe(true);
      });
    });

    test('defaults to medium size', () => {
      const button = Button({ text: 'Test' });

      expect(button.classList.contains('btn-medium')).toBe(true);
    });
  });

  describe('Icons', () => {
    test('renders leading icon', () => {
      const button = Button({
        text: 'Save',
        icon: '<svg>icon</svg>'
      });

      const iconSpan = button.querySelector('.btn-icon');
      expect(iconSpan).toBeTruthy();
      expect(iconSpan.innerHTML).toContain('svg');
    });

    test('renders trailing icon', () => {
      const button = Button({
        text: 'Next',
        iconAfter: '<svg>arrow</svg>'
      });

      const iconSpan = button.querySelector('.btn-icon-after');
      expect(iconSpan).toBeTruthy();
    });

    test('creates icon-only button', () => {
      const button = Button({
        icon: '<svg>icon</svg>',
        iconOnly: true,
        ariaLabel: 'Icon button'
      });

      expect(button.classList.contains('btn-icon-only')).toBe(true);
      expect(button.querySelector('.btn-text')).toBeFalsy();
    });

    test('icon-only button uses text as aria-label', () => {
      const button = Button({
        text: 'Delete',
        icon: '<svg>icon</svg>',
        iconOnly: true
      });

      expect(button.getAttribute('aria-label')).toBe('Delete');
    });
  });

  describe('States', () => {
    test('creates disabled button', () => {
      const button = Button({ text: 'Disabled', disabled: true });

      expect(button.disabled).toBe(true);
    });

    test('creates loading button', () => {
      const button = Button({ text: 'Loading', loading: true });

      expect(button.classList.contains('btn-loading')).toBe(true);
      expect(button.getAttribute('aria-busy')).toBe('true');
    });

    test('shows spinner when loading', () => {
      const button = Button({ text: 'Loading', loading: true });

      const spinner = button.querySelector('.btn-spinner');
      expect(spinner).toBeTruthy();
    });

    test('shows loading text when provided', () => {
      const button = Button({
        text: 'Save',
        loading: true,
        loadingText: 'Saving...'
      });

      expect(button.textContent).toContain('Saving...');
    });

    test('hides icon when loading', () => {
      const button = Button({
        text: 'Save',
        icon: '<svg>icon</svg>',
        loading: true
      });

      const icon = button.querySelector('.btn-icon:not(.btn-spinner .btn-icon)');
      expect(icon).toBeFalsy();
    });
  });

  describe('Full Width', () => {
    test('applies full width class', () => {
      const button = Button({ text: 'Full', fullWidth: true });

      expect(button.classList.contains('btn-full')).toBe(true);
    });
  });

  describe('Custom Classes', () => {
    test('applies additional CSS classes', () => {
      const button = Button({
        text: 'Custom',
        className: 'my-custom-class another-class'
      });

      expect(button.classList.contains('my-custom-class')).toBe(true);
      expect(button.classList.contains('another-class')).toBe(true);
    });
  });

  describe('Custom Attributes', () => {
    test('sets additional HTML attributes', () => {
      const button = Button({
        text: 'Custom',
        attributes: {
          'data-testid': 'my-button',
          'data-action': 'submit'
        }
      });

      expect(button.getAttribute('data-testid')).toBe('my-button');
      expect(button.getAttribute('data-action')).toBe('submit');
    });
  });

  describe('ARIA Accessibility', () => {
    test('sets aria-label when provided', () => {
      const button = Button({
        text: 'Button',
        ariaLabel: 'Custom aria label'
      });

      expect(button.getAttribute('aria-label')).toBe('Custom aria label');
    });

    test('sets aria-busy when loading', () => {
      const button = Button({ text: 'Loading', loading: true });

      expect(button.getAttribute('aria-busy')).toBe('true');
    });

    test('icon-only button has aria-label', () => {
      const button = Button({
        icon: '<svg>icon</svg>',
        iconOnly: true,
        ariaLabel: 'Settings'
      });

      expect(button.getAttribute('aria-label')).toBe('Settings');
    });

    test('icon span has aria-hidden', () => {
      const button = Button({
        text: 'Save',
        icon: '<svg>icon</svg>'
      });

      const iconSpan = button.querySelector('.btn-icon');
      expect(iconSpan.getAttribute('aria-hidden')).toBe('true');
    });
  });

  describe('Event Handling', () => {
    test('calls onClick handler', () => {
      const onClick = jest.fn();
      const button = Button({ text: 'Click', onClick });

      button.click();

      expect(onClick).toHaveBeenCalled();
    });

    test('does not call onClick when disabled', () => {
      const onClick = jest.fn();
      const button = Button({ text: 'Disabled', disabled: true, onClick });

      button.click();

      expect(onClick).not.toHaveBeenCalled();
    });

    test('does not call onClick when loading', () => {
      const onClick = jest.fn();
      const button = Button({ text: 'Loading', loading: true, onClick });

      button.click();

      expect(onClick).not.toHaveBeenCalled();
    });
  });

  describe('Helper Methods', () => {
    describe('setLoading()', () => {
      test('enables loading state', () => {
        const button = Button({ text: 'Save' });

        button.setLoading(true);

        expect(button.classList.contains('btn-loading')).toBe(true);
        expect(button.getAttribute('aria-busy')).toBe('true');
      });

      test('disables loading state', () => {
        const button = Button({ text: 'Save', loading: true });

        button.setLoading(false);

        expect(button.classList.contains('btn-loading')).toBe(false);
        expect(button.getAttribute('aria-busy')).toBe('false');
      });

      test('updates loading text', () => {
        const button = Button({ text: 'Save' });

        button.setLoading(true, 'Saving...');

        expect(button.textContent).toContain('Saving...');
      });
    });

    describe('setDisabled()', () => {
      test('enables disabled state', () => {
        const button = Button({ text: 'Test' });

        button.setDisabled(true);

        expect(button.disabled).toBe(true);
      });

      test('disables disabled state', () => {
        const button = Button({ text: 'Test', disabled: true });

        button.setDisabled(false);

        expect(button.disabled).toBe(false);
      });
    });

    describe('setText()', () => {
      test('updates button text', () => {
        const button = Button({ text: 'Original' });

        button.setText('Updated');

        expect(button.textContent).toContain('Updated');
      });
    });
  });
});

describe('ButtonGroup Component', () => {
  beforeEach(() => {
    document.body.innerHTML = '';
  });

  test('creates button group', () => {
    const buttons = [
      Button({ text: 'One' }),
      Button({ text: 'Two' })
    ];

    const group = ButtonGroup(buttons);

    expect(group.tagName).toBe('DIV');
    expect(group.classList.contains('btn-group')).toBe(true);
  });

  test('contains all buttons', () => {
    const buttons = [
      Button({ text: 'One' }),
      Button({ text: 'Two' }),
      Button({ text: 'Three' })
    ];

    const group = ButtonGroup(buttons);

    expect(group.children.length).toBe(3);
  });

  test('applies horizontal direction by default', () => {
    const buttons = [Button({ text: 'One' })];
    const group = ButtonGroup(buttons);

    expect(group.classList.contains('btn-group-horizontal')).toBe(true);
  });

  test('applies vertical direction', () => {
    const buttons = [Button({ text: 'One' })];
    const group = ButtonGroup(buttons, { direction: 'vertical' });

    expect(group.classList.contains('btn-group-vertical')).toBe(true);
  });

  test('applies custom class', () => {
    const buttons = [Button({ text: 'One' })];
    const group = ButtonGroup(buttons, { className: 'custom-group' });

    expect(group.classList.contains('custom-group')).toBe(true);
  });

  test('has role="group"', () => {
    const buttons = [Button({ text: 'One' })];
    const group = ButtonGroup(buttons);

    expect(group.getAttribute('role')).toBe('group');
  });
});

describe('ButtonIcons', () => {
  test('exports predefined icons', () => {
    expect(ButtonIcons.plus).toBeTruthy();
    expect(ButtonIcons.edit).toBeTruthy();
    expect(ButtonIcons.delete).toBeTruthy();
    expect(ButtonIcons.save).toBeTruthy();
    expect(ButtonIcons.download).toBeTruthy();
    expect(ButtonIcons.upload).toBeTruthy();
    expect(ButtonIcons.refresh).toBeTruthy();
    expect(ButtonIcons.search).toBeTruthy();
    expect(ButtonIcons.close).toBeTruthy();
    expect(ButtonIcons.check).toBeTruthy();
    expect(ButtonIcons.settings).toBeTruthy();
  });

  test('icons are SVG strings', () => {
    Object.values(ButtonIcons).forEach(icon => {
      expect(icon).toContain('<svg');
      expect(icon).toContain('</svg>');
    });
  });

  test('icons can be used with Button', () => {
    const button = Button({
      text: 'Edit',
      icon: ButtonIcons.edit
    });

    const iconSpan = button.querySelector('.btn-icon');
    expect(iconSpan.innerHTML).toContain('svg');
  });
});
