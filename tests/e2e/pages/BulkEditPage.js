/**
 * Bulk Edit Page Object (Modal)
 */
const { BasePage } = require('./BasePage');

class BulkEditPage extends BasePage {
  constructor(page) {
    super(page);

    // Modal principal
    this.modal = page.locator('#bulk-edit-modal');

    // Toolbar
    this.toolbar = page.locator('#bulk-edit-toolbar');
    this.selectedCount = page.locator('#selected-count');
    this.clearSelectionBtn = page.locator('#clear-selection-btn');
    this.openModalBtn = page.locator('#open-bulk-edit-btn');

    // Checkboxes en tabla
    this.selectAllCheckbox = page.locator('#select-all-checkbox');
    this.employeeCheckboxes = page.locator('.employee-checkbox');

    // Selected employees list
    this.selectedList = page.locator('#bulk-selected-list');
    this.selectedChips = page.locator('.bulk-selected-chip');

    // Edit fields
    this.addGrantedToggle = page.locator('#toggle-add-granted');
    this.addGrantedInput = page.locator('#bulk-add-granted');
    this.addUsedToggle = page.locator('#toggle-add-used');
    this.addUsedInput = page.locator('#bulk-add-used');
    this.setHakenToggle = page.locator('#toggle-set-haken');
    this.setHakenSelect = page.locator('#bulk-set-haken');

    // Preview section
    this.previewSection = page.locator('#bulk-preview-section');
    this.previewTable = page.locator('#bulk-preview-table');
    this.warningsSection = page.locator('#bulk-warnings-section');

    // Actions
    this.previewBtn = page.locator('#bulk-preview-btn');
    this.applyBtn = page.locator('#bulk-apply-btn');
    this.cancelBtn = page.locator('#bulk-cancel-btn');
  }

  async isToolbarVisible() {
    return await this.toolbar.isVisible();
  }

  async isModalVisible() {
    return await this.modal.isVisible();
  }

  async selectEmployee(employeeNum) {
    const checkbox = this.page.locator(`.employee-checkbox[data-employee-num="${employeeNum}"]`);
    await checkbox.check();
    await this.page.waitForTimeout(100);
  }

  async unselectEmployee(employeeNum) {
    const checkbox = this.page.locator(`.employee-checkbox[data-employee-num="${employeeNum}"]`);
    await checkbox.uncheck();
    await this.page.waitForTimeout(100);
  }

  async selectAll() {
    await this.selectAllCheckbox.check();
    await this.page.waitForTimeout(200);
  }

  async unselectAll() {
    await this.selectAllCheckbox.uncheck();
    await this.page.waitForTimeout(200);
  }

  async getSelectedCount() {
    const text = await this.selectedCount.textContent();
    return parseInt(text.match(/\d+/)?.[0] || '0');
  }

  async clearSelection() {
    await this.clearSelectionBtn.click();
    await this.page.waitForTimeout(200);
  }

  async openModal() {
    await this.openModalBtn.click();
    await this.modal.waitFor({ state: 'visible' });
  }

  async setAddGranted(days) {
    await this.addGrantedToggle.check();
    await this.addGrantedInput.fill(String(days));
  }

  async setAddUsed(days) {
    await this.addUsedToggle.check();
    await this.addUsedInput.fill(String(days));
  }

  async setHaken(haken) {
    await this.setHakenToggle.check();
    await this.setHakenSelect.selectOption(haken);
  }

  async preview() {
    await this.previewBtn.click();
    await this.previewSection.waitFor({ state: 'visible' });
  }

  async hasWarnings() {
    return await this.warningsSection.isVisible();
  }

  async getWarningsCount() {
    const warnings = await this.page.locator('.bulk-warning-item').count();
    return warnings;
  }

  async apply() {
    await this.applyBtn.click();
    await this.page.waitForTimeout(500);
  }

  async cancel() {
    await this.cancelBtn.click();
    await this.modal.waitFor({ state: 'hidden' });
  }

  async removeChip(employeeNum) {
    const chip = this.page.locator(`.bulk-selected-chip[data-employee-num="${employeeNum}"] .remove-chip`);
    await chip.click();
  }
}

module.exports = { BulkEditPage };
