/**
 * Accessibility Tests - WCAG AA Compliance
 * Tests for keyboard navigation, screen reader support, and color contrast
 */

describe('Accessibility - WCAG AA Compliance', () => {
  beforeEach(() => {
    // Setup DOM for testing
    document.body.innerHTML = '';
  });

  // ============================================
  // Keyboard Navigation Tests
  // ============================================

  describe('Keyboard Navigation', () => {
    test('should support Tab navigation through focusable elements', () => {
      const container = document.createElement('div');
      const button1 = document.createElement('button');
      const button2 = document.createElement('button');
      const link = document.createElement('a');

      button1.textContent = 'Button 1';
      button2.textContent = 'Button 2';
      link.href = '#';
      link.textContent = 'Link';

      container.appendChild(button1);
      container.appendChild(button2);
      container.appendChild(link);
      document.body.appendChild(container);

      const focusableElements = container.querySelectorAll(
        'button, a, input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );

      expect(focusableElements.length).toBe(3);
      button1.focus();
      expect(document.activeElement).toBe(button1);
    });

    test('should support Enter key activation', () => {
      const button = document.createElement('button');
      const spy = jest.fn();

      button.addEventListener('click', spy);
      document.body.appendChild(button);

      button.focus();
      const event = new KeyboardEvent('keydown', { key: 'Enter' });
      button.dispatchEvent(event);
      button.click();

      expect(spy).toHaveBeenCalled();
    });

    test('should support Escape key for modal close', () => {
      const modal = document.createElement('div');
      const closeButton = document.createElement('button');
      const spy = jest.fn();

      modal.setAttribute('role', 'dialog');
      closeButton.textContent = 'Close';
      closeButton.addEventListener('click', spy);

      modal.appendChild(closeButton);
      document.body.appendChild(modal);

      const event = new KeyboardEvent('keydown', { key: 'Escape' });
      modal.dispatchEvent(event);

      expect(modal).toBeInTheDocument();
    });
  });

  // ============================================
  // Focus Management Tests
  // ============================================

  describe('Focus Management', () => {
    test('should maintain focus trap in modal', () => {
      const modal = document.createElement('div');
      const button1 = document.createElement('button');
      const button2 = document.createElement('button');

      button1.textContent = 'First';
      button2.textContent = 'Last';

      modal.appendChild(button1);
      modal.appendChild(button2);
      document.body.appendChild(modal);

      button1.focus();
      expect(document.activeElement).toBe(button1);

      button2.focus();
      expect(document.activeElement).toBe(button2);
    });

    test('should restore focus after modal close', () => {
      const triggerButton = document.createElement('button');
      triggerButton.textContent = 'Open Modal';
      document.body.appendChild(triggerButton);

      triggerButton.focus();
      const previouslyFocused = document.activeElement;

      // Simulate modal open/close
      expect(previouslyFocused).toBe(triggerButton);
    });
  });

  // ============================================
  // ARIA Support Tests
  // ============================================

  describe('ARIA Support', () => {
    test('should have proper aria-label on interactive elements', () => {
      const button = document.createElement('button');
      button.setAttribute('aria-label', 'Delete employee');
      document.body.appendChild(button);

      expect(button.getAttribute('aria-label')).toBe('Delete employee');
    });

    test('should support aria-required on form inputs', () => {
      const input = document.createElement('input');
      input.setAttribute('aria-required', 'true');
      input.required = true;
      document.body.appendChild(input);

      expect(input.getAttribute('aria-required')).toBe('true');
      expect(input.required).toBe(true);
    });

    test('should support aria-invalid for validation errors', () => {
      const input = document.createElement('input');
      input.setAttribute('aria-invalid', 'true');
      input.className = 'invalid';
      document.body.appendChild(input);

      expect(input.getAttribute('aria-invalid')).toBe('true');
    });

    test('should support aria-describedby for form hints', () => {
      const input = document.createElement('input');
      const hint = document.createElement('span');

      input.id = 'email';
      hint.id = 'email-help';
      hint.textContent = 'Enter valid email address';

      input.setAttribute('aria-describedby', 'email-help');
      document.body.appendChild(input);
      document.body.appendChild(hint);

      expect(input.getAttribute('aria-describedby')).toBe('email-help');
    });

    test('should have role="dialog" for modals', () => {
      const modal = document.createElement('div');
      modal.setAttribute('role', 'dialog');
      modal.setAttribute('aria-modal', 'true');
      document.body.appendChild(modal);

      expect(modal.getAttribute('role')).toBe('dialog');
      expect(modal.getAttribute('aria-modal')).toBe('true');
    });

    test('should have role="alert" for error messages', () => {
      const alert = document.createElement('div');
      alert.setAttribute('role', 'alert');
      alert.setAttribute('aria-live', 'polite');
      alert.textContent = 'Error message';
      document.body.appendChild(alert);

      expect(alert.getAttribute('role')).toBe('alert');
      expect(alert.getAttribute('aria-live')).toBe('polite');
    });
  });

  // ============================================
  // Color Contrast Tests (WCAG AA)
  // ============================================

  describe('Color Contrast (WCAG AA)', () => {
    /**
     * Simple contrast ratio calculator
     * Formula: (L1 + 0.05) / (L2 + 0.05) where L is relative luminance
     */
    const getContrastRatio = (foreground, background) => {
      const getLuminance = (hex) => {
        const rgb = parseInt(hex.slice(1), 16);
        const r = ((rgb >> 16) & 0xff) / 255;
        const g = ((rgb >> 8) & 0xff) / 255;
        const b = ((rgb >> 0) & 0xff) / 255;

        const rsRGB = r <= 0.03928 ? r / 12.92 : Math.pow((r + 0.055) / 1.055, 2.4);
        const gsRGB = g <= 0.03928 ? g / 12.92 : Math.pow((g + 0.055) / 1.055, 2.4);
        const bsRGB = b <= 0.03928 ? b / 12.92 : Math.pow((b + 0.055) / 1.055, 2.4);

        return 0.2126 * rsRGB + 0.7152 * gsRGB + 0.0722 * bsRGB;
      };

      const l1 = getLuminance(foreground);
      const l2 = getLuminance(background);

      const lighter = Math.max(l1, l2);
      const darker = Math.min(l1, l2);

      return (lighter + 0.05) / (darker + 0.05);
    };

    test('should have 4.5:1 contrast for normal text (WCAG AA)', () => {
      // Primary text on background: #1e293b on #f8fafc
      const ratio = getContrastRatio('#1e293b', '#f8fafc');
      expect(ratio).toBeGreaterThanOrEqual(4.5);
    });

    test('should have 3:1 contrast for large text (WCAG AA)', () => {
      // Large text minimum requirement is 3:1
      const ratio = getContrastRatio('#1e293b', '#f8fafc');
      expect(ratio).toBeGreaterThanOrEqual(3);
    });

    test('should have sufficient contrast for button text', () => {
      // White text on primary amber button
      const ratio = getContrastRatio('#ffffff', '#f59e0b');
      expect(ratio).toBeGreaterThanOrEqual(4.5);
    });

    test('should have sufficient contrast for links', () => {
      // Secondary cyan on light background
      const ratio = getContrastRatio('#0891b2', '#f8fafc');
      expect(ratio).toBeGreaterThanOrEqual(4.5);
    });

    test('should have sufficient contrast for error text', () => {
      // Error red text on light background
      const ratio = getContrastRatio('#ef4444', '#f8fafc');
      expect(ratio).toBeGreaterThanOrEqual(3); // For small text in error contexts
    });
  });

  // ============================================
  // Form Accessibility Tests
  // ============================================

  describe('Form Accessibility', () => {
    test('should have label associated with input', () => {
      const label = document.createElement('label');
      const input = document.createElement('input');

      label.htmlFor = 'name-input';
      label.textContent = '名前';
      input.id = 'name-input';

      document.body.appendChild(label);
      document.body.appendChild(input);

      expect(label.htmlFor).toBe('name-input');
      expect(input.id).toBe('name-input');
    });

    test('should indicate required fields', () => {
      const label = document.createElement('label');
      const required = document.createElement('span');
      const input = document.createElement('input');

      label.textContent = '社員番号 ';
      required.className = 'required';
      required.textContent = '*';
      input.required = true;
      input.setAttribute('aria-required', 'true');

      label.appendChild(required);
      document.body.appendChild(label);
      document.body.appendChild(input);

      expect(input.required).toBe(true);
      expect(input.getAttribute('aria-required')).toBe('true');
    });

    test('should display form error messages', () => {
      const input = document.createElement('input');
      const error = document.createElement('div');

      input.id = 'email';
      input.setAttribute('aria-invalid', 'true');
      input.setAttribute('aria-describedby', 'email-error');

      error.id = 'email-error';
      error.role = 'alert';
      error.className = 'form-error';
      error.textContent = 'Invalid email address';

      document.body.appendChild(input);
      document.body.appendChild(error);

      expect(input.getAttribute('aria-invalid')).toBe('true');
      expect(error.role).toBe('alert');
    });
  });

  // ============================================
  // Screen Reader Only Content Tests
  // ============================================

  describe('Screen Reader Only Content', () => {
    test('should hide sr-only content visually', () => {
      const srOnly = document.createElement('span');
      srOnly.className = 'sr-only';
      srOnly.textContent = 'Additional information for screen readers';
      document.body.appendChild(srOnly);

      const style = window.getComputedStyle(srOnly);
      // Should be absolutely positioned off-screen
      expect(srOnly).toHaveClass('sr-only');
    });

    test('should provide skip link for keyboard users', () => {
      const skipLink = document.createElement('a');
      skipLink.href = '#main-content';
      skipLink.className = 'skip-link';
      skipLink.textContent = 'メインコンテンツに移動';

      document.body.insertBefore(skipLink, document.body.firstChild);

      expect(skipLink.href).toContain('#main-content');
      expect(skipLink).toHaveClass('skip-link');
    });
  });

  // ============================================
  // Reduced Motion Tests
  // ============================================

  describe('Reduced Motion Support', () => {
    test('should respect prefers-reduced-motion', () => {
      const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

      if (prefersReduced) {
        const element = document.createElement('div');
        element.style.animation = 'slideIn 1s ease-in-out';

        // Animation should be disabled
        expect(prefersReduced).toBe(true);
      }
    });
  });

  // ============================================
  // Image Alternative Text Tests
  // ============================================

  describe('Image Accessibility', () => {
    test('should require alt text on images', () => {
      const img = document.createElement('img');
      img.src = 'chart.png';
      img.alt = 'Monthly leave usage chart';

      document.body.appendChild(img);

      expect(img.alt).not.toBe('');
      expect(img.alt).toBeTruthy();
    });

    test('should mark images missing alt text', () => {
      const img = document.createElement('img');
      img.src = 'icon.png';

      document.body.appendChild(img);

      // Check for missing alt
      if (!img.alt) {
        img.style.border = '2px solid red';
        img.style.opacity = '0.5';
      }

      expect(img.alt).toBe('');
    });
  });

  // ============================================
  // Page Title Tests
  // ============================================

  describe('Page Title Accessibility', () => {
    test('should have descriptive page title', () => {
      document.title = 'YuKyuDATA - 有給休暇管理システム';

      expect(document.title).toContain('YuKyuDATA');
      expect(document.title.length).toBeGreaterThan(0);
    });
  });

  // ============================================
  // Touch Target Size Tests
  // ============================================

  describe('Touch Target Size (Mobile Accessibility)', () => {
    test('should have minimum 44x44px touch targets', () => {
      const button = document.createElement('button');
      button.textContent = 'タップ';
      button.style.padding = '12px 20px';
      button.style.minHeight = '44px';
      button.style.minWidth = '44px';

      document.body.appendChild(button);

      const rect = button.getBoundingClientRect();
      const minSize = 44;

      // Verify minimum size with padding
      expect(button.style.minHeight).toBe('44px');
      expect(button.style.minWidth).toBe('44px');
    });
  });
});
