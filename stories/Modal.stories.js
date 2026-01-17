/**
 * Modal/Dialog Stories - YuKyuDATA Design System
 *
 * Dialogos modales para confirmaciones, formularios y alertas.
 * Incluye accesibilidad completa con ARIA y manejo de focus.
 */

export default {
  title: 'Components/Modal',
  tags: ['autodocs'],
  parameters: {
    docs: {
      description: {
        component: `
## Dialogos Modales

Sistema de modales con:
- Overlay con backdrop blur
- Animaciones de entrada/salida
- Focus trap para accesibilidad
- Soporte para diferentes tipos (info, warning, danger)

### Uso basico
\`\`\`html
<div class="dialog-overlay active" role="dialog" aria-modal="true">
  <div class="dialog">
    Contenido del dialog
  </div>
</div>
\`\`\`
        `,
      },
    },
  },
};

// Confirmation Dialog
export const Confirmation = {
  render: () => `
    <div style="position: relative; min-height: 400px; background: rgba(0, 0, 0, 0.7); border-radius: 16px; display: flex; align-items: center; justify-content: center;">
      <div class="dialog" style="transform: none; opacity: 1; position: relative;">
        <div class="dialog-header">
          <div class="dialog-icon info">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"></circle>
              <path d="M12 16v-4"></path>
              <path d="M12 8h.01"></path>
            </svg>
          </div>
          <div class="dialog-header-text">
            <h3>有給休暇を申請しますか？</h3>
            <p>申請内容を確認してください。承認後は自動的に残日数から差し引かれます。</p>
          </div>
        </div>
        <div class="dialog-footer">
          <button class="dialog-btn dialog-btn-cancel">キャンセル</button>
          <button class="dialog-btn dialog-btn-confirm">申請する</button>
        </div>
      </div>
    </div>
  `,
  parameters: {
    docs: {
      description: {
        story: 'Dialog de confirmacion para solicitudes de vacaciones.',
      },
    },
  },
};

// Warning Dialog
export const Warning = {
  render: () => `
    <div style="position: relative; min-height: 400px; background: rgba(0, 0, 0, 0.7); border-radius: 16px; display: flex; align-items: center; justify-content: center;">
      <div class="dialog" style="transform: none; opacity: 1; position: relative;">
        <div class="dialog-header">
          <div class="dialog-icon warning">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
              <line x1="12" y1="9" x2="12" y2="13"></line>
              <line x1="12" y1="17" x2="12.01" y2="17"></line>
            </svg>
          </div>
          <div class="dialog-header-text">
            <h3>5日取得義務の警告</h3>
            <p>この従業員は年度内に最低5日の有給休暇を取得する必要があります。現在の取得日数は3日です。</p>
          </div>
        </div>
        <div class="dialog-footer">
          <button class="dialog-btn dialog-btn-cancel">閉じる</button>
          <button class="dialog-btn dialog-btn-confirm">詳細を確認</button>
        </div>
      </div>
    </div>
  `,
  parameters: {
    docs: {
      description: {
        story: 'Dialog de advertencia para cumplimiento de 5 dias obligatorios.',
      },
    },
  },
};

// Danger/Delete Dialog
export const Danger = {
  render: () => `
    <div style="position: relative; min-height: 400px; background: rgba(0, 0, 0, 0.7); border-radius: 16px; display: flex; align-items: center; justify-content: center;">
      <div class="dialog" style="transform: none; opacity: 1; position: relative;">
        <div class="dialog-header">
          <div class="dialog-icon danger">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="3 6 5 6 21 6"></polyline>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
              <line x1="10" y1="11" x2="10" y2="17"></line>
              <line x1="14" y1="11" x2="14" y2="17"></line>
            </svg>
          </div>
          <div class="dialog-header-text">
            <h3>申請を削除しますか？</h3>
            <p>この操作は取り消せません。削除された申請は復元できません。</p>
          </div>
        </div>
        <div class="dialog-footer">
          <button class="dialog-btn dialog-btn-cancel">キャンセル</button>
          <button class="dialog-btn dialog-btn-danger">削除する</button>
        </div>
      </div>
    </div>
  `,
  parameters: {
    docs: {
      description: {
        story: 'Dialog de peligro para acciones destructivas como eliminar.',
      },
    },
  },
};

