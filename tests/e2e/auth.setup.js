// @ts-check
const { test as setup, expect } = require('@playwright/test');
const path = require('path');

const authFile = path.join(__dirname, '.auth/user.json');

/**
 * Authentication setup for E2E tests
 * Logs in and saves session state for reuse
 */
setup('authenticate', async ({ page }) => {
  // Navigate to login page
  await page.goto('/');

  // Check if login form exists
  const loginForm = page.locator('form[id*="login"], #login-form, .login-form');
  const formExists = await loginForm.count() > 0;

  if (formExists) {
    // Fill in credentials (use test credentials)
    const usernameInput = page.locator('input[name="username"], input[type="text"]').first();
    const passwordInput = page.locator('input[name="password"], input[type="password"]');

    await usernameInput.fill(process.env.TEST_USERNAME || 'admin');
    await passwordInput.fill(process.env.TEST_PASSWORD || 'admin');

    // Submit form
    const submitButton = page.locator('button[type="submit"], input[type="submit"]');
    await submitButton.click();

    // Wait for navigation or dashboard
    await page.waitForLoadState('networkidle');
  }

  // Save storage state
  await page.context().storageState({ path: authFile });
});
