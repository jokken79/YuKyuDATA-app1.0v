/**
 * Authentication Setup for Playwright Tests
 * Realiza login una vez y guarda el estado para reutilizar en tests
 */

const { test as setup } = require('@playwright/test');
const path = require('path');

const authFile = path.join(__dirname, '.auth/user.json');

setup('authenticate', async ({ page }) => {
  // Navegar a la página de login
  await page.goto('/');

  // Realizar login
  await page.getByRole('button', { name: /login/i }).click();

  await page.locator('[data-testid="username"]').fill('admin');
  await page.locator('[data-testid="password"]').fill('admin123');
  await page.locator('[data-testid="login-submit"]').click();

  // Esperar a que la navegación complete
  await page.waitForURL('/dashboard');

  // Verificar que el login fue exitoso
  await page.waitForSelector('[data-testid="user-menu"]');

  // Guardar estado de autenticación
  await page.context().storageState({ path: authFile });
});
