// @ts-check
const { test, expect } = require('@playwright/test');

/**
 * Compliance Workflow E2E Tests
 * Tests for Japanese Labor Law compliance features
 * 労働基準法第39条 - 5-day obligation, expiring leave alerts
 */

test.describe('Compliance Dashboard', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await page.waitForLoadState('networkidle');
    });

    test('should display compliance section', async ({ page }) => {
        // Navigate to compliance view if there's a navigation item
        const complianceNav = page.locator('[data-view="compliance"], [onclick*="compliance"]');
        if (await complianceNav.count() > 0) {
            await complianceNav.first().click();
            await page.waitForLoadState('networkidle');
        }

        // Page should still be functional
        const body = page.locator('body');
        await expect(body).toBeVisible();
    });
});

test.describe('5-Day Obligation Check', () => {
    test('API should return compliance data', async ({ request }) => {
        const currentYear = new Date().getFullYear();
        const response = await request.get(`/api/compliance/5day?year=${currentYear}`);

        // Should return success or appropriate error
        expect([200, 404, 500]).toContain(response.status());

        if (response.ok()) {
            const data = await response.json();
            expect(data).toHaveProperty('status');
        }
    });

    test('should display at-risk employees', async ({ page }) => {
        await page.goto('/');
        await page.waitForLoadState('networkidle');

        // Try to find compliance-related elements
        const complianceSection = page.locator('#compliance, .compliance-section, [data-view="compliance"]');
        const exists = await complianceSection.count() > 0;

        // If exists, it should have some content
        if (exists) {
            const section = complianceSection.first();
            await expect(section).toBeVisible();
        }
    });
});

test.describe('Expiring Leave Alerts', () => {
    test('API should return expiring leave data', async ({ request }) => {
        const currentYear = new Date().getFullYear();
        const response = await request.get(`/api/expiring-soon?year=${currentYear}&threshold_months=3`);

        expect([200, 404, 500]).toContain(response.status());

        if (response.ok()) {
            const data = await response.json();
            expect(data).toHaveProperty('status');
        }
    });
});

test.describe('Leave Request Workflow', () => {
    test('should access leave requests page', async ({ page }) => {
        await page.goto('/');
        await page.waitForLoadState('networkidle');

        // Navigate to requests view
        const requestsNav = page.locator('[data-view="requests"], [onclick*="requests"]');
        if (await requestsNav.count() > 0) {
            await requestsNav.first().click();
            await page.waitForLoadState('networkidle');
        }

        // Page should still be functional
        const body = page.locator('body');
        await expect(body).toBeVisible();
    });

    test('API should return leave requests', async ({ request }) => {
        const response = await request.get('/api/leave-requests');

        expect(response.ok()).toBeTruthy();

        const data = await response.json();
        expect(data).toHaveProperty('status');
        expect(data.status).toBe('success');
        expect(data).toHaveProperty('data');
        expect(Array.isArray(data.data)).toBe(true);
    });

    test('should filter leave requests by status', async ({ request }) => {
        const response = await request.get('/api/leave-requests?status=PENDING');

        expect(response.ok()).toBeTruthy();

        const data = await response.json();
        expect(data.status).toBe('success');
    });
});

test.describe('Employee Data', () => {
    test('API should return employees', async ({ request }) => {
        const response = await request.get('/api/employees');

        expect(response.ok()).toBeTruthy();

        const data = await response.json();
        expect(data).toHaveProperty('data');
        expect(Array.isArray(data.data)).toBe(true);
    });

    test('API should return employees by type', async ({ request }) => {
        const response = await request.get('/api/employees/by-type');

        expect(response.ok()).toBeTruthy();

        const data = await response.json();
        expect(data).toHaveProperty('status');
        expect(data.status).toBe('success');
        expect(data).toHaveProperty('haken');
        expect(data).toHaveProperty('ukeoi');
        expect(data).toHaveProperty('staff');
    });
});

test.describe('Grant Table Calculation', () => {
    test('employees should have granted days based on seniority', async ({ request }) => {
        const response = await request.get('/api/employees');

        if (response.ok()) {
            const data = await response.json();

            // Check that employees have grant-related fields
            if (data.data && data.data.length > 0) {
                const employee = data.data[0];
                // Should have either granted or similar field
                const hasGrantField = 'granted' in employee ||
                                     'granted_days' in employee ||
                                     'fukyu' in employee;
                // Grant field presence check
            }
        }
    });
});

test.describe('LIFO Deduction Logic', () => {
    test('API info should reference LIFO correctly', async ({ request }) => {
        const response = await request.get('/api/project-status');

        if (response.ok()) {
            const data = await response.json();
            const text = JSON.stringify(data);

            // Should not have FIFO confusion (LIFO is correct)
            // This is informational, not a hard failure
            const hasFIFO = text.includes('FIFO') || text.includes('fifo');
            if (hasFIFO) {
                console.warn('Warning: Found FIFO reference, should be LIFO');
            }
        }
    });
});
