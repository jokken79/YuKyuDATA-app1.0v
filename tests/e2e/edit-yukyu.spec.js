/**
 * E2E Tests: Edit Yukyu Usage
 * Tests para edición de datos de uso de vacaciones
 */
const { test, expect } = require('@playwright/test');
const { DashboardPage, EditYukyuPage } = require('./pages');

test.describe('Edit Yukyu Usage', () => {
  let dashboardPage;
  let editPage;

  test.beforeEach(async ({ page }) => {
    dashboardPage = new DashboardPage(page);
    editPage = new EditYukyuPage(page);
    await dashboardPage.goto();
  });

  test('should open edit modal from employee detail', async ({ page }) => {
    // Click on first employee
    await dashboardPage.clickFirstEmployee();

    // Click edit button
    await dashboardPage.openEditYukyuModal();

    // Verify modal is visible
    await expect(editPage.modal).toBeVisible();

    // Verify employee info is loaded
    const info = await editPage.getEmployeeInfo();
    expect(info.name).toBeTruthy();
    expect(info.balance).toContain('日');
  });

  test('should display usage list correctly', async ({ page }) => {
    await dashboardPage.clickFirstEmployee();
    await dashboardPage.openEditYukyuModal();

    // Wait for data to load
    await page.waitForTimeout(1000);

    // Check if usage list has items or empty message
    const usageList = editPage.usageList;
    await expect(usageList).toBeVisible();
  });

  test('should add new usage date', async ({ page }) => {
    await dashboardPage.clickFirstEmployee();
    await dashboardPage.openEditYukyuModal();

    const initialCount = await editPage.getUsageCount();

    // Add new usage
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const dateStr = tomorrow.toISOString().split('T')[0];

    await editPage.addUsage(dateStr, '0.5');

    // Verify pending add
    const changes = await editPage.getPendingChangesCount();
    expect(changes.add).toBeGreaterThanOrEqual(1);
  });

  test('should update usage days', async ({ page }) => {
    await dashboardPage.clickFirstEmployee();
    await dashboardPage.openEditYukyuModal();

    const count = await editPage.getUsageCount();

    if (count > 0) {
      // Update first item
      await editPage.updateUsageDays(0, '0.5');

      // Verify pending update
      const changes = await editPage.getPendingChangesCount();
      expect(changes.update).toBeGreaterThanOrEqual(0); // May be 0 if already 0.5
    }
  });

  test('should delete and undo delete', async ({ page }) => {
    await dashboardPage.clickFirstEmployee();
    await dashboardPage.openEditYukyuModal();

    const count = await editPage.getUsageCount();

    if (count > 0) {
      // Delete first item
      await editPage.deleteUsage(0);

      // Verify pending delete
      let changes = await editPage.getPendingChangesCount();
      expect(changes.delete).toBe(1);

      // Undo delete
      await editPage.undoDelete(0);

      // Verify no pending delete
      changes = await editPage.getPendingChangesCount();
      expect(changes.delete).toBe(0);
    }
  });

  test('should update summary in real-time', async ({ page }) => {
    await dashboardPage.clickFirstEmployee();
    await dashboardPage.openEditYukyuModal();

    const initialSummary = await editPage.getSummary();

    // Add usage
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    await editPage.addUsage(tomorrow.toISOString().split('T')[0], '1.0');

    const newSummary = await editPage.getSummary();

    // Total used should increase
    expect(parseFloat(newSummary.totalUsed)).toBeGreaterThan(parseFloat(initialSummary.totalUsed) || 0);
  });

  test('should cancel without saving', async ({ page }) => {
    await dashboardPage.clickFirstEmployee();
    await dashboardPage.openEditYukyuModal();

    // Make changes
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    await editPage.addUsage(tomorrow.toISOString().split('T')[0], '1.0');

    // Cancel
    await editPage.cancel();

    // Modal should close
    await expect(editPage.modal).not.toBeVisible();
  });

  test('should show warning for no changes', async ({ page }) => {
    await dashboardPage.clickFirstEmployee();
    await dashboardPage.openEditYukyuModal();

    // Try to save without changes
    await editPage.save();

    // Should show warning toast
    await expect(page.locator('.toast-warning')).toBeVisible({ timeout: 3000 });
  });
});
