/**
 * Leave Request Page Object
 */
const { BasePage } = require('./BasePage');

class LeaveRequestPage extends BasePage {
  constructor(page) {
    super(page);

    // Navigation to requests tab
    this.requestsTab = page.locator('[data-tab="requests"]');

    // Form elements
    this.factoryFilter = page.locator('#factory-filter');
    this.empSearch = page.locator('#emp-search');
    this.empSearchResults = page.locator('#emp-search-results');
    this.selectedEmpInfo = page.locator('#selected-emp-info');
    this.selectedEmpName = page.locator('#selected-emp-name');
    this.selectedEmpBalance = page.locator('#selected-emp-balance');

    // Date inputs
    this.startDate = page.locator('#start-date');
    this.endDate = page.locator('#end-date');

    // Leave type
    this.leaveType = page.locator('#leave-type');
    this.daysRequested = page.locator('#days-requested');
    this.hoursRequested = page.locator('#hours-requested');
    this.leaveReason = page.locator('#leave-reason');

    // Buttons
    this.confirmBtn = page.locator('#confirm-request-btn');
    this.submitBtn = page.locator('#submit-request-btn');

    // Confirmation modal
    this.confirmModal = page.locator('#confirm-modal');
    this.confirmEmployee = page.locator('#confirm-employee');
    this.confirmDates = page.locator('#confirm-dates');
    this.confirmAmount = page.locator('#confirm-amount');
    this.confirmSubmitBtn = page.locator('#confirm-submit-btn');

    // Pending requests list
    this.pendingList = page.locator('#pending-requests');
    this.pendingItems = page.locator('.request-item');

    // Validation messages
    this.empValidation = page.locator('#emp-search-validation');
    this.startDateValidation = page.locator('#start-date-validation');
    this.endDateValidation = page.locator('#end-date-validation');
    this.daysValidation = page.locator('#days-validation');
  }

  async goto() {
    await super.goto('/');
    await this.requestsTab.click();
    await this.page.waitForTimeout(300);
  }

  async searchEmployee(query) {
    await this.empSearch.fill(query);
    await this.page.waitForTimeout(500);
    await this.empSearchResults.waitFor({ state: 'visible' });
  }

  async selectFirstEmployee() {
    const firstResult = this.empSearchResults.locator('.search-result-item').first();
    await firstResult.click();
    await this.selectedEmpInfo.waitFor({ state: 'visible' });
  }

  async selectEmployee(employeeNum) {
    const result = this.empSearchResults.locator(`.search-result-item[data-employee-num="${employeeNum}"]`);
    await result.click();
    await this.selectedEmpInfo.waitFor({ state: 'visible' });
  }

  async getSelectedEmployeeInfo() {
    return {
      name: await this.selectedEmpName.textContent(),
      balance: await this.selectedEmpBalance.textContent(),
    };
  }

  async setDates(start, end) {
    await this.startDate.fill(start);
    await this.endDate.fill(end);
  }

  async setLeaveType(type) {
    await this.leaveType.selectOption(type);
    await this.page.waitForTimeout(200);
  }

  async setDaysRequested(days) {
    await this.daysRequested.fill(String(days));
  }

  async setReason(reason) {
    await this.leaveReason.fill(reason);
  }

  async showConfirmation() {
    await this.confirmBtn.click();
    await this.confirmModal.waitFor({ state: 'visible' });
  }

  async submitFromConfirmation() {
    await this.confirmSubmitBtn.click();
    await this.page.waitForTimeout(500);
  }

  async submitRequest(employeeQuery, startDate, endDate, days = 1, type = 'full', reason = '') {
    await this.searchEmployee(employeeQuery);
    await this.selectFirstEmployee();
    await this.setDates(startDate, endDate);
    await this.setLeaveType(type);
    await this.setDaysRequested(days);
    if (reason) await this.setReason(reason);
    await this.showConfirmation();
    await this.submitFromConfirmation();
  }

  async getPendingCount() {
    return await this.pendingItems.count();
  }

  async approveRequest(index = 0) {
    const item = this.pendingItems.nth(index);
    const approveBtn = item.locator('.btn-approve');
    await approveBtn.click();
    await this.page.waitForTimeout(500);
  }

  async rejectRequest(index = 0, reason = 'Test rejection') {
    const item = this.pendingItems.nth(index);
    const rejectBtn = item.locator('.btn-reject');
    await rejectBtn.click();

    // Fill rejection reason if modal appears
    const reasonInput = this.page.locator('#reject-reason');
    if (await reasonInput.isVisible()) {
      await reasonInput.fill(reason);
      await this.page.locator('#confirm-reject-btn').click();
    }
    await this.page.waitForTimeout(500);
  }

  async getRequestInfo(index = 0) {
    const item = this.pendingItems.nth(index);
    return {
      employee: await item.locator('.request-employee').textContent(),
      dates: await item.locator('.request-dates').textContent(),
      days: await item.locator('.request-days').textContent(),
      status: await item.locator('.request-status').textContent(),
    };
  }
}

module.exports = { LeaveRequestPage };
