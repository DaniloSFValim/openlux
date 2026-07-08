import { test, expect } from '@playwright/test';

async function dismissSplash(page) {
  const skip = page.locator('#splashSkip');
  if (await skip.isVisible()) await skip.click();
  await expect(page.locator('#splash')).toBeHidden({ timeout: 5000 });
}

test.describe('Authentication Flow', () => {
  test('should open login modal', async ({ page }) => {
    await page.goto('/');
    await dismissSplash(page);

    // Login é um modal aberto pelo botão "Entrar" da barra superior
    await page.locator('#btnLogin').click();
    await expect(page.locator('#loginModal')).toBeVisible();

    // Campos de e-mail e senha do modal
    await expect(page.locator('#liEmail')).toBeVisible();
    await expect(page.locator('#liPass')).toBeVisible();
  });

  test('should display error on invalid login', async ({ page }) => {
    await page.goto('/');
    await dismissSplash(page);

    await page.locator('#btnLogin').click();
    await page.locator('#liEmail').fill('nonexistent@test.com');
    await page.locator('#liPass').fill('wrongpassword');
    await page.locator('#liSubmit').click();

    // Mensagem de erro do modal (#liErr) deve aparecer
    await expect(page.locator('#liErr')).toBeVisible({ timeout: 10000 });
  });

  test('should logout successfully', async ({ page }) => {
    // This would require seeded test account
    // Placeholder for authenticated flow
    test.skip();
  });
});
