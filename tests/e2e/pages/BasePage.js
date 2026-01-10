/**
 * Base Page Object - Funcionalidades comunes
 */
class BasePage {
  constructor(page) {
    this.page = page;

    // Navegación común
    this.navDashboard = page.locator('[data-testid="nav-dashboard"]');
    this.navRequests = page.locator('[data-testid="nav-requests"]');
    this.navCalendar = page.locator('[data-testid="nav-calendar"]');

    // Toast notifications
    this.toastContainer = page.locator('#toast-container');
    this.toastSuccess = page.locator('.toast-success');
    this.toastError = page.locator('.toast-error');

    // Loading overlay
    this.loadingOverlay = page.locator('.loader-overlay.active');

    // Theme toggle
    this.themeToggle = page.locator('[data-testid="theme-toggle"]');

    // Year selector
    this.yearSelect = page.locator('#year-select');
  }

  async goto(path = '/') {
    await this.page.goto(path);
    await this.waitForLoad();
  }

  async waitForLoad() {
    // Esperar a que el overlay de carga desaparezca
    await this.page.waitForFunction(() => {
      const overlay = document.querySelector('.loader-overlay.active');
      return !overlay || overlay.style.display === 'none';
    }, { timeout: 10000 }).catch(() => {});
  }

  async waitForToast(type = 'success') {
    const toast = type === 'success' ? this.toastSuccess : this.toastError;
    await toast.waitFor({ state: 'visible', timeout: 5000 });
    return toast.textContent();
  }

  async selectYear(year) {
    await this.yearSelect.selectOption(String(year));
    await this.waitForLoad();
  }

  async toggleTheme() {
    await this.themeToggle.click();
  }

  async getCurrentTheme() {
    return this.page.evaluate(() => document.documentElement.getAttribute('data-theme'));
  }

  async takeScreenshot(name) {
    await this.page.screenshot({ path: `screenshots/${name}.png` });
  }
}

module.exports = { BasePage };
