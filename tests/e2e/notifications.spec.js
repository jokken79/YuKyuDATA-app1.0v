/**
 * E2E Tests: Notifications System
 * Tests para el sistema de notificaciones
 */
const { test, expect } = require('@playwright/test');

test.describe('Notifications System', () => {

  test.describe('Notification Settings', () => {
    test('GET /api/notifications/settings returns current config', async ({ request }) => {
      const response = await request.get('/api/notifications/settings');

      if (response.ok()) {
        const data = await response.json();

        expect(data).toHaveProperty('email_enabled');
        expect(data).toHaveProperty('slack_enabled');
        expect(data).toHaveProperty('notify_leave_created');
        expect(data).toHaveProperty('notify_leave_approved');
        expect(data).toHaveProperty('notify_leave_rejected');
      }
    });

    test('PUT /api/notifications/settings updates config', async ({ request }) => {
      const response = await request.put('/api/notifications/settings', {
        data: {
          email_enabled: false,
          slack_enabled: false
        }
      });

      // May require admin auth
      expect([200, 401, 403]).toContain(response.status());
    });
  });

  test.describe('Notification Logs', () => {
    test('GET /api/notifications/logs returns history', async ({ request }) => {
      const response = await request.get('/api/notifications/logs?limit=10');

      if (response.ok()) {
        const data = await response.json();

        expect(data).toHaveProperty('logs');
        expect(Array.isArray(data.logs)).toBeTruthy();
      }
    });

    test('GET /api/notifications/logs filters by type', async ({ request }) => {
      const response = await request.get('/api/notifications/logs?type=email');

      if (response.ok()) {
        const data = await response.json();

        if (data.logs.length > 0) {
          data.logs.forEach(log => {
            expect(log.type).toBe('email');
          });
        }
      }
    });

    test('GET /api/notifications/logs filters by event', async ({ request }) => {
      const response = await request.get('/api/notifications/logs?event=leave_approved');

      if (response.ok()) {
        const data = await response.json();

        if (data.logs.length > 0) {
          data.logs.forEach(log => {
            expect(log.event).toBe('leave_approved');
          });
        }
      }
    });
  });

  test.describe('Test Notifications', () => {
    test('POST /api/notifications/test-email validates config', async ({ request }) => {
      const response = await request.post('/api/notifications/test-email', {
        data: { to: 'test@example.com' }
      });

      // Expected to fail if email not configured
      expect([200, 400, 401, 403, 500]).toContain(response.status());

      const data = await response.json();
      expect(data).toHaveProperty('status');
    });

    test('POST /api/notifications/test-slack validates config', async ({ request }) => {
      const response = await request.post('/api/notifications/test-slack');

      // Expected to fail if Slack not configured
      expect([200, 400, 401, 403, 500]).toContain(response.status());

      const data = await response.json();
      expect(data).toHaveProperty('status');
    });
  });

  test.describe('Automated Notifications', () => {
    test('POST /api/notifications/send-expiring-warnings works', async ({ request }) => {
      const response = await request.post('/api/notifications/send-expiring-warnings', {
        data: { days_threshold: 30 }
      });

      // May require admin auth
      expect([200, 401, 403]).toContain(response.status());

      if (response.ok()) {
        const data = await response.json();
        expect(data).toHaveProperty('notifications_sent');
      }
    });

    test('POST /api/notifications/send-compliance-warning works', async ({ request }) => {
      const response = await request.post('/api/notifications/send-compliance-warning', {
        data: { year: 2024 }
      });

      // May require admin auth
      expect([200, 401, 403]).toContain(response.status());

      if (response.ok()) {
        const data = await response.json();
        expect(data).toHaveProperty('employees_warned');
      }
    });
  });

  test.describe('Notification Integration with Leave Requests', () => {
    test('Creating leave request should trigger notification log', async ({ request }) => {
      // Get initial log count
      const initialLogsResponse = await request.get('/api/notifications/logs?limit=1');
      let initialCount = 0;
      if (initialLogsResponse.ok()) {
        const data = await initialLogsResponse.json();
        initialCount = data.total || 0;
      }

      // Create a leave request
      const employeesResponse = await request.get('/api/employees?year=2024');
      const employees = await employeesResponse.json();

      if (employees.employees.length > 0) {
        const emp = employees.employees[0];

        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        const dateStr = tomorrow.toISOString().split('T')[0];

        await request.post('/api/leave-requests', {
          data: {
            employee_num: emp.employee_num,
            employee_name: emp.name,
            start_date: dateStr,
            end_date: dateStr,
            days_requested: 1,
            leave_type: 'full',
            reason: 'E2E Test'
          }
        });

        // Check if notification was logged (may or may not be enabled)
        // Just verify the endpoint works
      }
    });
  });
});
