/**
 * Edit Yukyu Usage Page Object (Modal)
 */
const { BasePage } = require('./BasePage');

class EditYukyuPage extends BasePage {
  constructor(page) {
    super(page);

    // Modal principal
    this.modal = page.locator('#edit-yukyu-modal');

    // Employee info header
    this.empName = page.locator('#edit-emp-name');
    this.empNum = page.locator('#edit-emp-num');
    this.empBalance = page.locator('#edit-emp-balance');

    // Usage list
    this.usageList = page.locator('#edit-usage-list');
    this.usageItems = page.locator('.usage-item');

    // Add new usage form
    this.addDateInput = page.locator('#add-use-date');
    this.addDaysSelect = page.locator('#add-days-used');
    this.addButton = page.locator('button:has-text("追加")');

    // Summary
    this.totalUsed = page.locator('#edit-total-used');
    this.newBalance = page.locator('#edit-new-balance');

    // Actions
    this.cancelButton = page.locator('button:has-text("キャンセル")');
    this.saveButton = page.locator('#edit-save-btn');
  }

  async isVisible() {
    return await this.modal.isVisible();
  }

  async waitForOpen() {
    await this.modal.waitFor({ state: 'visible', timeout: 5000 });
  }

  async getEmployeeInfo() {
    return {
      name: await this.empName.textContent(),
      number: await this.empNum.textContent(),
      balance: await this.empBalance.textContent(),
    };
  }

  async getUsageCount() {
    return await this.usageItems.count();
  }

  async addUsage(date, days = '1.0') {
    await this.addDateInput.fill(date);
    await this.addDaysSelect.selectOption(days);
    await this.addButton.click();
    await this.page.waitForTimeout(300);
  }

  async updateUsageDays(index, newDays) {
    const item = this.usageItems.nth(index);
    const select = item.locator('select');
    await select.selectOption(newDays);
    await this.page.waitForTimeout(200);
  }

  async deleteUsage(index) {
    const item = this.usageItems.nth(index);
    const deleteBtn = item.locator('.usage-item-delete');
    await deleteBtn.click();
    await this.page.waitForTimeout(200);
  }

  async undoDelete(index) {
    const item = this.usageItems.nth(index);
    const undoBtn = item.locator('button:has-text("戻す")');
    await undoBtn.click();
    await this.page.waitForTimeout(200);
  }

  async getSummary() {
    return {
      totalUsed: await this.totalUsed.textContent(),
      newBalance: await this.newBalance.textContent(),
    };
  }

  async save() {
    await this.saveButton.click();
    await this.page.waitForTimeout(500);
  }

  async cancel() {
    await this.cancelButton.click();
    await this.modal.waitFor({ state: 'hidden' });
  }

  async getPendingChangesCount() {
    const pendingAdd = await this.page.locator('.usage-item.pending-add').count();
    const pendingUpdate = await this.page.locator('.usage-item.pending-update').count();
    const pendingDelete = await this.page.locator('.usage-item.pending-delete').count();
    return { add: pendingAdd, update: pendingUpdate, delete: pendingDelete };
  }
}

module.exports = { EditYukyuPage };
