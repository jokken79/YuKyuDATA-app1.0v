/**
 * Table Stories - YuKyuDATA Design System
 *
 * Tablas de datos con estilo glass, ordenamiento y responsive.
 * Optimizadas para mostrar datos de empleados y vacaciones.
 */

export default {
  title: 'Components/Table',
  tags: ['autodocs'],
  parameters: {
    docs: {
      description: {
        component: `
## Tablas de Datos

Sistema de tablas con:
- Estilo glassmorphism
- Filas hover animadas
- Badges de estado
- Responsive con scroll horizontal
- Acciones por fila

### Uso basico
\`\`\`html
<table class="modern-table">
  <thead>
    <tr><th>Header</th></tr>
  </thead>
  <tbody>
    <tr><td>Cell</td></tr>
  </tbody>
</table>
\`\`\`
        `,
      },
    },
  },
};

// Basic Table
export const BasicTable = {
  render: () => `
    <div class="glass-panel" style="overflow-x: auto;">
      <table style="width: 100%; border-collapse: collapse;">
        <thead>
          <tr>
            <th style="text-align: left; padding: 1rem; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--color-text-muted); border-bottom: 1px solid rgba(255, 255, 255, 0.1);">社員番号</th>
            <th style="text-align: left; padding: 1rem; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--color-text-muted); border-bottom: 1px solid rgba(255, 255, 255, 0.1);">氏名</th>
            <th style="text-align: right; padding: 1rem; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--color-text-muted); border-bottom: 1px solid rgba(255, 255, 255, 0.1);">残日数</th>
            <th style="text-align: center; padding: 1rem; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--color-text-muted); border-bottom: 1px solid rgba(255, 255, 255, 0.1);">状態</th>
          </tr>
        </thead>
        <tbody>
          <tr style="transition: background 0.2s;">
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); color: var(--color-text-primary); font-family: var(--font-mono);">001</td>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); color: var(--color-text-primary);">田中 太郎</td>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); color: var(--color-text-primary); text-align: right; font-weight: 600;">15.5</td>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); text-align: center;">
              <span class="badge badge-success">正常</span>
            </td>
          </tr>
          <tr style="transition: background 0.2s;">
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); color: var(--color-text-primary); font-family: var(--font-mono);">002</td>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); color: var(--color-text-primary);">佐藤 花子</td>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); color: var(--color-text-primary); text-align: right; font-weight: 600;">8.0</td>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); text-align: center;">
              <span class="badge badge-warning">注意</span>
            </td>
          </tr>
          <tr style="transition: background 0.2s;">
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); color: var(--color-text-primary); font-family: var(--font-mono);">003</td>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); color: var(--color-text-primary);">鈴木 一郎</td>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); color: var(--color-text-primary); text-align: right; font-weight: 600;">3.0</td>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); text-align: center;">
              <span class="badge badge-danger">要対応</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  `,
  parameters: {
    docs: {
      description: {
        story: 'Tabla basica con encabezados, datos y badges de estado.',
      },
    },
  },
};

// Table with Actions
export const TableWithActions = {
  render: () => `
    <div class="glass-panel" style="overflow-x: auto;">
      <table style="width: 100%; border-collapse: collapse;">
        <thead>
          <tr>
            <th style="text-align: left; padding: 1rem; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--color-text-muted); border-bottom: 1px solid rgba(255, 255, 255, 0.1);">社員番号</th>
            <th style="text-align: left; padding: 1rem; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--color-text-muted); border-bottom: 1px solid rgba(255, 255, 255, 0.1);">氏名</th>
            <th style="text-align: right; padding: 1rem; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--color-text-muted); border-bottom: 1px solid rgba(255, 255, 255, 0.1);">付与</th>
            <th style="text-align: right; padding: 1rem; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--color-text-muted); border-bottom: 1px solid rgba(255, 255, 255, 0.1);">使用</th>
            <th style="text-align: right; padding: 1rem; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--color-text-muted); border-bottom: 1px solid rgba(255, 255, 255, 0.1);">残</th>
            <th style="text-align: center; padding: 1rem; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--color-text-muted); border-bottom: 1px solid rgba(255, 255, 255, 0.1);">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr style="transition: background 0.2s;">
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); color: var(--color-text-primary); font-family: var(--font-mono);">001</td>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05);">
              <div style="display: flex; align-items: center; gap: 0.5rem;">
                <span style="color: var(--color-text-primary);">田中 太郎</span>
                <span class="badge-type type-genzai">派遣</span>
              </div>
            </td>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); color: var(--color-text-secondary); text-align: right;">20</td>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); color: var(--color-text-secondary); text-align: right;">4.5</td>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); color: #34d399; text-align: right; font-weight: 600;">15.5</td>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); text-align: center;">
              <div style="display: flex; gap: 0.5rem; justify-content: center;">
                <button class="btn btn-glass" style="padding: 0.5rem 0.75rem; font-size: 0.75rem;">編集</button>
                <button class="btn btn-glass" style="padding: 0.5rem 0.75rem; font-size: 0.75rem;">詳細</button>
              </div>
            </td>
          </tr>
          <tr style="transition: background 0.2s;">
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); color: var(--color-text-primary); font-family: var(--font-mono);">002</td>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05);">
              <div style="display: flex; align-items: center; gap: 0.5rem;">
                <span style="color: var(--color-text-primary);">佐藤 花子</span>
                <span class="badge-type type-ukeoi">請負</span>
              </div>
            </td>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); color: var(--color-text-secondary); text-align: right;">18</td>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); color: var(--color-text-secondary); text-align: right;">10.0</td>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); color: #fbbf24; text-align: right; font-weight: 600;">8.0</td>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); text-align: center;">
              <div style="display: flex; gap: 0.5rem; justify-content: center;">
                <button class="btn btn-glass" style="padding: 0.5rem 0.75rem; font-size: 0.75rem;">編集</button>
                <button class="btn btn-glass" style="padding: 0.5rem 0.75rem; font-size: 0.75rem;">詳細</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  `,
  parameters: {
    docs: {
      description: {
        story: 'Tabla con botones de accion y badges de tipo de empleado.',
      },
    },
  },
};

