# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: ui-interactions.spec.js >> UI Interactions >> should show filter controls
- Location: tests/e2e/ui-interactions.spec.js:10:7

# Error details

```
Error: expect(locator).toBeHidden() failed

Locator:  locator('#splash')
Expected: hidden
Received: visible
Timeout:  5000ms

Call log:
  - Expect "toBeHidden" with timeout 5000ms
  - waiting for locator('#splash')
    14 × locator resolved to <div id="splash">…</div>
       - unexpected value "visible"

```

```yaml
- text: Iluminação Pública · Niterói SECONSER · Diretoria de Iluminação Pública Desenvolvido por Danilo Valim v1.1
- button "Entrar"
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | async function dismissSplash(page) {
  4  |   const skip = page.locator('#splashSkip');
  5  |   if (await skip.isVisible()) await skip.click();
> 6  |   await expect(page.locator('#splash')).toBeHidden({ timeout: 5000 });
     |                                         ^ Error: expect(locator).toBeHidden() failed
  7  | }
  8  | 
  9  | test.describe('UI Interactions', () => {
  10 |   test('should show filter controls', async ({ page }) => {
  11 |     await page.goto('/');
  12 |     await dismissSplash(page);
  13 | 
  14 |     // Barra superior com os selects de filtro
  15 |     await expect(page.locator('#fBairro')).toBeVisible();
  16 |     await expect(page.locator('#fTipo')).toBeVisible();
  17 |     await expect(page.locator('#fEstado')).toBeVisible();
  18 |     await expect(page.locator('#fPot')).toBeVisible();
  19 |   });
  20 | 
  21 |   test('should change filter selection', async ({ page }) => {
  22 |     await page.goto('/');
  23 |     await dismissSplash(page);
  24 | 
  25 |     // Selecionar um estado no filtro deve manter a UI estável
  26 |     await page.locator('#fEstado').selectOption('led');
  27 |     await page.waitForTimeout(500);
  28 |     await expect(page.locator('#map')).toBeVisible();
  29 |   });
  30 | 
  31 |   test('should initialize map layers', async ({ page }) => {
  32 |     await page.goto('/');
  33 |     await dismissSplash(page);
  34 | 
  35 |     // Leaflet cria os panes de camadas dentro do container do mapa
  36 |     await expect(page.locator('#map .leaflet-pane').first()).toBeAttached();
  37 |     await expect(page.locator('#map .leaflet-tile-pane')).toBeAttached();
  38 |   });
  39 | 
  40 |   test('should maintain UI responsiveness', async ({ page }) => {
  41 |     await page.goto('/');
  42 |     await dismissSplash(page);
  43 | 
  44 |     // Simulate multiple rapid interactions
  45 |     const themeBtn = page.locator('#themeToggle');
  46 | 
  47 |     // Click multiple times
  48 |     for (let i = 0; i < 3; i++) {
  49 |       await themeBtn.click();
  50 |       await page.waitForTimeout(100);
  51 |     }
  52 | 
  53 |     // Page should still be responsive
  54 |     await expect(page.locator('body')).toBeVisible();
  55 |   });
  56 | 
  57 |   test('should load without console errors', async ({ page }) => {
  58 |     const consoleMessages = [];
  59 |     page.on('console', msg => {
  60 |       if (msg.type() === 'error' || msg.type() === 'warning') {
  61 |         consoleMessages.push({
  62 |           type: msg.type(),
  63 |           text: msg.text()
  64 |         });
  65 |       }
  66 |     });
  67 | 
  68 |     await page.goto('/');
  69 |     await page.waitForTimeout(2000);
  70 | 
  71 |     // Filter out known third-party warnings
  72 |     const criticalErrors = consoleMessages.filter(m =>
  73 |       m.type === 'error' &&
  74 |       !m.text.includes('Cross-Origin') &&
  75 |       !m.text.includes('third-party')
  76 |     );
  77 | 
  78 |     expect(criticalErrors.length).toBe(0);
  79 |   });
  80 | });
  81 | 
```