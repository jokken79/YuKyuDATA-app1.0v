/**
 * Leave Requests E2E Tests
 * Tests del flujo completo de solicitudes de vacaciones
 */

const { test, expect } = require('@playwright/test');

test.describe('Solicitudes de Vacaciones', () => {

  test.use({ storageState: 'tests/e2e/.auth/user.json' });

  test.beforeEach(async ({ page }) => {
    await page.goto('/leave-requests');
  });

  test('debe crear nueva solicitud de vacaciones', async ({ page }) => {
    // Click en botón "Nueva Solicitud"
    await page.getByRole('button', { name: /nueva solicitud/i }).click();

    // Llenar formulario
    await page.locator('[data-testid="employee-num"]').fill('001');
    await page.locator('[data-testid="employee-name"]').fill('田中太郎');
    await page.locator('[data-testid="start-date"]').fill('2024-12-25');
    await page.locator('[data-testid="end-date"]').fill('2024-12-26');
    await page.locator('[data-testid="leave-type"]').selectOption('annual');
    await page.locator('[data-testid="reason"]').fill('Vacaciones de fin de año');

    // Enviar formulario
    await page.locator('[data-testid="submit-request"]').click();

    // Esperar respuesta del API
    await page.waitForResponse(response =>
      response.url().includes('/api/leave-requests') &&
      response.status() === 201
    );

    // Verificar mensaje de éxito
    await expect(page.locator('[data-testid="success-message"]'))
      .toContainText(/solicitud creada exitosamente/i);
  });

  test('debe validar fechas de solicitud', async ({ page }) => {
    await page.getByRole('button', { name: /nueva solicitud/i }).click();

    // Intentar fecha de fin anterior a fecha de inicio
    await page.locator('[data-testid="start-date"]').fill('2024-12-26');
    await page.locator('[data-testid="end-date"]').fill('2024-12-25');

    await page.locator('[data-testid="submit-request"]').click();

    // Verificar mensaje de error
    await expect(page.locator('[data-testid="error-message"]'))
      .toContainText(/fecha de fin debe ser posterior/i);
  });

  test('manager debe aprobar solicitud', async ({ page }) => {
    // Buscar solicitud pendiente
    const pendingRequest = page.locator('[data-testid="request-status-PENDING"]').first();
    await pendingRequest.click();

    // Click en botón aprobar
    await page.getByRole('button', { name: /aprobar/i }).click();

    // Confirmar aprobación
    await page.getByRole('button', { name: /confirmar/i }).click();

    // Esperar respuesta
    await page.waitForResponse(response =>
      response.url().includes('/approve') &&
      response.status() === 200
    );

    // Verificar cambio de estado
    await expect(page.locator('[data-testid="request-status"]'))
      .toContainText('APPROVED');
  });

  test('debe filtrar solicitudes por estado', async ({ page }) => {
    // Seleccionar filtro "Aprobadas"
    await page.locator('[data-testid="status-filter"]').selectOption('APPROVED');

    // Esperar actualización
    await page.waitForTimeout(500);

    // Verificar que todas las solicitudes visibles están aprobadas
    const requests = page.locator('[data-testid="request-row"]');
    const count = await requests.count();

    for (let i = 0; i < count; i++) {
      await expect(requests.nth(i).locator('[data-testid="status-badge"]'))
        .toContainText('APPROVED');
    }
  });

  test('debe calcular días automáticamente', async ({ page }) => {
    await page.getByRole('button', { name: /nueva solicitud/i }).click();

    // Seleccionar rango de fechas
    await page.locator('[data-testid="start-date"]').fill('2024-12-25');
    await page.locator('[data-testid="end-date"]').fill('2024-12-27');

    // Verificar cálculo automático de días
    const daysField = page.locator('[data-testid="days-calculated"]');
    await expect(daysField).toHaveValue('3');
  });

  test('debe mostrar historial de solicitudes del empleado', async ({ page }) => {
    // Buscar empleado
    await page.locator('[data-testid="employee-search"]').fill('001');

    // Click en "Ver Historial"
    await page.getByRole('button', { name: /ver historial/i }).click();

    // Verificar que se muestra el modal de historial
    const historyModal = page.locator('[data-testid="history-modal"]');
    await expect(historyModal).toBeVisible();

    // Verificar que muestra solicitudes del empleado
    await expect(historyModal.getByText('田中太郎')).toBeVisible();
  });
});
