/**
 * Tests for Form Component
 * YuKyuDATA Design System
 */

const { JSDOM } = require('jsdom');

// Setup DOM environment before imports
const dom = new JSDOM('<!DOCTYPE html><html><head></head><body><div id="form-container"></div></body></html>', {
  url: 'http://localhost'
});
global.document = dom.window.document;
global.window = dom.window;
global.HTMLElement = dom.window.HTMLElement;

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
const { Form } = require('../../../static/src/components/Form.js');

describe('Form Component', () => {
  let container;
  let testFields;

  beforeEach(() => {
    // Reset DOM
    document.body.innerHTML = '<div id="form-container"></div>';
    container = document.getElementById('form-container');

    // Reset test fields
    testFields = [
      { name: 'name', type: 'text', label: '名前', required: true },
      { name: 'email', type: 'email', label: 'メール', required: true },
      { name: 'age', type: 'number', label: '年齢', min: 0, max: 150 },
      { name: 'department', type: 'select', label: '部門', options: [
        { value: 'sales', label: '営業' },
        { value: 'dev', label: '開発' },
        { value: 'hr', label: '人事' }
      ]},
      { name: 'notes', type: 'textarea', label: '備考' },
      { name: 'active', type: 'checkbox', label: 'アクティブ' }
    ];
  });

  describe('Constructor', () => {
    test('creates form with default options', () => {
      const form = new Form(container, { fields: testFields });

      expect(form.validateOnChange).toBe(true);
      expect(form.validateOnBlur).toBe(true);
      expect(form.showErrors).toBe(true);
      expect(form.layout).toBe('vertical');
    });

    test('creates form with custom options', () => {
      const form = new Form(container, {
        fields: testFields,
        validateOnChange: false,
        layout: 'horizontal',
        submitLabel: '保存',
        showCancel: true
      });

      expect(form.validateOnChange).toBe(false);
      expect(form.layout).toBe('horizontal');
      expect(form.submitLabel).toBe('保存');
      expect(form.showCancel).toBe(true);
    });

    test('accepts string selector for container', () => {
      const form = new Form('#form-container', { fields: testFields });
      expect(form.container).toBe(container);
    });

    test('throws error when container not found', () => {
      expect(() => {
        new Form('#nonexistent', { fields: testFields });
      }).toThrow('Form: Container element not found');
    });

    test('renders form immediately', () => {
      new Form(container, { fields: testFields });
      expect(container.querySelector('form')).toBeTruthy();
    });

    test('sets initial values', () => {
      const form = new Form(container, {
        fields: testFields,
        values: { name: 'Test User', age: 25 }
      });

      expect(form.getValue('name')).toBe('Test User');
      expect(form.getValue('age')).toBe(25);
    });
  });

  describe('Field Rendering', () => {
    test('renders text input', () => {
      new Form(container, {
        fields: [{ name: 'text', type: 'text', label: 'Text' }]
      });

      const input = container.querySelector('input[type="text"]');
      expect(input).toBeTruthy();
      expect(input.name).toBe('text');
    });

    test('renders email input', () => {
      new Form(container, {
        fields: [{ name: 'email', type: 'email', label: 'Email' }]
      });

      const input = container.querySelector('input[type="email"]');
      expect(input).toBeTruthy();
    });

    test('renders number input', () => {
      new Form(container, {
        fields: [{ name: 'num', type: 'number', label: 'Number', min: 0, max: 100, step: 5 }]
      });

      const input = container.querySelector('input[type="number"]');
      expect(input).toBeTruthy();
      expect(input.getAttribute('min')).toBe('0');
      expect(input.getAttribute('max')).toBe('100');
      expect(input.getAttribute('step')).toBe('5');
    });

    test('renders date input', () => {
      new Form(container, {
        fields: [{ name: 'date', type: 'date', label: 'Date' }]
      });

      const input = container.querySelector('input[type="date"]');
      expect(input).toBeTruthy();
    });

    test('renders select with options', () => {
      new Form(container, {
        fields: [{
          name: 'select',
          type: 'select',
          label: 'Select',
          options: [
            { value: 'a', label: 'Option A' },
            { value: 'b', label: 'Option B' }
          ]
        }]
      });

      const select = container.querySelector('select');
      expect(select).toBeTruthy();
      expect(select.options.length).toBe(2);
    });

    test('renders select with placeholder option', () => {
      new Form(container, {
        fields: [{
          name: 'select',
          type: 'select',
          label: 'Select',
          placeholder: '選択してください',
          options: [{ value: 'a', label: 'A' }]
        }]
      });

      const select = container.querySelector('select');
      expect(select.options[0].textContent).toBe('選択してください');
      expect(select.options[0].value).toBe('');
    });

    test('renders textarea', () => {
      new Form(container, {
        fields: [{ name: 'notes', type: 'textarea', label: 'Notes', rows: 6 }]
      });

      const textarea = container.querySelector('textarea');
      expect(textarea).toBeTruthy();
      expect(textarea.getAttribute('rows')).toBe('6');
    });

    test('renders checkbox', () => {
      new Form(container, {
        fields: [{ name: 'agree', type: 'checkbox', label: 'I agree' }]
      });

      const checkbox = container.querySelector('input[type="checkbox"]');
      expect(checkbox).toBeTruthy();
    });

    test('renders radio group', () => {
      new Form(container, {
        fields: [{
          name: 'gender',
          type: 'radio',
          label: 'Gender',
          options: [
            { value: 'male', label: 'Male' },
            { value: 'female', label: 'Female' }
          ]
        }]
      });

      const radios = container.querySelectorAll('input[type="radio"]');
      expect(radios.length).toBe(2);
      expect(radios[0].name).toBe('gender');
    });

    test('renders labels for all fields', () => {
      new Form(container, { fields: testFields });

      const labels = container.querySelectorAll('.form-label');
      expect(labels.length).toBeGreaterThan(0);
    });

    test('renders required indicator', () => {
      new Form(container, {
        fields: [{ name: 'required', type: 'text', label: 'Required', required: true }]
      });

      const indicator = container.querySelector('.required-indicator');
      expect(indicator).toBeTruthy();
      expect(indicator.textContent).toBe('*');
    });

    test('renders help text', () => {
      new Form(container, {
        fields: [{ name: 'field', type: 'text', label: 'Field', help: 'Help text here' }]
      });

      const help = container.querySelector('.form-help');
      expect(help).toBeTruthy();
      expect(help.textContent).toBe('Help text here');
    });

    test('sets disabled attribute', () => {
      new Form(container, {
        fields: [{ name: 'disabled', type: 'text', label: 'Disabled', disabled: true }]
      });

      const input = container.querySelector('input');
      expect(input.disabled).toBe(true);
    });

    test('sets readonly attribute', () => {
      new Form(container, {
        fields: [{ name: 'readonly', type: 'text', label: 'Readonly', readonly: true }]
      });

      const input = container.querySelector('input');
      expect(input.readOnly).toBe(true);
    });

    test('sets placeholder attribute', () => {
      new Form(container, {
        fields: [{ name: 'field', type: 'text', label: 'Field', placeholder: 'Enter value' }]
      });

      const input = container.querySelector('input');
      expect(input.placeholder).toBe('Enter value');
    });

    test('sets autocomplete attribute', () => {
      new Form(container, {
        fields: [{ name: 'email', type: 'email', label: 'Email', autocomplete: 'email' }]
      });

      const input = container.querySelector('input');
      expect(input.autocomplete).toBe('email');
    });
  });

  describe('ARIA Accessibility', () => {
    test('input has aria-required for required fields', () => {
      new Form(container, {
        fields: [{ name: 'required', type: 'text', label: 'Required', required: true }]
      });

      const input = container.querySelector('input');
      expect(input.getAttribute('aria-required')).toBe('true');
    });

    test('input has aria-describedby for help text', () => {
      new Form(container, {
        fields: [{ name: 'field', type: 'text', label: 'Field', help: 'Help text' }]
      });

      const input = container.querySelector('input');
      expect(input.getAttribute('aria-describedby')).toContain('-help');
    });

    test('input has aria-invalid when validation fails', () => {
      const form = new Form(container, {
        fields: [{ name: 'required', type: 'text', label: 'Required', required: true }]
      });

      form.touched['required'] = true;
      form.validate();

      const input = container.querySelector('input');
      expect(input.getAttribute('aria-invalid')).toBe('true');
    });

    test('error message has role="alert"', () => {
      const form = new Form(container, {
        fields: [{ name: 'required', type: 'text', label: 'Required', required: true }]
      });

      form.touched['required'] = true;
      form.validate();

      const error = container.querySelector('.form-error');
      expect(error.getAttribute('role')).toBe('alert');
    });

    test('radio group has role="radiogroup"', () => {
      new Form(container, {
        fields: [{
          name: 'options',
          type: 'radio',
          label: 'Options',
          options: [{ value: 'a', label: 'A' }]
        }]
      });

      const radioGroup = container.querySelector('.form-radio-group');
      expect(radioGroup.getAttribute('role')).toBe('radiogroup');
    });

    test('radio group has aria-label', () => {
      new Form(container, {
        fields: [{
          name: 'options',
          type: 'radio',
          label: 'Options Label',
          options: [{ value: 'a', label: 'A' }]
        }]
      });

      const radioGroup = container.querySelector('.form-radio-group');
      expect(radioGroup.getAttribute('aria-label')).toBe('Options Label');
    });
  });

  describe('Layout', () => {
    test('applies vertical layout by default', () => {
      new Form(container, { fields: testFields });

      const form = container.querySelector('form');
      expect(form.classList.contains('inline')).toBe(false);
    });

    test('applies inline layout', () => {
      new Form(container, {
        fields: testFields,
        layout: 'inline'
      });

      const form = container.querySelector('form');
      expect(form.classList.contains('inline')).toBe(true);
    });

    test('applies horizontal layout', () => {
      new Form(container, {
        fields: testFields,
        layout: 'horizontal'
      });

      const groups = container.querySelectorAll('.form-group-horizontal');
      expect(groups.length).toBeGreaterThan(0);
    });
  });

  describe('Buttons', () => {
    test('renders submit button', () => {
      new Form(container, { fields: testFields });

      const submitBtn = container.querySelector('button[type="submit"]');
      expect(submitBtn).toBeTruthy();
    });

    test('renders custom submit label', () => {
      new Form(container, {
        fields: testFields,
        submitLabel: '保存する'
      });

      const submitBtn = container.querySelector('button[type="submit"]');
      expect(submitBtn.textContent).toContain('保存する');
    });

    test('renders cancel button when showCancel is true', () => {
      new Form(container, {
        fields: testFields,
        showCancel: true,
        cancelLabel: 'キャンセル'
      });

      const cancelBtn = container.querySelector('.form-cancel-btn');
      expect(cancelBtn).toBeTruthy();
      expect(cancelBtn.textContent).toContain('キャンセル');
    });

    test('calls onCancel when cancel button clicked', () => {
      const onCancel = jest.fn();
      new Form(container, {
        fields: testFields,
        showCancel: true,
        onCancel
      });

      const cancelBtn = container.querySelector('.form-cancel-btn');
      cancelBtn.click();

      expect(onCancel).toHaveBeenCalled();
    });
  });

  describe('Validation', () => {
    test('validates required field', () => {
      const form = new Form(container, {
        fields: [{ name: 'required', type: 'text', label: 'Required', required: true }]
      });

      form.touched['required'] = true;
      const isValid = form.validate();

      expect(isValid).toBe(false);
      expect(form.errors['required']).toBeTruthy();
    });

    test('validates required checkbox', () => {
      const form = new Form(container, {
        fields: [{ name: 'agree', type: 'checkbox', label: 'Agree', required: true }],
        values: { agree: false }
      });

      form.touched['agree'] = true;
      const isValid = form.validate();

      expect(isValid).toBe(false);
    });

    test('validates email format', () => {
      const form = new Form(container, {
        fields: [{ name: 'email', type: 'email', label: 'Email' }],
        values: { email: 'invalid-email' }
      });

      form.touched['email'] = true;
      const isValid = form.validate();

      expect(isValid).toBe(false);
      expect(form.errors['email']).toContain('メールアドレス');
    });

    test('validates min value for number', () => {
      const form = new Form(container, {
        fields: [{ name: 'age', type: 'number', label: 'Age', min: 18 }],
        values: { age: 10 }
      });

      form.touched['age'] = true;
      const isValid = form.validate();

      expect(isValid).toBe(false);
      expect(form.errors['age']).toContain('18');
    });

    test('validates max value for number', () => {
      const form = new Form(container, {
        fields: [{ name: 'age', type: 'number', label: 'Age', max: 100 }],
        values: { age: 150 }
      });

      form.touched['age'] = true;
      const isValid = form.validate();

      expect(isValid).toBe(false);
      expect(form.errors['age']).toContain('100');
    });

    test('validates minLength for string', () => {
      const form = new Form(container, {
        fields: [{ name: 'password', type: 'text', label: 'Password', minLength: 8 }],
        values: { password: 'short' }
      });

      form.touched['password'] = true;
      const isValid = form.validate();

      expect(isValid).toBe(false);
      expect(form.errors['password']).toContain('8');
    });

    test('validates maxLength for string', () => {
      const form = new Form(container, {
        fields: [{ name: 'name', type: 'text', label: 'Name', maxLength: 10 }],
        values: { name: 'Very Long Name Here' }
      });

      form.touched['name'] = true;
      const isValid = form.validate();

      expect(isValid).toBe(false);
      expect(form.errors['name']).toContain('10');
    });

    test('validates pattern', () => {
      const form = new Form(container, {
        fields: [{
          name: 'code',
          type: 'text',
          label: 'Code',
          pattern: '^[A-Z]{3}$'
        }],
        values: { code: 'abc' }
      });

      form.touched['code'] = true;
      const isValid = form.validate();

      expect(isValid).toBe(false);
    });

    test('custom validation function', () => {
      const form = new Form(container, {
        fields: [{
          name: 'custom',
          type: 'text',
          label: 'Custom',
          validation: {
            custom: (value) => value === 'valid' ? null : 'Must be "valid"'
          }
        }],
        values: { custom: 'invalid' }
      });

      form.touched['custom'] = true;
      const isValid = form.validate();

      expect(isValid).toBe(false);
      expect(form.errors['custom']).toBe('Must be "valid"');
    });

    test('passes when all validations pass', () => {
      const form = new Form(container, {
        fields: [
          { name: 'name', type: 'text', label: 'Name', required: true },
          { name: 'email', type: 'email', label: 'Email', required: true }
        ],
        values: { name: 'Test User', email: 'test@example.com' }
      });

      form.touched['name'] = true;
      form.touched['email'] = true;
      const isValid = form.validate();

      expect(isValid).toBe(true);
      expect(Object.keys(form.errors).length).toBe(0);
    });
  });

  describe('Value Management', () => {
    test('getValues returns all values', () => {
      const form = new Form(container, {
        fields: testFields,
        values: { name: 'Test', age: 25 }
      });

      const values = form.getValues();
      expect(values.name).toBe('Test');
      expect(values.age).toBe(25);
    });

    test('getValue returns single value', () => {
      const form = new Form(container, {
        fields: testFields,
        values: { name: 'Test' }
      });

      expect(form.getValue('name')).toBe('Test');
    });

    test('setValues updates multiple values', () => {
      const form = new Form(container, { fields: testFields });

      form.setValues({ name: 'New Name', age: 30 });

      expect(form.getValue('name')).toBe('New Name');
      expect(form.getValue('age')).toBe(30);
    });

    test('setValue updates single value', () => {
      const form = new Form(container, { fields: testFields });

      form.setValue('name', 'Single Update');

      expect(form.getValue('name')).toBe('Single Update');
    });

    test('setValues updates DOM elements', () => {
      const form = new Form(container, {
        fields: [{ name: 'text', type: 'text', label: 'Text' }]
      });

      form.setValues({ text: 'Updated' });

      const input = container.querySelector('input');
      expect(input.value).toBe('Updated');
    });

    test('setValues updates checkbox state', () => {
      const form = new Form(container, {
        fields: [{ name: 'check', type: 'checkbox', label: 'Check' }]
      });

      form.setValues({ check: true });

      const checkbox = container.querySelector('input[type="checkbox"]');
      expect(checkbox.checked).toBe(true);
    });

    test('setValues updates select value', () => {
      const form = new Form(container, {
        fields: [{
          name: 'select',
          type: 'select',
          label: 'Select',
          options: [{ value: 'a', label: 'A' }, { value: 'b', label: 'B' }]
        }]
      });

      form.setValues({ select: 'b' });

      const select = container.querySelector('select');
      expect(select.value).toBe('b');
    });
  });

  describe('Error Management', () => {
    test('getErrors returns all errors', () => {
      const form = new Form(container, {
        fields: [
          { name: 'field1', type: 'text', label: 'Field 1', required: true },
          { name: 'field2', type: 'text', label: 'Field 2', required: true }
        ]
      });

      form.touched['field1'] = true;
      form.touched['field2'] = true;
      form.validate();

      const errors = form.getErrors();
      expect(Object.keys(errors).length).toBe(2);
    });

    test('setError manually sets field error', () => {
      const form = new Form(container, {
        fields: [{ name: 'field', type: 'text', label: 'Field' }]
      });

      form.setError('field', 'Custom error message');

      expect(form.errors['field']).toBe('Custom error message');
    });

    test('clearErrors removes all errors', () => {
      const form = new Form(container, {
        fields: [{ name: 'field', type: 'text', label: 'Field', required: true }]
      });

      form.touched['field'] = true;
      form.validate();
      form.clearErrors();

      expect(Object.keys(form.errors).length).toBe(0);
    });
  });

  describe('Form Submission', () => {
    test('calls onSubmit when valid', async () => {
      const onSubmit = jest.fn();
      const form = new Form(container, {
        fields: [{ name: 'name', type: 'text', label: 'Name', required: true }],
        values: { name: 'Valid' },
        onSubmit
      });

      const formEl = container.querySelector('form');
      formEl.dispatchEvent(new dom.window.Event('submit'));

      // Wait for async submit
      await new Promise(resolve => setTimeout(resolve, 0));

      expect(onSubmit).toHaveBeenCalledWith({ name: 'Valid' }, form);
    });

    test('does not call onSubmit when invalid', async () => {
      const onSubmit = jest.fn();
      new Form(container, {
        fields: [{ name: 'name', type: 'text', label: 'Name', required: true }],
        onSubmit
      });

      const formEl = container.querySelector('form');
      formEl.dispatchEvent(new dom.window.Event('submit'));

      // Wait for async submit
      await new Promise(resolve => setTimeout(resolve, 0));

      expect(onSubmit).not.toHaveBeenCalled();
    });

    test('marks all fields as touched on submit', () => {
      const form = new Form(container, {
        fields: testFields
      });

      const formEl = container.querySelector('form');
      formEl.dispatchEvent(new dom.window.Event('submit'));

      testFields.forEach(field => {
        expect(form.touched[field.name]).toBe(true);
      });
    });

    test('disables submit button during submission', async () => {
      const onSubmit = jest.fn(() => new Promise(r => setTimeout(r, 100)));
      const form = new Form(container, {
        fields: [{ name: 'name', type: 'text', label: 'Name' }],
        values: { name: 'Test' },
        onSubmit
      });

      const formEl = container.querySelector('form');
      formEl.dispatchEvent(new dom.window.Event('submit'));

      expect(form.isSubmitting).toBe(true);
      const submitBtn = container.querySelector('.form-submit-btn');
      expect(submitBtn.disabled).toBe(true);
    });
  });

  describe('onChange Callback', () => {
    test('calls onChange when field value changes', () => {
      const onChange = jest.fn();
      new Form(container, {
        fields: [{ name: 'text', type: 'text', label: 'Text' }],
        onChange
      });

      const input = container.querySelector('input');
      input.value = 'new value';
      input.dispatchEvent(new dom.window.Event('input'));

      expect(onChange).toHaveBeenCalledWith('text', 'new value', expect.any(Object));
    });

    test('calls onChange for checkbox change', () => {
      const onChange = jest.fn();
      new Form(container, {
        fields: [{ name: 'check', type: 'checkbox', label: 'Check' }],
        onChange
      });

      const checkbox = container.querySelector('input[type="checkbox"]');
      checkbox.checked = true;
      checkbox.dispatchEvent(new dom.window.Event('change'));

      expect(onChange).toHaveBeenCalledWith('check', true, expect.any(Object));
    });
  });

  describe('reset()', () => {
    test('resets form to initial state', () => {
      const form = new Form(container, {
        fields: [
          { name: 'name', type: 'text', label: 'Name', value: 'Default' }
        ],
        values: { name: 'Modified' }
      });

      form.reset();

      expect(form.getValue('name')).toBe('Default');
    });

    test('clears errors on reset', () => {
      const form = new Form(container, {
        fields: [{ name: 'field', type: 'text', label: 'Field', required: true }]
      });

      form.touched['field'] = true;
      form.validate();
      form.reset();

      expect(Object.keys(form.errors).length).toBe(0);
    });

    test('clears touched state on reset', () => {
      const form = new Form(container, {
        fields: [{ name: 'field', type: 'text', label: 'Field' }]
      });

      form.touched['field'] = true;
      form.reset();

      expect(form.touched['field']).toBeFalsy();
    });
  });

  describe('setEnabled()', () => {
    test('disables all fields', () => {
      const form = new Form(container, { fields: testFields });

      form.setEnabled(false);

      const inputs = container.querySelectorAll('input, select, textarea');
      inputs.forEach(input => {
        expect(input.disabled).toBe(true);
      });
    });

    test('enables all fields', () => {
      const form = new Form(container, { fields: testFields });

      form.setEnabled(false);
      form.setEnabled(true);

      const inputs = container.querySelectorAll('input, select, textarea');
      inputs.forEach(input => {
        expect(input.disabled).toBe(false);
      });
    });
  });

  describe('focus()', () => {
    test('focuses specified field', () => {
      const form = new Form(container, {
        fields: [{ name: 'text', type: 'text', label: 'Text' }]
      });

      form.focus('text');

      const input = container.querySelector('input');
      expect(document.activeElement).toBe(input);
    });
  });

  describe('destroy()', () => {
    test('clears container content', () => {
      const form = new Form(container, { fields: testFields });

      form.destroy();

      expect(container.innerHTML).toBe('');
      expect(form.formElement).toBe(null);
    });
  });
});
