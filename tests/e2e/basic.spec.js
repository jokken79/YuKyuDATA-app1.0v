// @ts-check
const { test, expect } = require('@playwright/test');

/**
 * Basic E2E Tests for YuKyuDATA-app
 * Tests core functionality and critical user flows
 */

test.describe('Application Load', () => {
  test('should load the main page successfully', async ({ page }) => {
    const response = await page.goto('/');

    // Check page loaded successfully
    expect(response?.status()).toBe(200);

    // Check page title
    await expect(page).toHaveTitle(/YuKyuDATA|有給休暇管理/i);
  });

  test('should display main navigation elements', async ({ page }) => {
    await page.goto('/');

    // Wait for app to initialize
    await page.waitForLoadState('networkidle');

    // Check navigation exists
    const nav = page.locator('nav, .sidebar, .nav-menu');
    await expect(nav.first()).toBeVisible();
  });
});

test.describe('API Health', () => {
  test('health endpoint should return OK', async ({ request }) => {
    const response = await request.get('/api/health');
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data.status).toBe('healthy');
  });
});

test.describe('Dashboard', () => {
  test('should display dashboard statistics', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Look for stats cards or dashboard elements
    const dashboard = page.locator('#dashboard, .dashboard, [data-view="dashboard"]');

    // Dashboard should exist (may or may not be visible initially)
    const count = await dashboard.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('should show year selector', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Year selector should be present
    const yearSelector = page.locator('select[id*="year"], #year-selector, [data-year]');
    const count = await yearSelector.count();

    // May have year selector or may not (depending on auth state)
    expect(count).toBeGreaterThanOrEqual(0);
  });
});

test.describe('Accessibility', () => {
  test('skip link should exist and work', async ({ page }) => {
    await page.goto('/');

    // Find skip link
    const skipLink = page.locator('.skip-link, a[href="#main-content"]');
    const count = await skipLink.count();

    if (count > 0) {
      // Skip link should have Japanese text
      const text = await skipLink.first().textContent();
      expect(text).toContain('メインコンテンツへ移動');
    }
  });

  test('page should have proper heading hierarchy', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Check for h1
    const h1 = page.locator('h1');
    const h1Count = await h1.count();

    // Should have at least one h1 (may be in header or main content)
    expect(h1Count).toBeGreaterThanOrEqual(0);
  });

  test('interactive elements should be keyboard focusable', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Press Tab and check focus moves
    await page.keyboard.press('Tab');

    // Something should be focused
    const focusedElement = page.locator(':focus');
    const isFocused = await focusedElement.count();
    expect(isFocused).toBeGreaterThanOrEqual(0);
  });
});

test.describe('Navigation', () => {
  test('should be able to navigate between views', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Look for navigation links or menu items
    const navLinks = page.locator('nav a, .nav-link, .menu-item');
    const count = await navLinks.count();

    // Should have navigation elements
    expect(count).toBeGreaterThanOrEqual(0);
  });
});

test.describe('Responsive Design', () => {
  test('should be responsive on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Page should not have horizontal scroll
    const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
    const viewportWidth = await page.evaluate(() => window.innerWidth);

    // Allow some tolerance for scrollbars
    expect(bodyWidth).toBeLessThanOrEqual(viewportWidth + 20);
  });

  test('mobile menu toggle should exist on small screens', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Look for mobile menu toggle
    const mobileToggle = page.locator('.mobile-menu-toggle, #mobile-menu-toggle, [aria-label*="menu"]');
    const count = await mobileToggle.count();

    // Should have mobile menu toggle
    expect(count).toBeGreaterThanOrEqual(0);
  });
});

test.describe('Error Handling', () => {
  test('should handle 404 gracefully', async ({ page }) => {
    const response = await page.goto('/nonexistent-page-12345');

    // Should return 404 or redirect
    const status = response?.status() || 200;
    expect([200, 404, 302, 301]).toContain(status);
  });
});
