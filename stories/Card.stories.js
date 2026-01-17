/**
 * Card Stories - YuKyuDATA Design System
 *
 * Paneles con efecto glassmorphism para contenido agrupado.
 * Incluye variantes para estadisticas, formularios y datos.
 */

export default {
  title: 'Components/Card',
  tags: ['autodocs'],
  parameters: {
    docs: {
      description: {
        component: `
## Cards y Paneles Glass

Sistema de tarjetas con efecto glassmorphism:
- Backdrop blur para efecto cristal
- Bordes sutiles con transparencia
- Sombras para profundidad
- Animaciones hover suaves

### Uso basico
\`\`\`html
<div class="glass-panel">
  Contenido de la tarjeta
</div>
\`\`\`
        `,
      },
    },
  },
};

// Glass Panel Basic
export const GlassPanel = {
  render: () => `
    <div class="glass-panel" style="max-width: 400px;">
      <h3 style="color: var(--color-text-primary); margin-bottom: 1rem;">Panel Glass</h3>
      <p style="color: var(--color-text-secondary);">
        Este panel utiliza efecto glassmorphism con backdrop-filter blur
        para crear una apariencia de vidrio esmerilado.
      </p>
    </div>
  `,
  parameters: {
    docs: {
      description: {
        story: 'Panel basico con efecto glassmorphism.',
      },
    },
  },
};

// Stat Card
export const StatCard = {
  render: () => `
    <div class="glass-panel" style="max-width: 200px; text-align: center;">
      <div style="font-size: 2.5rem; font-weight: 800; background: linear-gradient(135deg, #06b6d4, #22d3ee); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        15.5
      </div>
      <div style="color: var(--color-text-muted); font-size: 0.875rem; margin-top: 0.5rem;">
        残日数
      </div>
    </div>
  `,
  parameters: {
    docs: {
      description: {
        story: 'Tarjeta de estadistica con valor destacado.',
      },
    },
  },
};

// Stats Grid
export const StatsGrid = {
  render: () => `
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1.5rem;">
      <div class="glass-panel" style="text-align: center; padding: 1.5rem;">
        <div style="font-size: 2rem; font-weight: 800; color: #34d399;">15.5</div>
        <div style="color: var(--color-text-muted); font-size: 0.875rem; margin-top: 0.5rem;">残日数</div>
        <div style="color: var(--color-text-muted); font-size: 0.75rem;">Dias restantes</div>
      </div>

      <div class="glass-panel" style="text-align: center; padding: 1.5rem;">
        <div style="font-size: 2rem; font-weight: 800; color: #fbbf24;">4.5</div>
        <div style="color: var(--color-text-muted); font-size: 0.875rem; margin-top: 0.5rem;">使用日数</div>
        <div style="color: var(--color-text-muted); font-size: 0.75rem;">Dias usados</div>
      </div>

      <div class="glass-panel" style="text-align: center; padding: 1.5rem;">
        <div style="font-size: 2rem; font-weight: 800; color: #06b6d4;">20</div>
        <div style="color: var(--color-text-muted); font-size: 0.875rem; margin-top: 0.5rem;">付与日数</div>
        <div style="color: var(--color-text-muted); font-size: 0.75rem;">Dias otorgados</div>
      </div>

      <div class="glass-panel" style="text-align: center; padding: 1.5rem;">
        <div style="font-size: 2rem; font-weight: 800; color: #f87171;">2</div>
        <div style="color: var(--color-text-muted); font-size: 0.875rem; margin-top: 0.5rem;">期限切れ</div>
        <div style="color: var(--color-text-muted); font-size: 0.75rem;">Dias expirados</div>
      </div>
    </div>
  `,
  parameters: {
    docs: {
      description: {
        story: 'Grid de tarjetas de estadisticas con diferentes colores de estado.',
      },
    },
  },
};

// Info Card with Icon
export const InfoCard = {
  render: () => `
    <div class="glass-panel" style="max-width: 350px;">
      <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
        <div style="width: 48px; height: 48px; border-radius: 12px; background: linear-gradient(135deg, rgba(6, 182, 212, 0.2), rgba(8, 145, 178, 0.1)); display: flex; align-items: center; justify-content: center;">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#06b6d4" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="16" x2="12" y2="12"></line>
            <line x1="12" y1="8" x2="12.01" y2="8"></line>
          </svg>
        </div>
        <div>
          <h4 style="color: var(--color-text-primary); font-weight: 600;">5日取得義務</h4>
          <span style="color: var(--color-text-muted); font-size: 0.75rem;">5-day obligation</span>
        </div>
      </div>
      <p style="color: var(--color-text-secondary); font-size: 0.875rem; line-height: 1.6;">
        年間10日以上の有給休暇が付与される従業員は、
        最低5日の取得が義務付けられています。
      </p>
    </div>
  `,
  parameters: {
    docs: {
      description: {
        story: 'Tarjeta informativa con icono y descripcion.',
      },
    },
  },
};

