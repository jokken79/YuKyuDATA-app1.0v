/**
 * Button Stories - YuKyuDATA Design System
 *
 * Sistema de botones con efectos glassmorphism y estados interactivos.
 * Todos los botones cumplen con WCAG AA para accesibilidad.
 */

export default {
  title: 'Components/Button',
  tags: ['autodocs'],
  parameters: {
    docs: {
      description: {
        component: `
## Botones del Sistema YuKyuDATA

Sistema unificado de botones con soporte para:
- Efectos glassmorphism
- Estados de carga
- Variantes de color
- Accesibilidad WCAG AA

### Uso basico
\`\`\`html
<button class="btn btn-primary">Texto del boton</button>
\`\`\`
        `,
      },
    },
  },
  argTypes: {
    label: {
      control: 'text',
      description: 'Texto del boton',
    },
    disabled: {
      control: 'boolean',
      description: 'Estado deshabilitado',
    },
    loading: {
      control: 'boolean',
      description: 'Estado de carga',
    },
  },
};

// Primary Button
export const Primary = {
  args: {
    label: '承認する',
    disabled: false,
    loading: false,
  },
  render: ({ label, disabled, loading }) => {
    const disabledAttr = disabled ? 'disabled' : '';
    const loadingClass = loading ? 'is-loading' : '';
    return `
      <button
        class="btn btn-primary ${loadingClass}"
        ${disabledAttr}
        aria-label="${label}">
        ${label}
      </button>
    `;
  },
  parameters: {
    docs: {
      description: {
        story: 'Boton primario con gradiente cyan. Usado para acciones principales como aprobar solicitudes.',
      },
    },
  },
};

// Glass Button
export const Glass = {
  args: {
    label: 'キャンセル',
    disabled: false,
  },
  render: ({ label, disabled }) => {
    const disabledAttr = disabled ? 'disabled' : '';
    return `
      <button
        class="btn btn-glass"
        ${disabledAttr}
        aria-label="${label}">
        ${label}
      </button>
    `;
  },
  parameters: {
    docs: {
      description: {
        story: 'Boton con efecto glassmorphism. Ideal para acciones secundarias como cancelar.',
      },
    },
  },
};

// Export/Success Button
export const Export = {
  args: {
    label: 'エクスポート',
  },
  render: ({ label }) => `
    <button class="btn btn-export" aria-label="${label}">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
        <polyline points="7 10 12 15 17 10"></polyline>
        <line x1="12" y1="15" x2="12" y2="3"></line>
      </svg>
      ${label}
    </button>
  `,
  parameters: {
    docs: {
      description: {
        story: 'Boton verde para exportaciones y acciones de exito.',
      },
    },
  },
};

// Disabled State
export const Disabled = {
  render: () => `
    <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
      <button class="btn btn-primary" disabled>Primary Disabled</button>
      <button class="btn btn-glass" disabled>Glass Disabled</button>
      <button class="btn btn-export" disabled>Export Disabled</button>
    </div>
  `,
  parameters: {
    docs: {
      description: {
        story: 'Estados deshabilitados de todos los tipos de botones.',
      },
    },
  },
};

// Loading State
export const Loading = {
  render: () => `
    <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
      <button class="btn btn-primary is-loading">
        処理中...
      </button>
      <button class="btn btn-export is-loading">
        エクスポート中...
      </button>
    </div>
  `,
  parameters: {
    docs: {
      description: {
        story: 'Estado de carga con spinner animado.',
      },
    },
  },
};

// Button Group
export const ButtonGroup = {
  render: () => `
    <div style="display: flex; gap: 0.5rem;">
      <button class="btn btn-primary">承認</button>
      <button class="btn btn-glass">保留</button>
      <button class="btn" style="background: linear-gradient(135deg, #f87171, #ef4444); color: white;">却下</button>
    </div>
  `,
  parameters: {
    docs: {
      description: {
        story: 'Grupo de botones para acciones de workflow (Aprobar, Pendiente, Rechazar).',
      },
    },
  },
};

// All Variants
export const AllVariants = {
  render: () => `
    <div style="display: flex; flex-direction: column; gap: 2rem;">
      <div>
        <h3 style="color: var(--color-text-primary); margin-bottom: 1rem; font-size: 1rem;">Botones Principales</h3>
        <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
          <button class="btn btn-primary">Primary</button>
          <button class="btn btn-glass">Glass</button>
          <button class="btn btn-export">Export</button>
        </div>
      </div>

      <div>
        <h3 style="color: var(--color-text-primary); margin-bottom: 1rem; font-size: 1rem;">Con Iconos</h3>
        <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
          <button class="btn btn-primary">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 5v14M5 12h14"/>
            </svg>
            新規作成
          </button>
          <button class="btn btn-glass">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
            編集
          </button>
        </div>
      </div>

      <div>
        <h3 style="color: var(--color-text-primary); margin-bottom: 1rem; font-size: 1rem;">Estados</h3>
        <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
          <button class="btn btn-primary">Normal</button>
          <button class="btn btn-primary" disabled>Disabled</button>
          <button class="btn btn-primary is-loading">Loading</button>
        </div>
      </div>
    </div>
  `,
  parameters: {
    docs: {
      description: {
        story: 'Vista completa de todas las variantes de botones disponibles.',
      },
    },
  },
};
