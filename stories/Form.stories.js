/**
 * Form Stories - YuKyuDATA Design System
 *
 * Componentes de formulario con estilo glass y validacion.
 * Todos los inputs cumplen con WCAG AA para accesibilidad.
 */

export default {
  title: 'Components/Form',
  tags: ['autodocs'],
  parameters: {
    docs: {
      description: {
        component: `
## Formularios del Sistema

Componentes de entrada con:
- Estilo glassmorphism
- Estados de validacion
- Mensajes de error accesibles
- Soporte para dark/light mode

### Uso basico
\`\`\`html
<div class="form-group">
  <label for="input-id">Label</label>
  <input type="text" id="input-id" class="input-glass">
</div>
\`\`\`
        `,
      },
    },
  },
};

// Text Input
export const TextInput = {
  render: () => `
    <div class="form-group" style="max-width: 300px;">
      <label for="employee-num" style="display: block; margin-bottom: 0.5rem; font-size: 0.875rem; color: var(--color-text-secondary);">
        社員番号 <span style="color: #f87171;">*</span>
      </label>
      <input
        type="text"
        id="employee-num"
        class="input-glass"
        placeholder="例: 001"
        aria-required="true"
        aria-describedby="employee-help">
      <span id="employee-help" style="display: block; margin-top: 0.5rem; font-size: 0.75rem; color: var(--color-text-muted);">
        3桁の社員番号を入力してください
      </span>
    </div>
  `,
  parameters: {
    docs: {
      description: {
        story: 'Input de texto basico con label, placeholder y texto de ayuda.',
      },
    },
  },
};

// Select Input
export const SelectInput = {
  render: () => `
    <div class="form-group" style="max-width: 300px;">
      <label for="year-select" style="display: block; margin-bottom: 0.5rem; font-size: 0.875rem; color: var(--color-text-secondary);">
        年度
      </label>
      <select id="year-select" class="input-glass">
        <option value="2025">2025年度</option>
        <option value="2024">2024年度</option>
        <option value="2023">2023年度</option>
      </select>
    </div>
  `,
  parameters: {
    docs: {
      description: {
        story: 'Selector con estilo glass y flecha personalizada.',
      },
    },
  },
};

// Date Input
export const DateInput = {
  render: () => `
    <div class="form-group" style="max-width: 300px;">
      <label for="date-input" style="display: block; margin-bottom: 0.5rem; font-size: 0.875rem; color: var(--color-text-secondary);">
        取得日
      </label>
      <input
        type="date"
        id="date-input"
        class="input-glass"
        value="2025-01-17">
    </div>
  `,
  parameters: {
    docs: {
      description: {
        story: 'Input de fecha con estilo glass.',
      },
    },
  },
};

// Textarea
export const Textarea = {
  render: () => `
    <div class="form-group" style="max-width: 400px;">
      <label for="reason" style="display: block; margin-bottom: 0.5rem; font-size: 0.875rem; color: var(--color-text-secondary);">
        申請理由
      </label>
      <textarea
        id="reason"
        class="input-glass"
        placeholder="休暇の理由を入力してください"
        style="min-height: 120px; resize: vertical;"></textarea>
    </div>
  `,
  parameters: {
    docs: {
      description: {
        story: 'Area de texto expandible con estilo glass.',
      },
    },
  },
};

// Validation States
export const ValidationStates = {
  render: () => `
    <div style="display: flex; flex-direction: column; gap: 2rem; max-width: 300px;">
      <div class="form-group">
        <label style="display: block; margin-bottom: 0.5rem; font-size: 0.875rem; color: var(--color-text-secondary);">
          Normal
        </label>
        <input type="text" class="input-glass" placeholder="Normal input">
      </div>

      <div class="form-group">
        <label style="display: block; margin-bottom: 0.5rem; font-size: 0.875rem; color: var(--color-text-secondary);">
          Valid
        </label>
        <input type="text" class="input-glass is-valid" value="001">
        <span style="display: block; margin-top: 0.5rem; font-size: 0.75rem; color: #34d399;">
          有効な社員番号です
        </span>
      </div>

      <div class="form-group">
        <label style="display: block; margin-bottom: 0.5rem; font-size: 0.875rem; color: var(--color-text-secondary);">
          Invalid
        </label>
        <input type="text" class="input-glass is-invalid" value="abc">
        <span role="alert" style="display: block; margin-top: 0.5rem; font-size: 0.75rem; color: #f87171;">
          社員番号は数字で入力してください
        </span>
      </div>
    </div>
  `,
  parameters: {
    docs: {
      description: {
        story: 'Estados de validacion: normal, valido e invalido con mensajes.',
      },
    },
  },
};

