import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test('should load login page', async ({ page }) => {
    await page.goto('/');

    // Should show login form initially
    const loginForm = page.locator('form');
    await expect(loginForm).toBeVisible();

    // Should have email input
    const emailInput = page.locator('input[type="email"]');
    await expect(emailInput).toBeVisible();
  });

  test('should display error on invalid login', async ({ page }) => {
    await page.goto('/');

    // Try login with non-existent account
    await page.locator('input[type="email"]').fill('nonexistent@test.com');
    await page.locator('input[type="password"]').fill('wrongpassword');
    await page.locator('button:has-text("Entrar")').click();

    // Should show error message
    await expect(page.locator('text=/erro|erro|invalid/i')).toBeVisible({ timeout: 5000 });
  });

  test('should logout successfully', async ({ page }) => {
    // This would require seeded test account
    // Placeholder for authenticated flow
    test.skip();
  });
});
