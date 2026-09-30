// Playwright Configuration - E2E Testing
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false, // Sequential to avoid conflicts
  forbidOnly: !!process.env.CI,
  // 2 retries triplicam o tempo de todo teste que falha. Com 44 blocos x 2
  // navegadores e um unico worker, isso estourava o orcamento do job. 1 retry
  // ainda distingue flake de falha real pela metade do custo.
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 1 : 1,
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/junit.xml' }],
    ['list']
  ],
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:8000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  webServer: {
    command: 'npx http-server -p 8000 -c-1',
    url: 'http://localhost:8000',
    reuseExistingServer: true,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
  ],
  // Este valor precisa ficar abaixo do timeout-minutes do job em e2e-tests.yml
  // (30). Quando os dois eram iguais a 30, o runner matava o job no exato
  // instante em que o Playwright desistiria, entao ele nunca chegava a escrever
  // o relatorio: o resultado aparecia como "cancelled", sem uma linha dizendo
  // qual teste falhou. 20 minutos deixam 10 de folga para relatorio e upload.
  globalTimeout: 20 * 60 * 1000,
  timeout: 30 * 1000,
});
