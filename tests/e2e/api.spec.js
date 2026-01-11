/**
 * E2E Tests: API Endpoints
 * Tests para verificar los endpoints del backend
 */
const { test, expect } = require('@playwright/test');

test.describe('API Endpoints', () => {

  test.describe('Employees API', () => {
    test('GET /api/employees should return employee list', async ({ request }) => {
      const response = await request.get('/api/employees?year=2024');

      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      expect(data).toHaveProperty('employees');
      expect(Array.isArray(data.employees)).toBeTruthy();
    });

    test('GET /api/employees with invalid year should handle gracefully', async ({ request }) => {
      const response = await request.get('/api/employees?year=1900');

      expect(response.ok()).toBeTruthy();
      const data = await response.json();
      expect(data.employees).toEqual([]);
    });

    test('PUT /api/employees should update employee', async ({ request }) => {
      // First get an employee
      const listResponse = await request.get('/api/employees?year=2024');
      const listData = await listResponse.json();

      if (listData.employees.length > 0) {
        const emp = listData.employees[0];

        const response = await request.put(`/api/employees/${emp.employee_num}/2024`, {
          data: { granted: emp.granted }
        });

        // May require auth, so just check it doesn't crash
        expect([200, 401, 403, 404]).toContain(response.status());
      }
    });
  });

  test.describe('Yukyu Usage API', () => {
    test('GET /api/yukyu/usage-details should return usage details', async ({ request }) => {
      const response = await request.get('/api/yukyu/usage-details?year=2024');

      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      expect(Array.isArray(data)).toBeTruthy();
    });

    test('GET /api/yukyu/monthly-summary should return monthly data', async ({ request }) => {
      const response = await request.get('/api/yukyu/monthly-summary/2024');

      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      expect(data).toBeDefined();
    });

    test('GET /api/yukyu/employee-summary should return employee summary', async ({ request }) => {
      // First get an employee
      const listResponse = await request.get('/api/employees?year=2024');
      const listData = await listResponse.json();

      if (listData.employees.length > 0) {
        const empNum = listData.employees[0].employee_num;
        const response = await request.get(`/api/yukyu/employee-summary/${empNum}/2024`);

        expect([200, 404]).toContain(response.status());
      }
    });
  });

  test.describe('Leave Requests API', () => {
    test('GET /api/leave-requests should return requests', async ({ request }) => {
      const response = await request.get('/api/leave-requests');

      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      expect(data).toHaveProperty('requests');
    });

    test('GET /api/leave-requests with status filter', async ({ request }) => {
      const response = await request.get('/api/leave-requests?status=PENDING');

      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      expect(Array.isArray(data.requests)).toBeTruthy();
    });
  });

  test.describe('Audit Log API', () => {
    test('GET /api/audit-log should return audit entries', async ({ request }) => {
      const response = await request.get('/api/audit-log');

      // May require auth
      expect([200, 401, 403]).toContain(response.status());

      if (response.ok()) {
        const data = await response.json();
        expect(data).toHaveProperty('entries');
      }
    });
  });

  test.describe('Project Status API', () => {
    test('GET /api/project-status should return status', async ({ request }) => {
      const response = await request.get('/api/project-status');

      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      expect(data).toHaveProperty('project');
      expect(data).toHaveProperty('database');
      expect(data).toHaveProperty('system');
    });
  });

  test.describe('Bulk Update API', () => {
    test('POST /api/employees/bulk-update/preview should return preview', async ({ request }) => {
      const listResponse = await request.get('/api/employees?year=2024');
      const listData = await listResponse.json();

      if (listData.employees.length >= 2) {
        const empNums = listData.employees.slice(0, 2).map(e => e.employee_num);

        const response = await request.post('/api/employees/bulk-update/preview', {
          data: {
            employee_nums: empNums,
            year: 2024,
            updates: { add_granted: 1 }
          }
        });

        expect([200, 401, 403]).toContain(response.status());
      }
    });
  });

  test.describe('Notifications API', () => {
    test('GET /api/notifications/settings should return settings', async ({ request }) => {
      const response = await request.get('/api/notifications/settings');

      // May require auth
      expect([200, 401, 403]).toContain(response.status());

      if (response.ok()) {
        const data = await response.json();
        expect(data).toHaveProperty('email_enabled');
        expect(data).toHaveProperty('slack_enabled');
      }
    });

    test('GET /api/notifications/logs should return logs', async ({ request }) => {
      const response = await request.get('/api/notifications/logs');

      expect([200, 401, 403]).toContain(response.status());
    });
  });

  test.describe('GitHub Integration API', () => {
    test('GET /api/github/status should return integration status', async ({ request }) => {
      const response = await request.get('/api/github/status');

      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      expect(data).toHaveProperty('configured');
    });
  });

  test.describe('Compliance API', () => {
    test('GET /api/compliance/5day-check should return compliance data', async ({ request }) => {
      const response = await request.get('/api/compliance/5day-check/2024');

      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      expect(data).toHaveProperty('year');
      expect(data).toHaveProperty('summary');
    });

    test('GET /api/expiring-soon should return expiring days', async ({ request }) => {
      const response = await request.get('/api/expiring-soon?year=2024');

      expect([200, 404]).toContain(response.status());
    });
  });

  test.describe('Backup API', () => {
    test('GET /api/backups should return backup list', async ({ request }) => {
      const response = await request.get('/api/backups');

      // May require auth
      expect([200, 401, 403]).toContain(response.status());

      if (response.ok()) {
        const data = await response.json();
        expect(data).toHaveProperty('backups');
      }
    });
  });
});
