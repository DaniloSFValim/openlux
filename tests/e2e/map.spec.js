import { test, expect } from '@playwright/test';

async function dismissSplash(page) {
  const skip = page.locator('#splashSkip');
  if (await skip.isVisible()) await skip.click();
  await expect(page.locator('#splash')).toBeHidden({ timeout: 5000 });
}

test.describe('Map Visualization', () => {
  test('should load map on page load', async ({ page }) => {
    await page.goto('/');

    // Map container should exist
    const mapContainer = page.locator('#map');
    await expect(mapContainer).toBeVisible();
  });

  test('should support zoom controls', async ({ page }) => {
    await page.goto('/');
    await dismissSplash(page);

    // Leaflet renderiza os controles de zoom no canto do mapa
    const zoomIn = page.locator('.leaflet-control-zoom-in');
    await expect(zoomIn).toBeVisible();
    await zoomIn.click();
    await page.waitForTimeout(500);

    // Map should still be visible after zooming
    await expect(page.locator('#map')).toBeVisible();
  });

  test('should show theme toggle button', async ({ page }) => {
    await page.goto('/');

    // Find theme toggle button
    const themeButton = page.locator('#themeToggle');
    await expect(themeButton).toBeVisible();
  });

  test('should toggle between dark and light theme', async ({ page }) => {
    await page.goto('/');
    await dismissSplash(page);

    // Get initial theme
    const initialTheme = await page.locator('body').getAttribute('data-theme');
    expect(initialTheme).toMatch(/dark|light/);

    // Click theme toggle
    await page.locator('#themeToggle').click();
    await page.waitForTimeout(300);

    // Theme should have changed
    const newTheme = await page.locator('body').getAttribute('data-theme');
    expect(newTheme).not.toBe(initialTheme);
  });

  test('should persist theme in localStorage', async ({ page }) => {
    await page.goto('/');
    await dismissSplash(page);

    // Click theme toggle
    await page.locator('#themeToggle').click();
    await page.waitForTimeout(300);

    // Get current theme
    const theme = await page.evaluate(() => localStorage.getItem('theme'));
    expect(theme).toMatch(/dark|light/);
  });
});