// Employee Card
export const EmployeeCard = {
  render: () => `
    <div class="glass-panel" style="max-width: 400px;">
      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
        <div style="display: flex; align-items: center; gap: 1rem;">
          <div style="width: 56px; height: 56px; border-radius: 16px; background: linear-gradient(135deg, #06b6d4, #0891b2); display: flex; align-items: center; justify-content: center; color: white; font-weight: 700; font-size: 1.25rem;">
            TN
          </div>
          <div>
            <h4 style="color: var(--color-text-primary); font-weight: 600; font-size: 1.125rem;">田中 太郎</h4>
            <span style="color: var(--color-text-muted); font-size: 0.875rem;">社員番号: 001</span>
          </div>
        </div>
        <span class="badge badge-success">正社員</span>
      </div>

      <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; padding-top: 1rem; border-top: 1px solid rgba(255, 255, 255, 0.1);">
        <div style="text-align: center;">
          <div style="font-size: 1.5rem; font-weight: 700; color: #34d399;">15.5</div>
          <div style="font-size: 0.75rem; color: var(--color-text-muted);">残日数</div>
        </div>
        <div style="text-align: center;">
          <div style="font-size: 1.5rem; font-weight: 700; color: #fbbf24;">4.5</div>
          <div style="font-size: 0.75rem; color: var(--color-text-muted);">使用</div>
        </div>
        <div style="text-align: center;">
          <div style="font-size: 1.5rem; font-weight: 700; color: #06b6d4;">20</div>
          <div style="font-size: 0.75rem; color: var(--color-text-muted);">付与</div>
        </div>
      </div>
    </div>
  `,
  parameters: {
    docs: {
      description: {
        story: 'Tarjeta de empleado con avatar, informacion y estadisticas.',
      },
    },
  },
};

// Card with Form
export const CardWithForm = {
  render: () => `
    <div class="glass-panel" style="max-width: 450px;">
      <h3 style="color: var(--color-text-primary); margin-bottom: 1.5rem; font-size: 1.125rem; font-weight: 600;">
        有給休暇申請
      </h3>

      <div class="form-group">
        <label style="display: block; margin-bottom: 0.5rem; font-size: 0.875rem; color: var(--color-text-secondary);">
          申請日 <span style="color: #f87171;">*</span>
        </label>
        <input type="date" class="input-glass" style="width: 100%;" value="2025-01-17">
      </div>

      <div class="form-group" style="margin-top: 1rem;">
        <label style="display: block; margin-bottom: 0.5rem; font-size: 0.875rem; color: var(--color-text-secondary);">
          理由
        </label>
        <textarea class="input-glass" style="width: 100%; min-height: 80px; resize: vertical;" placeholder="申請理由を入力してください"></textarea>
      </div>

      <div style="display: flex; gap: 0.75rem; margin-top: 1.5rem;">
        <button class="btn btn-primary" style="flex: 1;">申請する</button>
        <button class="btn btn-glass">キャンセル</button>
      </div>
    </div>
  `,
  parameters: {
    docs: {
      description: {
        story: 'Tarjeta con formulario de solicitud de vacaciones.',
      },
    },
  },
};

// Skeleton Loading Card
export const SkeletonCard = {
  render: () => `
    <div class="glass-panel" style="max-width: 350px;">
      <div style="display: flex; gap: 1rem; margin-bottom: 1rem;">
        <div class="skeleton skeleton-avatar"></div>
        <div style="flex: 1;">
          <div class="skeleton skeleton-text lg"></div>
          <div class="skeleton skeleton-text sm" style="margin-top: 0.5rem;"></div>
        </div>
      </div>
      <div class="skeleton skeleton-text full"></div>
      <div class="skeleton skeleton-text lg"></div>
      <div class="skeleton skeleton-text md"></div>
    </div>
  `,
  parameters: {
    docs: {
      description: {
        story: 'Estado de carga skeleton para tarjetas.',
      },
    },
  },
};
