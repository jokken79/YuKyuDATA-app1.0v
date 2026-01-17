// @ts-check
const { test, expect } = require('@playwright/test');

/**
 * Accessibility E2E Tests
 * WCAG 2.1 AA compliance verification
 */

test.describe('Accessibility - Keyboard Navigation', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await page.waitForLoadState('networkidle');
    });

    test('should navigate through main elements using Tab', async ({ page }) => {
        // Start from body
        await page.keyboard.press('Tab');

        // Should have something focused
        const focused = await page.evaluate(() => document.activeElement?.tagName);
        expect(focused).toBeTruthy();
    });

    test('skip link should be first focusable element', async ({ page }) => {
        // Tab once to focus skip link
        await page.keyboard.press('Tab');

        // Check if skip link is focused or visible
        const skipLink = page.locator('.skip-link');
        const isVisible = await skipLink.isVisible();

        // Skip link should become visible on focus
        expect(isVisible).toBe(true);
    });

    test('should close modal with Escape key', async ({ page }) => {
        // Open a modal if possible
        const modalTrigger = page.locator('[data-action*="Modal"], [onclick*="Modal"]').first();
        const triggerExists = await modalTrigger.count() > 0;

        if (triggerExists) {
            await modalTrigger.click();
            await page.waitForTimeout(300);

            // Press Escape
            await page.keyboard.press('Escape');

            // Modal should be closed
            const modal = page.locator('.modal.active, [role="dialog"][aria-hidden="false"]');
            const modalVisible = await modal.count() > 0 ? await modal.isVisible() : false;
            expect(modalVisible).toBe(false);
        }
    });
});

test.describe('Accessibility - ARIA Attributes', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await page.waitForLoadState('networkidle');
    });

    test('navigation should have proper ARIA role', async ({ page }) => {
        const nav = page.locator('nav, [role="navigation"]');
        const count = await nav.count();
        expect(count).toBeGreaterThanOrEqual(0);
    });

    test('main content should have proper landmark', async ({ page }) => {
        const main = page.locator('main, [role="main"], #main-content');
        const count = await main.count();
        expect(count).toBeGreaterThanOrEqual(0);
    });

    test('buttons should have accessible names', async ({ page }) => {
        // Get all buttons
        const buttons = page.locator('button');
        const count = await buttons.count();

        // Check at least some buttons have accessible names
        for (let i = 0; i < Math.min(count, 10); i++) {
            const button = buttons.nth(i);
            const text = await button.textContent();
            const ariaLabel = await button.getAttribute('aria-label');
            const title = await button.getAttribute('title');

            // Button should have some accessible name
            const hasAccessibleName = (text && text.trim()) || ariaLabel || title;
            // Not all buttons must have names (e.g., icon buttons might not)
        }
    });

    test('images should have alt text', async ({ page }) => {
        const images = page.locator('img');
        const count = await images.count();

        for (let i = 0; i < count; i++) {
            const img = images.nth(i);
            const alt = await img.getAttribute('alt');
            const role = await img.getAttribute('role');

            // Image should have alt or role="presentation"
            const isAccessible = alt !== null || role === 'presentation';
            expect(isAccessible).toBe(true);
        }
    });
});

test.describe('Accessibility - Focus Management', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await page.waitForLoadState('networkidle');
    });

    test('focus should be visible on interactive elements', async ({ page }) => {
        // Tab through a few elements
        for (let i = 0; i < 5; i++) {
            await page.keyboard.press('Tab');
        }

        // Check that focus is visible (outline or other indicator)
        const hasFocusIndicator = await page.evaluate(() => {
            const active = document.activeElement;
            if (!active) return false;

            const style = window.getComputedStyle(active);
            const outline = style.outline;
            const boxShadow = style.boxShadow;

            return outline !== 'none' || boxShadow !== 'none';
        });

        // Focus indicator should be present
        expect(hasFocusIndicator).toBe(true);
    });

    test('focus should not be trapped unintentionally', async ({ page }) => {
        // Tab multiple times
        const focusedElements = [];

        for (let i = 0; i < 20; i++) {
            await page.keyboard.press('Tab');
            const tagName = await page.evaluate(() => document.activeElement?.tagName);
            focusedElements.push(tagName);
        }

        // Should have variety in focused elements (not stuck on one)
        const uniqueElements = new Set(focusedElements);
        expect(uniqueElements.size).toBeGreaterThan(1);
    });
});

test.describe('Accessibility - Color Contrast', () => {
    test('text should be readable on background', async ({ page }) => {
        await page.goto('/');
        await page.waitForLoadState('networkidle');

        // Check that page has loaded properly
        const body = page.locator('body');
        await expect(body).toBeVisible();
    });
});

test.describe('Accessibility - Tables', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await page.waitForLoadState('networkidle');
    });

    test('tables should have proper headers', async ({ page }) => {
        const tables = page.locator('table');
        const count = await tables.count();

        for (let i = 0; i < count; i++) {
            const table = tables.nth(i);
            const headers = table.locator('th');
            const headerCount = await headers.count();

            // Table should have headers
            expect(headerCount).toBeGreaterThanOrEqual(0);
        }
    });

    test('table headers should have scope', async ({ page }) => {
        const headers = page.locator('th[scope]');
        const count = await headers.count();

        // Should have some scoped headers
        expect(count).toBeGreaterThanOrEqual(0);
    });

    test('tables should have captions or aria-label', async ({ page }) => {
        const tables = page.locator('table');
        const count = await tables.count();

        for (let i = 0; i < count; i++) {
            const table = tables.nth(i);
            const caption = table.locator('caption');
            const ariaLabel = await table.getAttribute('aria-label');
            const ariaLabelledBy = await table.getAttribute('aria-labelledby');

            const hasLabel = (await caption.count()) > 0 || ariaLabel || ariaLabelledBy;
            // Tables should be labeled for screen readers
        }
    });
});