// Leave Requests Table
export const LeaveRequestsTable = {
  render: () => `
    <div class="glass-panel" style="overflow-x: auto;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
        <h3 style="color: var(--color-text-primary); font-size: 1rem; font-weight: 600;">有給休暇申請一覧</h3>
        <div style="display: flex; gap: 0.5rem;">
          <span class="badge badge-warning" style="font-size: 0.75rem;">3件 承認待ち</span>
        </div>
      </div>

      <table style="width: 100%; border-collapse: collapse;">
        <thead>
          <tr>
            <th style="text-align: left; padding: 0.75rem 1rem; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; color: var(--color-text-muted); border-bottom: 1px solid rgba(255, 255, 255, 0.1);">申請日</th>
            <th style="text-align: left; padding: 0.75rem 1rem; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; color: var(--color-text-muted); border-bottom: 1px solid rgba(255, 255, 255, 0.1);">社員名</th>
            <th style="text-align: left; padding: 0.75rem 1rem; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; color: var(--color-text-muted); border-bottom: 1px solid rgba(255, 255, 255, 0.1);">取得日</th>
            <th style="text-align: right; padding: 0.75rem 1rem; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; color: var(--color-text-muted); border-bottom: 1px solid rgba(255, 255, 255, 0.1);">日数</th>
            <th style="text-align: center; padding: 0.75rem 1rem; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; color: var(--color-text-muted); border-bottom: 1px solid rgba(255, 255, 255, 0.1);">状態</th>
            <th style="text-align: center; padding: 0.75rem 1rem; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; color: var(--color-text-muted); border-bottom: 1px solid rgba(255, 255, 255, 0.1);">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); color: var(--color-text-muted); font-size: 0.875rem;">2025/01/15</td>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); color: var(--color-text-primary);">田中 太郎</td>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); color: var(--color-text-primary);">2025/01/20</td>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); color: var(--color-text-primary); text-align: right;">1.0</td>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); text-align: center;">
              <span class="badge badge-warning">承認待ち</span>
            </td>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); text-align: center;">
              <div style="display: flex; gap: 0.5rem; justify-content: center;">
                <button class="btn btn-primary" style="padding: 0.4rem 0.75rem; font-size: 0.75rem;">承認</button>
                <button class="btn" style="padding: 0.4rem 0.75rem; font-size: 0.75rem; background: linear-gradient(135deg, #f87171, #ef4444); color: white;">却下</button>
              </div>
            </td>
          </tr>
          <tr>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); color: var(--color-text-muted); font-size: 0.875rem;">2025/01/14</td>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); color: var(--color-text-primary);">佐藤 花子</td>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); color: var(--color-text-primary);">2025/01/22 〜 23</td>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); color: var(--color-text-primary); text-align: right;">2.0</td>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); text-align: center;">
              <span class="badge badge-success">承認済み</span>
            </td>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); text-align: center;">
              <button class="btn btn-glass" style="padding: 0.4rem 0.75rem; font-size: 0.75rem;">取消</button>
            </td>
          </tr>
          <tr>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); color: var(--color-text-muted); font-size: 0.875rem;">2025/01/10</td>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); color: var(--color-text-primary);">鈴木 一郎</td>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); color: var(--color-text-primary);">2025/01/18</td>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); color: var(--color-text-primary); text-align: right;">0.5</td>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); text-align: center;">
              <span class="badge badge-danger">却下</span>
            </td>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); text-align: center;">
              <button class="btn btn-glass" style="padding: 0.4rem 0.75rem; font-size: 0.75rem;">詳細</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  `,
  parameters: {
    docs: {
      description: {
        story: 'Tabla de solicitudes de vacaciones con workflow de aprobacion.',
      },
    },
  },
};

