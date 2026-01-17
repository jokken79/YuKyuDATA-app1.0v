// @ts-check
const { defineConfig, devices } = require('@playwright/test');

/**
 * Playwright Test Configuration
 * Configuración para tests E2E de YuKyuDATA-app
 * @see https://playwright.dev/docs/test-configuration
 */
module.exports = defineConfig({
  testDir: './tests/e2e',

  /* Timeout por test */
  timeout: 30 * 1000,

  /* Expect timeout */
  expect: {
    timeout: 5000
  },

  /* Configuración de reintentos */
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,

  /* Workers para paralelización */
  workers: process.env.CI ? 1 : undefined,

  /* Reporter configuration */
  reporter: [
    ['html'],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/junit.xml' }],
    ['list']
  ],

  /* Configuración compartida para todos los tests */
  use: {
    /* Base URL de la aplicación */
    baseURL: process.env.BASE_URL || 'http://localhost:8000',

    /* Recolectar trazas en primer retry */
    trace: 'on-first-retry',

    /* Screenshots solo en fallo */
    screenshot: 'only-on-failure',

    /* Video solo en fallo */
    video: 'retain-on-failure',

    /* Configuración de navegador */
    viewport: { width: 1280, height: 720 },
    ignoreHTTPSErrors: true,

    /* Timeout de navegación */
    navigationTimeout: 15000,
    actionTimeout: 10000,
  },

  /* Configurar proyectos para diferentes navegadores */
  projects: [
    /* Setup project para autenticación */
    {
      name: 'setup',
      testMatch: /auth\.setup\.js/,
    },

    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },

    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },

    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },

    /* Tests en mobile viewports */
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },

    /* Tests con autenticación persistente */
    {
      name: 'authenticated',
      use: {
        ...devices['Desktop Chrome'],
        storageState: 'tests/e2e/.auth/user.json',
      },
      dependencies: ['setup'],
    },
  ],

  /* Ejecutar servidor antes de los tests */
  webServer: {
    command: process.env.CI ? 'python -m uvicorn main:app --host 0.0.0.0 --port 8000' : 'npm run start:test',
    url: 'http://localhost:8000',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },
});