// Dialog with Input
export const WithInput = {
  render: () => `
    <div style="position: relative; min-height: 450px; background: rgba(0, 0, 0, 0.7); border-radius: 16px; display: flex; align-items: center; justify-content: center;">
      <div class="dialog" style="transform: none; opacity: 1; position: relative;">
        <div class="dialog-header">
          <div class="dialog-icon info">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
            </svg>
          </div>
          <div class="dialog-header-text">
            <h3>コメントを追加</h3>
            <p>申請に関するコメントを入力してください。</p>
          </div>
        </div>
        <div class="dialog-body">
          <textarea
            class="dialog-input"
            placeholder="コメントを入力..."
            style="min-height: 100px; resize: vertical;"></textarea>
        </div>
        <div class="dialog-footer">
          <button class="dialog-btn dialog-btn-cancel">キャンセル</button>
          <button class="dialog-btn dialog-btn-confirm">保存</button>
        </div>
      </div>
    </div>
  `,
  parameters: {
    docs: {
      description: {
        story: 'Dialog con campo de entrada para comentarios.',
      },
    },
  },
};

// Dialog with Form
export const WithForm = {
  render: () => `
    <div style="position: relative; min-height: 550px; background: rgba(0, 0, 0, 0.7); border-radius: 16px; display: flex; align-items: center; justify-content: center;">
      <div class="dialog" style="transform: none; opacity: 1; position: relative; max-width: 480px;">
        <div class="dialog-header">
          <div class="dialog-icon info">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
              <line x1="16" y1="2" x2="16" y2="6"></line>
              <line x1="8" y1="2" x2="8" y2="6"></line>
              <line x1="3" y1="10" x2="21" y2="10"></line>
            </svg>
          </div>
          <div class="dialog-header-text">
            <h3>有給取得日を編集</h3>
            <p>取得日と日数を修正できます。</p>
          </div>
        </div>
        <div class="dialog-body">
          <div style="display: grid; gap: 1rem;">
            <div>
              <label style="display: block; margin-bottom: 0.5rem; font-size: 0.875rem; color: var(--color-text-secondary);">
                取得日
              </label>
              <input type="date" class="dialog-input" value="2025-01-17">
            </div>
            <div>
              <label style="display: block; margin-bottom: 0.5rem; font-size: 0.875rem; color: var(--color-text-secondary);">
                日数
              </label>
              <select class="dialog-input">
                <option value="1">1日（全日）</option>
                <option value="0.5">0.5日（半日）</option>
              </select>
            </div>
            <div>
              <label style="display: block; margin-bottom: 0.5rem; font-size: 0.875rem; color: var(--color-text-secondary);">
                備考
              </label>
              <input type="text" class="dialog-input" placeholder="オプション">
            </div>
          </div>
        </div>
        <div class="dialog-footer">
          <button class="dialog-btn dialog-btn-cancel">キャンセル</button>
          <button class="dialog-btn dialog-btn-confirm">保存する</button>
        </div>
      </div>
    </div>
  `,
  parameters: {
    docs: {
      description: {
        story: 'Dialog con formulario completo para editar fechas de vacaciones.',
      },
    },
  },
};

// Toast Notifications (relacionado con modales)
export const Toast = {
  render: () => `
    <div style="display: flex; flex-direction: column; gap: 1rem; max-width: 400px;">
      <div class="toast success" style="transform: none; opacity: 1; position: relative;">
        <div class="toast-icon">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
        </div>
        <div class="toast-content">
          <div class="toast-title">申請が承認されました</div>
          <div class="toast-message">田中太郎さんの有給休暇申請が承認されました。</div>
        </div>
        <button class="toast-close" aria-label="閉じる">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>

      <div class="toast error" style="transform: none; opacity: 1; position: relative;">
        <div class="toast-icon">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="15" y1="9" x2="9" y2="15"></line>
            <line x1="9" y1="9" x2="15" y2="15"></line>
          </svg>
        </div>
        <div class="toast-content">
          <div class="toast-title">エラーが発生しました</div>
          <div class="toast-message">申請の処理中にエラーが発生しました。</div>
        </div>
        <button class="toast-close" aria-label="閉じる">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>

      <div class="toast warning" style="transform: none; opacity: 1; position: relative;">
        <div class="toast-icon">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
            <line x1="12" y1="9" x2="12" y2="13"></line>
            <line x1="12" y1="17" x2="12.01" y2="17"></line>
          </svg>
        </div>
        <div class="toast-content">
          <div class="toast-title">残日数が少なくなっています</div>
          <div class="toast-message">有給残日数が5日を下回りました。</div>
        </div>
        <button class="toast-close" aria-label="閉じる">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>

      <div class="toast info" style="transform: none; opacity: 1; position: relative;">
        <div class="toast-icon">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="16" x2="12" y2="12"></line>
            <line x1="12" y1="8" x2="12.01" y2="8"></line>
          </svg>
        </div>
        <div class="toast-content">
          <div class="toast-title">新しい申請があります</div>
          <div class="toast-message">3件の承認待ち申請があります。</div>
        </div>
        <button class="toast-close" aria-label="閉じる">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>
    </div>
  `,
  parameters: {
    docs: {
      description: {
        story: 'Notificaciones toast en los 4 tipos: success, error, warning e info.',
      },
    },
  },
};