// Skeleton Table Loading
export const SkeletonTable = {
  render: () => `
    <div class="glass-panel" style="overflow-x: auto;">
      <table style="width: 100%; border-collapse: collapse;">
        <thead>
          <tr>
            <th style="text-align: left; padding: 1rem; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; color: var(--color-text-muted); border-bottom: 1px solid rgba(255, 255, 255, 0.1);">社員番号</th>
            <th style="text-align: left; padding: 1rem; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; color: var(--color-text-muted); border-bottom: 1px solid rgba(255, 255, 255, 0.1);">氏名</th>
            <th style="text-align: right; padding: 1rem; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; color: var(--color-text-muted); border-bottom: 1px solid rgba(255, 255, 255, 0.1);">残日数</th>
            <th style="text-align: center; padding: 1rem; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; color: var(--color-text-muted); border-bottom: 1px solid rgba(255, 255, 255, 0.1);">状態</th>
          </tr>
        </thead>
        <tbody>
          ${[1, 2, 3, 4, 5].map(() => `
            <tr>
              <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05);">
                <div class="skeleton skeleton-text" style="width: 60px;"></div>
              </td>
              <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05);">
                <div class="skeleton skeleton-text" style="width: 120px;"></div>
              </td>
              <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); text-align: right;">
                <div class="skeleton skeleton-text" style="width: 40px; margin-left: auto;"></div>
              </td>
              <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); text-align: center;">
                <div class="skeleton skeleton-badge" style="margin: 0 auto;"></div>
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  `,
  parameters: {
    docs: {
      description: {
        story: 'Estado de carga skeleton para tablas.',
      },
    },
  },
};

// Employee Type Tabs
export const EmployeeTypeTabs = {
  render: () => `
    <div style="margin-bottom: 1.5rem;">
      <div class="type-filter-tabs">
        <button class="type-tab active">
          <span>全員</span>
          <span class="tab-count">150</span>
        </button>
        <button class="type-tab">
          <span>派遣</span>
          <span class="tab-count">80</span>
        </button>
        <button class="type-tab">
          <span>請負</span>
          <span class="tab-count">45</span>
        </button>
        <button class="type-tab">
          <span>社員</span>
          <span class="tab-count">25</span>
        </button>
      </div>
    </div>

    <div class="glass-panel" style="overflow-x: auto;">
      <table style="width: 100%; border-collapse: collapse;">
        <thead>
          <tr>
            <th style="text-align: left; padding: 1rem; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; color: var(--color-text-muted); border-bottom: 1px solid rgba(255, 255, 255, 0.1);">社員番号</th>
            <th style="text-align: left; padding: 1rem; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; color: var(--color-text-muted); border-bottom: 1px solid rgba(255, 255, 255, 0.1);">氏名</th>
            <th style="text-align: right; padding: 1rem; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; color: var(--color-text-muted); border-bottom: 1px solid rgba(255, 255, 255, 0.1);">残日数</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); color: var(--color-text-primary); font-family: var(--font-mono);">001</td>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05);">
              <div class="employee-name-cell">
                <span style="color: var(--color-text-primary);">田中 太郎</span>
                <span class="badge-type type-genzai">派遣</span>
              </div>
            </td>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); color: #34d399; text-align: right; font-weight: 600;">15.5</td>
          </tr>
          <tr>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); color: var(--color-text-primary); font-family: var(--font-mono);">002</td>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05);">
              <div class="employee-name-cell">
                <span style="color: var(--color-text-primary);">佐藤 花子</span>
                <span class="badge-type type-ukeoi">請負</span>
              </div>
            </td>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); color: #fbbf24; text-align: right; font-weight: 600;">8.0</td>
          </tr>
          <tr>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); color: var(--color-text-primary); font-family: var(--font-mono);">003</td>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05);">
              <div class="employee-name-cell">
                <span style="color: var(--color-text-primary);">鈴木 一郎</span>
                <span class="badge-type type-staff">社員</span>
              </div>
            </td>
            <td style="padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); color: #f87171; text-align: right; font-weight: 600;">3.0</td>
          </tr>
        </tbody>
      </table>
    </div>
  `,
  parameters: {
    docs: {
      description: {
        story: 'Tabs de filtro por tipo de empleado con tabla filtrada.',
      },
    },
  },
};
