/**
 * Modal Component Stories
 * Storybook documentation and examples for the Modal component
 */

import { Modal } from './Modal.js';
import '../../../static/css/main.css';
import '../../../static/css/design-system/accessibility-wcag-aa.css';

export default {
  title: 'Components/Modal',
  component: Modal,
  parameters: {
    docs: {
      description: {
        component: 'Accessible modal/dialog component with focus management and keyboard navigation (WCAG AA compliant)',
      },
    },
    a11y: {
      config: {
        rules: [
          {
            id: 'color-contrast',
            enabled: true,
          },
        ],
      },
    },
  },
  tags: ['autodocs'],
};

const Template = (args) => {
  const container = document.createElement('div');
  const button = document.createElement('button');
  button.textContent = 'モーダルを開く';
  button.className = 'btn btn-primary';

  button.addEventListener('click', () => {
    const modal = new Modal(args);
    modal.open();
  });

  container.appendChild(button);
  return container;
};

/**
 * Basic confirmation modal
 */
export const Confirmation = Template.bind({});
Confirmation.args = {
  title: '確認',
  content: '本当に削除しますか？',
  buttons: [
    {
      text: 'キャンセル',
      variant: 'secondary',
      action: 'close',
    },
    {
      text: '削除する',
      variant: 'danger',
      action: 'confirm',
    },
  ],
  onConfirm: () => console.log('削除が確認されました'),
  onCancel: () => console.log('キャンセルされました'),
};

Confirmation.parameters = {
  docs: {
    description: {
      story: '削除またはリスクのある操作の確認用',
    },
  },
};

/**
 * Form modal
 */
export const FormModal = Template.bind({});
FormModal.args = {
  title: '新規有給休暇申請',
  content: `
    <form>
      <div class="form-group">
        <label for="employee" class="form-label">社員番号 <span class="required">*</span></label>
        <input type="text" id="employee" class="form-input" required aria-required="true" placeholder="例: 001">
      </div>
      <div class="form-group">
        <label for="start-date" class="form-label">開始日 <span class="required">*</span></label>
        <input type="date" id="start-date" class="form-input" required aria-required="true">
      </div>
      <div class="form-group">
        <label for="days" class="form-label">日数 <span class="required">*</span></label>
        <input type="number" id="days" class="form-input" min="0.5" max="40" step="0.5" required aria-required="true" placeholder="0.5">
      </div>
    </form>
  `,
  buttons: [
    {
      text: 'キャンセル',
      variant: 'secondary',
      action: 'close',
    },
    {
      text: '申請する',
      variant: 'primary',
      action: 'confirm',
    },
  ],
  onConfirm: () => console.log('申請が送信されました'),
};

FormModal.parameters = {
  docs: {
    description: {
      story: 'フォーム入力用のモーダル',
    },
  },
};

/**
 * Alert modal
 */
export const Alert = Template.bind({});
Alert.args = {
  title: 'エラー',
  content: 'システムエラーが発生しました。管理者に連絡してください。',
  type: 'error',
  buttons: [
    {
      text: '了解',
      variant: 'primary',
      action: 'close',
    },
  ],
};

Alert.parameters = {
  docs: {
    description: {
      story: 'ユーザーへの警告またはエラーメッセージ表示',
    },
  },
};

/**
 * Success modal
 */
export const Success = Template.bind({});
Success.args = {
  title: '完了',
  content: '有給休暇が正常に申請されました。',
  type: 'success',
  buttons: [
    {
      text: '了解',
      variant: 'primary',
      action: 'close',
    },
  ],
};

Success.parameters = {
  docs: {
    description: {
      story: '成功メッセージ表示用',
    },
  },
};

/**
 * Accessibility Demo
 */
export const AccessibilityDemo = Template.bind({});
AccessibilityDemo.args = {
  title: 'アクセシビリティ対応モーダル',
  content: `
    <div>
      <p>このモーダルは WCAG AA 対応です：</p>
      <ul style="margin-left: 1.5rem; margin-top: 1rem;">
        <li>フォーカストラップ (Tab キーで循環)</li>
        <li>Escape キーでクローズ</li>
        <li>スクリーンリーダー対応 (ARIA roles)</li>
        <li>キーボードナビゲーション完全対応</li>
        <li>色コントラスト確認済み (4.5:1 以上)</li>
      </ul>
    </div>
  `,
  buttons: [
    {
      text: 'キャンセル',
      variant: 'secondary',
      action: 'close',
      ariaLabel: 'このモーダルをキャンセルして閉じる',
    },
    {
      text: '確認',
      variant: 'primary',
      action: 'confirm',
      ariaLabel: 'アクセシビリティ対応を確認して送信',
    },
  ],
};

AccessibilityDemo.parameters = {
  docs: {
    description: {
      story: 'WCAG AA コンプライアンスのデモ',
    },
  },
  a11y: {
    disable: false,
  },
};

/**
 * Large Content Modal
 */
export const LargeContent = Template.bind({});
LargeContent.args = {
  title: '就業規則 - 有給休暇について',
  content: `
    <div style="max-height: 400px; overflow-y: auto;">
      <h3>有給休暇ポリシー</h3>
      <p>
        従業員は労働基準法第 39 条に基づき、以下の有給休暇を取得することができます。
      </p>
      <h4>付与日数</h4>
      <ul>
        <li>試用期間終了時 (6 ヶ月): 10 日</li>
        <li>1 年 6 ヶ月: 11 日</li>
        <li>2 年 6 ヶ月: 12 日</li>
        <li>3 年 6 ヶ月: 14 日</li>
        <li>4 年 6 ヶ月: 16 日</li>
        <li>5 年 6 ヶ月: 18 日</li>
        <li>6 年 6 ヶ月以上: 20 日</li>
      </ul>
      <h4>使用制限</h4>
      <p>
        10 日以上の有給休暇を保有する従業員は、毎年最低 5 日の有給休暇を使用する必要があります。
      </p>
      <h4>繰越</h4>
      <p>
        2 年間の繰越が認められます。3 年目以降の日数は失効します。
      </p>
    </div>
  `,
  buttons: [
    {
      text: '了解しました',
      variant: 'primary',
      action: 'close',
    },
  ],
  maxWidth: '600px',
};

LargeContent.parameters = {
  docs: {
    description: {
      story: 'スクロール可能な大量コンテンツ表示',
    },
  },
};
