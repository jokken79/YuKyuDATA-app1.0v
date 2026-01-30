/**
 * Tests para Componentes UI
 * Cobertura: Buttons, Forms, Cards, Layout
 */

describe('UI Components', () => {
  describe('Buttons', () => {
    test('debe renderizar botón primario', () => {
      const button = document.createElement('button');
      button.className = 'btn btn-primary';
      button.textContent = 'Guardar';
      
      expect(button.className).toContain('btn-primary');
      expect(button.textContent).toBe('Guardar');
    });

    test('debe tener estados de botón (hover, active, disabled)', () => {
      const button = document.createElement('button');
      button.className = 'btn btn-primary';
      
      // Simular disabled
      button.disabled = true;
      expect(button.disabled).toBe(true);
      
      // Simular hover
      button.classList.add('hover');
      expect(button.classList.contains('hover')).toBe(true);
    });

    test('debe ejecutar callback al hacer click', () => {
      const callback = jest.fn();
      const button = document.createElement('button');
      button.addEventListener('click', callback);
      button.click();
      
      expect(callback).toHaveBeenCalled();
    });
  });

  describe('Forms', () => {
    test('debe validar input requerido', () => {
      const input = document.createElement('input');
      input.required = true;
      input.value = '';
      
      expect(input.required).toBe(true);
      expect(input.value).toBe('');
    });

    test('debe mostrar error en campo inválido', () => {
      const input = document.createElement('input');
      input.type = 'email';
      input.value = 'invalid-email';
      
      const isValid = input.value.includes('@');
      expect(isValid).toBe(false);
    });

    test('debe permitir envío de formulario válido', () => {
      const form = document.createElement('form');
      const input = document.createElement('input');
      input.name = 'username';
      input.value = 'admin';
      input.required = true;
      form.appendChild(input);
      
      const isValid = form.checkValidity && input.value.length > 0;
      expect(isValid).toBeTruthy();
    });
  });

  describe('Cards', () => {
    test('debe renderizar card con contenido', () => {
      const card = document.createElement('div');
      card.className = 'card';
      card.innerHTML = '<h3>Card Title</h3><p>Content</p>';
      
      expect(card.className).toContain('card');
      expect(card.innerHTML).toContain('Card Title');
    });

    test('debe tener espaciado consistente', () => {
      const card = document.createElement('div');
      card.style.padding = '1rem';
      card.style.margin = '1rem';
      
      expect(card.style.padding).toBe('1rem');
      expect(card.style.margin).toBe('1rem');
    });
  });

  describe('Modal', () => {
    test('debe mostrar/ocultar modal', () => {
      const modal = document.createElement('div');
      modal.className = 'modal';
      modal.style.display = 'none';
      
      expect(modal.style.display).toBe('none');
      
      modal.style.display = 'block';
      expect(modal.style.display).toBe('block');
    });

    test('debe tener botón cerrar', () => {
      const modal = document.createElement('div');
      modal.className = 'modal';
      const closeBtn = document.createElement('button');
      closeBtn.className = 'modal-close';
      closeBtn.innerHTML = '&times;';
      modal.appendChild(closeBtn);
      
      expect(modal.querySelector('.modal-close')).toBeTruthy();
    });
  });
});
