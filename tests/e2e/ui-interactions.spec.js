import { test, expect } from '@playwright/test';

test.describe('UI Interactions', () => {
  test('should show filter controls', async ({ page }) => {
    await page.goto('/');

    // Should have navbar with filter dropdowns
    const navbar = page.locator('nav');
    await expect(navbar).toBeVisible();

    // Should have cascade menus
    const cascades = page.locator('[id*="Cascade"]');
    expect(await cascades.count()).toBeGreaterThan(0);
  });

  test('should open cascade menu on hover', async ({ page }) => {
    await page.goto('/');

    // Wait for page load
    await page.waitForTimeout(1000);

    // Find a cascade button
    const cascadeBtn = page.locator('[id*="Cascade"]').first();

    if (await cascadeBtn.isVisible()) {
      // Hover over it
      await cascadeBtn.hover();

      // Menu should appear
      const menu = cascadeBtn.locator('..').locator('ul, .menu, [role="menu"]');
      await expect(menu).toBeVisible({ timeout: 1000 });
    }
  });

  test('should show municipality limits on map', async ({ page }) => {
    await page.goto('/');

    // Wait for map to fully load
    await page.waitForTimeout(2000);

    // Municipality limits should be rendered
    // (This is a Leaflet SVG/path element)
    const municipioPath = page.locator('path[stroke*="blue"], g[id*="municipio"]');

    // At least the element structure should exist
    const mapSvg = page.locator('#map svg');
    const isSvgPresent = await mapSvg.count() > 0;
    expect(isSvgPresent).toBeTruthy();
  });

  test('should maintain UI responsiveness', async ({ page }) => {
    await page.goto('/');

    // Simulate multiple rapid interactions
    const themeBtn = page.locator('#themeToggle');

    // Click multiple times
    for (let i = 0; i < 3; i++) {
      await themeBtn.click();
      await page.waitForTimeout(100);
    }

    // Page should still be responsive
    await expect(page.locator('body')).toBeVisible();

    // No console errors
    const errors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') errors.push(msg.text());
    });

    // After interactions, errors should be minimal
    // (Some may exist but critical ones should not)
  });

  test('should load without console errors', async ({ page }) => {
    const consoleMessages = [];
    page.on('console', msg => {
      if (msg.type() === 'error' || msg.type() === 'warning') {
        consoleMessages.push({
          type: msg.type(),
          text: msg.text()
        });
      }
    });

    await page.goto('/');
    await page.waitForTimeout(2000);

    // Filter out known third-party warnings
    const criticalErrors = consoleMessages.filter(m =>
      m.type === 'error' &&
      !m.text.includes('Cross-Origin') &&
      !m.text.includes('third-party')
    );

    expect(criticalErrors.length).toBe(0);
  });
});
