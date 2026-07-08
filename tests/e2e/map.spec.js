import { test, expect } from '@playwright/test';

test.describe('Map Visualization', () => {
  test('should load map on page load', async ({ page }) => {
    await page.goto('/');

    // Map container should exist
    const mapContainer = page.locator('#map');
    await expect(mapContainer).toBeVisible();
  });

  test('should support zoom controls', async ({ page }) => {
    await page.goto('/');

    // Wait for map to load
    await page.waitForTimeout(2000);

    // Get initial map center
    const mapBounds = await page.locator('#map').boundingBox();
    expect(mapBounds).toBeTruthy();

    // Simulate zoom in
    await page.keyboard.press('Plus');
    await page.waitForTimeout(500);

    // Map should still be visible
    const mapAfterZoom = page.locator('#map');
    await expect(mapAfterZoom).toBeVisible();
  });

  test('should show theme toggle button', async ({ page }) => {
    await page.goto('/');

    // Find theme toggle button
    const themeButton = page.locator('#themeToggle');
    await expect(themeButton).toBeVisible();
  });

  test('should toggle between dark and light theme', async ({ page }) => {
    await page.goto('/');

    // Get initial theme
    const initialTheme = await page.locator('body').getAttribute('data-theme');

    // Click theme toggle
    const themeButton = page.locator('#themeToggle');
    await themeButton.click();

    // Wait for theme change
    await page.waitForTimeout(300);

    // Theme should have changed
    const newTheme = await page.locator('body').getAttribute('data-theme');
    expect(newTheme).not.toBe(initialTheme);
  });

  test('should persist theme in localStorage', async ({ page }) => {
    await page.goto('/');

    // Click theme toggle
    await page.locator('#themeToggle').click();
    await page.waitForTimeout(300);

    // Get current theme
    const theme = await page.evaluate(() => localStorage.getItem('theme'));
    expect(theme).toMatch(/dark|light/);
  });
});