// Form Section
export const FormSection = {
  render: () => `
    <div class="form-section" style="max-width: 500px; background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 1.5rem;">
      <div class="form-section-title" style="font-size: 0.875rem; font-weight: 600; color: #06b6d4; margin-bottom: 1.25rem; display: flex; align-items: center; gap: 0.5rem;">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
          <circle cx="12" cy="7" r="4"></circle>
        </svg>
        社員情報
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
        <div class="form-group">
          <label style="display: block; margin-bottom: 0.5rem; font-size: 0.875rem; color: var(--color-text-secondary);">
            社員番号 <span style="color: #f87171;">*</span>
          </label>
          <input type="text" class="input-glass" placeholder="001">
        </div>

        <div class="form-group">
          <label style="display: block; margin-bottom: 0.5rem; font-size: 0.875rem; color: var(--color-text-secondary);">
            氏名 <span style="color: #f87171;">*</span>
          </label>
          <input type="text" class="input-glass" placeholder="田中 太郎">
        </div>
      </div>

      <div class="form-group" style="margin-top: 1rem;">
        <label style="display: block; margin-bottom: 0.5rem; font-size: 0.875rem; color: var(--color-text-secondary);">
          部署
        </label>
        <select class="input-glass">
          <option value="">選択してください</option>
          <option value="sales">営業部</option>
          <option value="dev">開発部</option>
          <option value="hr">人事部</option>
        </select>
      </div>
    </div>
  `,
  parameters: {
    docs: {
      description: {
        story: 'Seccion de formulario agrupada con titulo e icono.',
      },
    },
  },
};

// Complete Form
export const CompleteForm = {
  render: () => `
    <div class="glass-panel" style="max-width: 550px;">
      <h3 style="color: var(--color-text-primary); margin-bottom: 1.5rem; font-size: 1.25rem; font-weight: 700;">
        有給休暇申請
      </h3>

      <form>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
          <div class="form-group">
            <label style="display: block; margin-bottom: 0.5rem; font-size: 0.875rem; color: var(--color-text-secondary);">
              開始日 <span style="color: #f87171;">*</span>
            </label>
            <input type="date" class="input-glass" value="2025-01-20">
          </div>

          <div class="form-group">
            <label style="display: block; margin-bottom: 0.5rem; font-size: 0.875rem; color: var(--color-text-secondary);">
              終了日 <span style="color: #f87171;">*</span>
            </label>
            <input type="date" class="input-glass" value="2025-01-20">
          </div>
        </div>

        <div class="form-group" style="margin-bottom: 1rem;">
          <label style="display: block; margin-bottom: 0.5rem; font-size: 0.875rem; color: var(--color-text-secondary);">
            取得区分
          </label>
          <select class="input-glass">
            <option value="full">全日</option>
            <option value="am">午前半休</option>
            <option value="pm">午後半休</option>
          </select>
        </div>

        <div class="form-group" style="margin-bottom: 1.5rem;">
          <label style="display: block; margin-bottom: 0.5rem; font-size: 0.875rem; color: var(--color-text-secondary);">
            備考
          </label>
          <textarea
            class="input-glass"
            style="min-height: 80px; resize: vertical;"
            placeholder="必要に応じて備考を入力"></textarea>
        </div>

        <div style="display: flex; gap: 0.75rem; justify-content: flex-end; padding-top: 1rem; border-top: 1px solid rgba(255, 255, 255, 0.1);">
          <button type="button" class="btn btn-glass">キャンセル</button>
          <button type="submit" class="btn btn-primary">申請する</button>
        </div>
      </form>
    </div>
  `,
  parameters: {
    docs: {
      description: {
        story: 'Formulario completo de solicitud de vacaciones con todos los campos.',
      },
    },
  },
};

// Search Input
export const SearchInput = {
  render: () => `
    <div style="max-width: 400px; position: relative;">
      <input
        type="search"
        class="input-glass"
        placeholder="社員名または番号で検索..."
        style="padding-left: 2.75rem;"
        aria-label="検索">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="18"
        height="18"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        style="position: absolute; left: 1rem; top: 50%; transform: translateY(-50%); color: var(--color-text-muted);">
        <circle cx="11" cy="11" r="8"></circle>
        <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
      </svg>
    </div>
  `,
  parameters: {
    docs: {
      description: {
        story: 'Input de busqueda con icono integrado.',
      },
    },
  },
};
