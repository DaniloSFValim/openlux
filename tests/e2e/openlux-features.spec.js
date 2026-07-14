import { test, expect } from '@playwright/test';

// Cobertura das features pós-auditoria: seleção por polígono, fotometria de
// instalação (Tier 3), configuração de cidade (Fase 1) e recenseamento (Fase 2).

async function dismissSplash(page) {
  const skip = page.locator('#splashSkip');
  if (await skip.isVisible()) await skip.click();
  await expect(page.locator('#splash')).toBeHidden({ timeout: 5000 });
}

async function waitApp(page) {
  await page.goto('/');
  await dismissSplash(page);
  await page.waitForFunction(() => typeof dentroDaCidade === 'function' && typeof fotometriaIndices === 'function');
}

test.describe('Fase 1 — Cidade como configuração (CITY)', () => {
  test('CITY carregada e dentroDaCidade correta (dentro/fora/NaN)', async ({ page }) => {
    await waitApp(page);
    const r = await page.evaluate(() => ({
      slug: CITY.slug,
      dentro: dentroDaCidade(-22.9, -43.1),
      foraRio: dentroDaCidade(-22.95, -43.35),
      nanSeguro: dentroDaCidade(NaN, -43.1)
    }));
    expect(r.slug).toBe('niteroi');
    expect(r.dentro).toBe(true);
    expect(r.foraRio).toBe(false);
    expect(r.nanSeguro).toBe(false);
  });
});

test.describe('Tier 3 — Fotometria de instalação', () => {
  test('índices corretos nos casos canônicos do modelo', async ({ page }) => {
    await waitApp(page);
    const r = await page.evaluate(() => {
      const nadir = fotometriaIndices(0, 'concreto');
      const horiz = fotometriaIndices(90, 'concreto');
      const incompleto = fotometriaIndices(45, '');
      return {
        nadirEta: Math.round(nadir.etaPiso * 100) / 100,
        nadirP: Math.round(nadir.P * 100) / 100,
        horizP: Math.round(horiz.P * 100) / 100,
        incompleto,
        nAngulos: ANGULOS_INCLINACAO.length,
        nMateriais: MATERIAIS_PISO.length
      };
    });
    expect(r.nadirEta).toBe(1);       // η = cos(0°) = 1
    expect(r.nadirP).toBe(0.15);      // P = ρ·η·0,5 = 0,30·1·0,5
    expect(r.horizP).toBe(1);         // horizontal: tudo vira poluição
    expect(r.incompleto).toBeNull();  // sem material → sem índice
    expect(r.nAngulos).toBe(8);
    expect(r.nMateriais).toBe(8);
  });

  test('painel de detalhe alterna herdado vs verificado', async ({ page }) => {
    await waitApp(page);
    const r = await page.evaluate(() => {
      openDetail({ id: 't1', tipo_ativo: 'luminaria', tipo_lampada: 'led', modernizado_led: true, verificado_em: null });
      const herdado = document.getElementById('detail').innerHTML.includes('herdado — não verificado');
      openDetail({ id: 't2', tipo_ativo: 'luminaria', tipo_lampada: 'led', modernizado_led: true, verificado_em: '2026-07-11T12:00:00Z' });
      const verificado = document.getElementById('detail').innerHTML.includes('verificado em');
      return { herdado, verificado };
    });
    expect(r.herdado).toBe(true);
    expect(r.verificado).toBe(true);
  });
});

test.describe('Seleção por polígono (Área)', () => {
  test('botão Área é público e ativa/cancela o modo desenho', async ({ page }) => {
    await waitApp(page);
    await expect(page.locator('#btnArea')).toBeVisible();

    await page.locator('#btnArea').click();
    await expect(page.locator('#drawCtl')).toBeVisible();

    await page.locator('#drawCancel').click();
    await expect(page.locator('#drawCtl')).toBeHidden();
  });

  test('Concluir com menos de 3 vértices avisa e não fecha o desenho', async ({ page }) => {
    await waitApp(page);
    await page.locator('#btnArea').click();
    await page.locator('#drawDone').click();
    await expect(page.locator('#toast')).toContainText('3 vértices');
    await expect(page.locator('#drawCtl')).toBeVisible();
    await page.locator('#drawCancel').click();
  });

  test('desenhar polígono retorna estatísticas da área (RPC real)', async ({ page }) => {
    await waitApp(page);
    await page.locator('#btnArea').click();

    // 3 cliques sobre Niterói (o mapa abre centrado em CITY.centro)
    const box = await page.locator('#map').boundingBox();
    const cx = box.x + box.width / 2, cy = box.y + box.height / 2;
    await page.mouse.click(cx - 60, cy - 60);
    await page.mouse.click(cx + 60, cy - 60);
    await page.mouse.click(cx, cy + 60);
    await expect(page.locator('#drawCount')).toContainText('3 vértices');

    await page.locator('#drawDone').click();
    const panel = page.locator('#poligonoPanel');
    await expect(panel).toBeVisible({ timeout: 15000 });
    await expect(panel).toContainText('Área selecionada');
    await expect(panel).toContainText('Densidade');

    // Limpar restaura o mapa normal
    await panel.getByText('✕ Limpar').click();
    await expect(panel).toBeHidden();
  });
});

test.describe('Fase 2 — Recenseamento', () => {
  test('filtro "não verificados" existe e mapeia para o RPC', async ({ page }) => {
    await waitApp(page);
    await expect(page.locator('#fFila option[value="nao_verificado"]')).toHaveCount(1);
    const r = await page.evaluate(() => {
      state.fila = 'nao_verificado';
      const on = filtros().p_nao_verificado;
      state.fila = '';
      const off = filtros().p_nao_verificado;
      return { on, off };
    });
    expect(r.on).toBe(true);
    expect(r.off).toBeNull();
  });

  test('aba Campanhas existe no Admin e ip_listar_campanhas responde (RPC real, leitura pública)', async ({ page }) => {
    await waitApp(page);
    await expect(page.locator('[data-sec="campanhas"]')).toHaveCount(1);
    await expect(page.locator('#campBox')).toHaveCount(1);
    const campanhas = await page.evaluate(async () => {
      const { data, error } = await sb.rpc('ip_listar_campanhas');
      return { ok: !error, isArray: Array.isArray(data) };
    });
    expect(campanhas.ok).toBe(true);
    expect(campanhas.isArray).toBe(true);
  });

  test('escrita de campanha é bloqueada para anônimo (grants)', async ({ page }) => {
    await waitApp(page);
    const r = await page.evaluate(async () => {
      const { data, error } = await sb.rpc('ip_criar_campanha', { p_nome: 'nao-deve-criar' });
      // anon não tem EXECUTE (erro de permissão) — e mesmo que resolvesse,
      // a função exigiria papel admin (data.error)
      return { blocked: !!error || !!(data && data.error) };
    });
    expect(r.blocked).toBe(true);
  });
});
