/**
 * Dashboard Page Object
 */
const { BasePage } = require('./BasePage');

class DashboardPage extends BasePage {
  constructor(page) {
    super(page);

    // KPI Cards
    this.kpiTotalEmployees = page.locator('[data-testid="kpi-total-employees"]');
    this.kpiTotalUsed = page.locator('[data-testid="kpi-total-used"]');
    this.kpiAvgUsageRate = page.locator('[data-testid="kpi-avg-usage-rate"]');
    this.kpiCompliance = page.locator('[data-testid="kpi-compliance"]');

    // Charts
    this.usageChart = page.locator('#usage-chart');
    this.monthlyTrendChart = page.locator('#monthly-trend-chart');

    // Employee Table
    this.employeeTable = page.locator('#employee-table');
    this.tableBody = page.locator('#table-body');
    this.employeeRows = page.locator('.employee-row');

    // Search and Filters
    this.searchInput = page.locator('#search-input');
    this.factoryFilter = page.locator('#factory-filter');
    this.typeFilter = page.locator('#type-filter');

    // Sync button
    this.syncButton = page.locator('[data-testid="sync-button"]');

    // Employee Detail Modal
    this.detailModal = page.locator('#detail-modal');
    this.modalTitle = page.locator('#modal-title');
    this.modalContent = page.locator('#modal-content');
    this.editYukyuButton = page.locator('button:has-text("有給使用データを編集")');
  }

  async goto() {
    await super.goto('/');
    await this.waitForDashboard();
  }

  async waitForDashboard() {
    await this.employeeTable.waitFor({ state: 'visible', timeout: 15000 });
  }

  async getKPIValues() {
    return {
      totalEmployees: await this.kpiTotalEmployees.textContent(),
      totalUsed: await this.kpiTotalUsed.textContent(),
      avgUsageRate: await this.kpiAvgUsageRate.textContent(),
      compliance: await this.kpiCompliance.textContent(),
    };
  }

  async searchEmployee(query) {
    await this.searchInput.fill(query);
    await this.page.waitForTimeout(300); // Debounce
    await this.waitForLoad();
  }

  async clearSearch() {
    await this.searchInput.clear();
    await this.waitForLoad();
  }

  async filterByFactory(factory) {
    await this.factoryFilter.selectOption(factory);
    await this.waitForLoad();
  }

  async filterByType(type) {
    await this.typeFilter.selectOption(type);
    await this.waitForLoad();
  }

  async getEmployeeCount() {
    return await this.employeeRows.count();
  }

  async clickEmployee(employeeNum) {
    const row = this.page.locator(`.employee-row[data-employee-num="${employeeNum}"]`);
    await row.click();
    await this.detailModal.waitFor({ state: 'visible' });
  }

  async clickFirstEmployee() {
    await this.employeeRows.first().click();
    await this.detailModal.waitFor({ state: 'visible' });
  }

  async closeDetailModal() {
    await this.page.locator('.modal-close-btn').click();
    await this.detailModal.waitFor({ state: 'hidden' });
  }

  async openEditYukyuModal() {
    await this.editYukyuButton.click();
    await this.page.locator('#edit-yukyu-modal').waitFor({ state: 'visible' });
  }

  async syncData() {
    await this.syncButton.click();
    await this.waitForToast('success');
    await this.waitForLoad();
  }

  async getEmployeeData(employeeNum) {
    const row = this.page.locator(`.employee-row[data-employee-num="${employeeNum}"]`);
    return {
      name: await row.locator('td:nth-child(2)').textContent(),
      granted: await row.locator('td:nth-child(5)').textContent(),
      used: await row.locator('td:nth-child(6)').textContent(),
      balance: await row.locator('td:nth-child(7)').textContent(),
    };
  }
}

module.exports = { DashboardPage };
