import { test, expect } from '@playwright/test';

async function dismissSplash(page) {
  const skip = page.locator('#splashSkip');
  if (await skip.isVisible()) await skip.click();
  await expect(page.locator('#splash')).toBeHidden({ timeout: 5000 });
}

test.describe('UI Interactions', () => {
  test('should show filter controls', async ({ page }) => {
    await page.goto('/');
    await dismissSplash(page);

    // Barra superior com os selects de filtro
    await expect(page.locator('#fBairro')).toBeVisible();
    await expect(page.locator('#fTipo')).toBeVisible();
    await expect(page.locator('#fEstado')).toBeVisible();
    await expect(page.locator('#fPot')).toBeVisible();
  });

  test('should change filter selection', async ({ page }) => {
    await page.goto('/');
    await dismissSplash(page);

    // Selecionar um estado no filtro deve manter a UI estável
    await page.locator('#fEstado').selectOption('led');
    await page.waitForTimeout(500);
    await expect(page.locator('#map')).toBeVisible();
  });

  test('should initialize map layers', async ({ page }) => {
    await page.goto('/');
    await dismissSplash(page);

    // Leaflet cria os panes de camadas dentro do container do mapa
    await expect(page.locator('#map .leaflet-pane').first()).toBeAttached();
    await expect(page.locator('#map .leaflet-tile-pane')).toBeAttached();
  });

  test('should maintain UI responsiveness', async ({ page }) => {
    await page.goto('/');
    await dismissSplash(page);

    // Simulate multiple rapid interactions
    const themeBtn = page.locator('#themeToggle');

    // Click multiple times
    for (let i = 0; i < 3; i++) {
      await themeBtn.click();
      await page.waitForTimeout(100);
    }

    // Page should still be responsive
    await expect(page.locator('body')).toBeVisible();
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
