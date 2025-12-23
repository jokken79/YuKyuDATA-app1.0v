/**
 * Dashboard E2E Tests
 * Tests completos del dashboard principal de vacaciones
 */

const { test, expect } = require('@playwright/test');

test.describe('Dashboard de Vacaciones', () => {

  test.beforeEach(async ({ page }) => {
    // Navegar al dashboard antes de cada test
    await page.goto('/');
  });

  test('debe cargar el dashboard correctamente', async ({ page }) => {
    // Verificar título de la página
    await expect(page).toHaveTitle(/YuKyuDATA/);

    // Verificar que los KPI cards están visibles
    const kpiCards = page.locator('[data-testid="kpi-card"]');
    await expect(kpiCards).toHaveCount(4);

    // Verificar labels de KPIs
    await expect(page.getByText('Total Empleados')).toBeVisible();
    await expect(page.getByText('Tasa de Uso Promedio')).toBeVisible();
    await expect(page.getByText('Días Totales Usados')).toBeVisible();
    await expect(page.getByText('Balance Total')).toBeVisible();
  });

  test('debe filtrar por año correctamente', async ({ page }) => {
    // Esperar a que carguen los datos
    await page.waitForLoadState('networkidle');

    // Seleccionar año 2024
    await page.locator('[data-testid="year-filter"]').selectOption('2024');

    // Esperar a que se actualicen los datos
    await page.waitForResponse(response =>
      response.url().includes('/api/employees?year=2024') && response.status() === 200
    );

    // Verificar que la tabla muestra datos de 2024
    const firstRow = page.locator('[data-testid="employee-row"]').first();
    await expect(firstRow).toContainText('2024');
  });

  test('debe mostrar gráfico de tasa de uso', async ({ page }) => {
    // Esperar a que se renderice el gráfico
    await page.waitForFunction(() => {
      const canvas = document.querySelector('[data-testid="usage-rate-chart"]');
      return canvas && canvas.getContext('2d');
    });

    // Verificar que el canvas está visible
    const chart = page.locator('[data-testid="usage-rate-chart"]');
    await expect(chart).toBeVisible();

    // Screenshot para regresión visual
    await expect(chart).toHaveScreenshot('usage-rate-chart.png', {
      maxDiffPixels: 100
    });
  });

  test('debe abrir modal de detalle de empleado', async ({ page }) => {
    // Esperar a que cargue la tabla
    await page.waitForSelector('[data-testid="employee-row"]');

    // Click en el primer empleado
    await page.locator('[data-testid="employee-row"]').first().click();

    // Verificar que el modal se abre
    const modal = page.locator('[data-testid="employee-modal"]');
    await expect(modal).toBeVisible();

    // Verificar que muestra información del empleado
    await expect(modal.getByText(/Información del Empleado/)).toBeVisible();

    // Cerrar modal
    await page.locator('[data-testid="modal-close"]').click();
    await expect(modal).not.toBeVisible();
  });

  test('debe cambiar entre modo claro y oscuro', async ({ page }) => {
    // Obtener tema actual
    const bodyBefore = await page.locator('body');
    const themeBefore = await bodyBefore.getAttribute('data-theme');

    // Click en toggle de tema
    await page.locator('[data-testid="theme-toggle"]').click();

    // Verificar que el tema cambió
    const bodyAfter = await page.locator('body');
    const themeAfter = await bodyAfter.getAttribute('data-theme');

    expect(themeAfter).not.toBe(themeBefore);
  });

  test('debe sincronizar datos desde Excel', async ({ page }) => {
    // Click en botón de sync
    await page.getByRole('button', { name: /sync/i }).click();

    // Esperar la respuesta del API
    const response = await page.waitForResponse(
      response => response.url().includes('/api/sync') && response.status() === 200
    );

    // Verificar mensaje de éxito
    await expect(page.locator('[data-testid="success-message"]'))
      .toContainText(/sincronización exitosa/i);
  });

  test('debe exportar datos a Excel', async ({ page }) => {
    // Click en botón de exportar
    const downloadPromise = page.waitForEvent('download');
    await page.getByRole('button', { name: /export/i }).click();

    // Verificar que se descarga el archivo
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toMatch(/\.xlsx$/);
  });

  test('debe mostrar alerta de compliance 5 días', async ({ page }) => {
    // Navegar a compliance
    await page.goto('/compliance');

    // Esperar datos de compliance
    await page.waitForResponse(response =>
      response.url().includes('/api/compliance/5day-check') && response.status() === 200
    );

    // Verificar que muestra alertas si existen
    const alertsTable = page.locator('[data-testid="compliance-alerts"]');
    await expect(alertsTable).toBeVisible();
  });

  test('debe buscar empleado por nombre', async ({ page }) => {
    // Escribir en campo de búsqueda
    const searchInput = page.locator('[data-testid="employee-search"]');
    await searchInput.fill('田中');

    // Esperar a que se filtren los resultados
    await page.waitForTimeout(500); // Debounce

    // Verificar que la tabla muestra solo resultados relevantes
    const rows = page.locator('[data-testid="employee-row"]');
    const count = await rows.count();

    // Verificar que todos los resultados contienen el término de búsqueda
    for (let i = 0; i < count; i++) {
      const rowText = await rows.nth(i).textContent();
      expect(rowText).toContain('田中');
    }
  });

  test('debe calcular KPIs correctamente', async ({ page }) => {
    // Esperar a que carguen los datos
    await page.waitForLoadState('networkidle');

    // Obtener valores de KPIs
    const totalEmployees = await page.locator('[data-testid="kpi-total-employees"]').textContent();
    const avgUsageRate = await page.locator('[data-testid="kpi-avg-usage-rate"]').textContent();

    // Validar que los valores son numéricos
    expect(parseInt(totalEmployees)).toBeGreaterThan(0);
    expect(parseFloat(avgUsageRate)).toBeGreaterThanOrEqual(0);
    expect(parseFloat(avgUsageRate)).toBeLessThanOrEqual(100);
  });
});

test.describe('Responsive Design', () => {

  test('debe adaptarse a mobile correctamente', async ({ page }) => {
    // Cambiar viewport a mobile
    await page.setViewportSize({ width: 375, height: 667 });

    await page.goto('/');

    // Verificar que el menú hamburguesa está visible en mobile
    const mobileMenu = page.locator('[data-testid="mobile-menu"]');
    await expect(mobileMenu).toBeVisible();

    // Verificar que la tabla es scrolleable horizontalmente
    const table = page.locator('[data-testid="employee-table"]');
    await expect(table).toBeVisible();
  });
});

test.describe('Performance', () => {

  test('debe cargar en menos de 3 segundos', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const loadTime = Date.now() - startTime;

    expect(loadTime).toBeLessThan(3000);
  });

  test('gráficos deben renderizar en menos de 2 segundos', async ({ page }) => {
    await page.goto('/');

    const startTime = Date.now();

    await page.waitForFunction(() => {
      const canvas = document.querySelector('[data-testid="usage-rate-chart"]');
      return canvas && canvas.getContext('2d');
    });

    const renderTime = Date.now() - startTime;

    expect(renderTime).toBeLessThan(2000);
  });
});
