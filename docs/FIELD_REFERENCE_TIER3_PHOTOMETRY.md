<div align="center">

# 📐 Tier 3 · Fotometria de Instalação

### Ângulo de apontamento · Material do piso · Índices de aproveitamento e poluição luminosa

*Referência técnica e modelo de cálculo para índices fotométricos de instalação*

</div>

---

## 1. Motivação

O inventário registra, para cada luminária, **o que** está instalado (potência, tipo de
lâmpada, fotometria do modelo — Tier 2). Isso **não** é suficiente para estimar o
desempenho luminotécnico *no local*: duas luminárias idênticas produzem iluminância,
percepção visual e poluição luminosa completamente diferentes conforme **como** e **onde**
estão instaladas.

Dois parâmetros de instalação, de baixo custo de coleta e alto poder explicativo,
capturam a maior parte dessa variância:

| Fase | Campo | O que é | Por que importa |
|:---:|---|---|---|
| **1** | `angulo_inclinacao_graus` | Ângulo de apontamento do facho | Governa quanto do fluxo incide útil no piso vs. escapa para o céu/lateral |
| **2** | `material_piso` | Material predominante da superfície | Define a refletância ρ → percepção visual e luz refletida de volta ao céu |

Ambos são coletados por **opções pré-classificadas** (sem digitação livre), garantindo
integridade e comparabilidade estatística — condição necessária para uso científico.

> **Escopo desta entrega:** captura dos dados + um **índice de primeira ordem** (proxy
> geométrico) exibido na interface. O cálculo radiométrico rigoroso (curva .IES + espalhamento
> atmosférico por partículas / PM2.5) é a **Fase 3**, tratada na seção [§7](#7-limitações-e-caminho-para-a-fase-3).

---

## 2. Fase 1 — Ângulo de apontamento

### 2.1 Convenção

O ângulo **θ** é medido a partir da **vertical descendente (nadir)** — a direção que aponta
diretamente para o solo:

```
        ☁  céu
         ↑  (uplight, θ > 90°)
         |
  θ=90° ─┼───────►  horizontal
         |╲
         | ╲ θ  (ângulo de apontamento)
         |  ╲
         |   ▼
      ───┴────  solo      θ = 0°  → facho reto para baixo (full-cutoff)
```

| θ (nadir) | Situação | Relação com o solo | Qualidade |
|:---:|---|---|:---:|
| **0°** | Facho reto para baixo (*full-cutoff*) | perpendicular ao solo | 🟢 ideal |
| 15°–30° | Leve inclinação | quase perpendicular | 🟢 boa |
| 45° | Inclinação média | 45° do solo | 🟡 moderada |
| 60°–75° | Inclinação acentuada / rasante | próximo do rasante | 🟠 ruim |
| **90°** | Facho horizontal | paralelo ao solo | 🔴 péssima |
| **120°** | *Uplight* (acima da horizontal) | apontando para cima (holofote) | 🔴 crítica |

> **Nota de nomenclatura.** No campo, a orientação é frequentemente descrita “em relação ao
> solo” (0° = paralelo ao solo). Adotamos a convenção **a partir do nadir** por ser o padrão
> da engenharia de iluminação (*aiming/tilt angle*) e por produzir fórmulas monotônicas
> limpas. As etiquetas da interface trazem as duas leituras para evitar ambiguidade.

### 2.2 Opções pré-classificadas

`{ 0, 15, 30, 45, 60, 75, 90, 120 }` graus — validadas por `CHECK` no banco.

---

## 3. Fase 2 — Material do piso e refletância (ρ)

A superfície sob a luminária reflete parte do fluxo incidente. A fração refletida difusa
média (albedo, ρ) determina **a luminância percebida** (o que o olho enxerga) e a
**parcela de luz devolvida ao hemisfério superior** (poluição refletida).

### 3.1 Tabela de refletância (`ref_material_piso`)

| Chave | Rótulo | ρ | Fonte |
|---|---|:---:|---|
| `asfalto_novo` | Asfalto novo (escuro) | **0,07** | CIE 144 / ABNT NBR 5101 |
| `asfalto_desgastado` | Asfalto desgastado (claro) | **0,12** | CIE 144 |
| `concreto` | Concreto / cimento | **0,30** | CIE 144 / IESNA |
| `paralelepipedo` | Paralelepípedo / pedra | **0,18** | CIE 144 |
| `terra` | Terra batida | **0,20** | CIE 30.2 |
| `vegetacao` | Vegetação / grama | **0,08** | CIE 30.2 |
| `areia` | Areia | **0,25** | CIE 30.2 |
| `agua` | Água (espelho d'água) | **0,06**¹ | CIE 30.2 |

> ¹ **Água** tem ρ difuso baixo, porém comportamento **especular** intenso em ângulos
> rasantes (reflexão de Fresnel) — fonte relevante de ofuscamento. O modelo difuso de
> primeira ordem **subestima** a poluição sobre lâminas d'água; sinalizado como limitação.

Os valores vivem em uma **tabela de referência versionada no banco** (`ref_material_piso`,
leitura pública), permitindo auditoria e replicação da análise via SQL puro.

---

## 4. Modelo de cálculo (proxy de primeira ordem)

### 4.1 Premissas declaradas

1. **Aproximação de eixo central**: o facho é tratado pela direção do seu eixo óptico
   (feixe estreito). A largura real do facho é ignorada nesta ordem.
2. **Reflexão Lambertiana (difusa)** do piso; metade da luz refletida (f_up = 0,5) retorna
   ao hemisfério superior.
3. **Plano de trabalho horizontal** ao nível do solo.
4. Componente especular, obstruções (copa de árvores, postes) e a curva fotométrica real
   (.IES) **não** entram nesta ordem — ver [§7](#7-limitações-e-caminho-para-a-fase-3).

Estas premissas são deliberadamente simples e **explícitas**: o objetivo é um *indicador
comparável entre pontos*, não uma simulação radiométrica.

### 4.2 Fórmulas

Seja **θ** o ângulo de apontamento (nadir, em graus) e **ρ** a refletância do material.

**(a) Aproveitamento geométrico no piso** — fração do fluxo cujo eixo incide útil no plano
horizontal:

$$\eta_{piso} = \max\!\big(0,\; \cos\theta\big)$$

**(b) Luminância relativa da superfície** — proporcional ao que o olho percebe (explica por
que asfalto escuro “pede” mais lúmens que concreto para a mesma sensação de claridade):

$$L_{rel} = \eta_{piso}\cdot\rho$$

**(c) Índice de poluição luminosa (proxy, 0–1)** — soma da luz que **não** incide no piso
(perdida para lateral/céu como ofuscamento e *skyglow* direto) com a parcela **refletida**
de volta ao céu:

$$P = \min\!\Big(1,\; \underbrace{(1-\eta_{piso})}_{\text{direta perdida}} + \underbrace{\rho\cdot\eta_{piso}\cdot f_{up}}_{\text{refletida}}\Big),\qquad f_{up}=0{,}5$$

### 4.3 Comportamento

| θ | Material | η_piso | P | L_rel | Leitura |
|:---:|---|:---:|:---:|:---:|---|
| 0° | Asfalto novo | 1,00 | **0,035** | 0,07 | Ótimo aproveitamento, pouca poluição; superfície escura |
| 0° | Concreto | 1,00 | 0,150 | 0,30 | Ótimo aproveitamento; mais luz refletida ao céu |
| 45° | Asfalto novo | 0,71 | 0,318 | 0,05 | Perde ~30% para lateral/céu |
| 90° | Concreto | 0,00 | **1,000** | 0,00 | Facho horizontal: nada no piso, tudo poluição |
| 120° | Concreto | 0,00 | **1,000** | 0,00 | *Uplight*: máxima poluição |

Propriedades desejáveis: **P cresce monotonicamente** conforme o facho se afasta do nadir,
e **cresce com ρ** (materiais claros devolvem mais luz ao céu) — reproduzindo a física
qualitativa que o modelo se propõe a capturar.

---

## 5. Interpretação e enquadramento normativo

- **η_piso** dialoga com a *utilância* / fator de utilização da **ABNT NBR 5101** (iluminação
  pública viária) e com o *Coefficient of Utilization* (IESNA).
- **P** é um proxy do **Upward Light Ratio (ULR)** da **CIE 150:2017** (*Guide on the
  Limitation of the Effects of Obtrusive Light*) e conversa com o eixo **U** (*Uplight*) do
  sistema de classificação **BUG** (*Backlight–Uplight–Glare*, IESNA TM-15).
- A distinção **η_piso × L_rel** materializa o achado central: **material escuro (asfalto)
  exige maior potência** para atingir a mesma luminância de projeto — insumo direto para
  dimensionamento e para a política de modernização LED.

---

## 6. Esquema de dados

### 6.1 Colunas (`pontos_luminaria`)

| Coluna | Tipo | Restrição | Observação |
|---|---|---|---|
| `angulo_inclinacao_graus` | `smallint` | `CHECK IN (0,15,30,45,60,75,90,120)` | *nullable* (retrocompatível) |
| `material_piso` | `text` | `FK → ref_material_piso(material)` | *nullable* |

Ambas as colunas são **opcionais**: os ~42.763 pontos legados permanecem válidos com valor
`NULL` (“não classificado”), e os índices só são exibidos quando **ambos** estão preenchidos.

### 6.2 RPCs

`ip_inserir_ponto` e `ip_atualizar_ponto` receberam dois parâmetros ao final da assinatura,
com `DEFAULT NULL` (sem criar *overloads* — assinatura única por função):

```
p_angulo   integer  DEFAULT NULL   -- graus (nadir)
p_material text     DEFAULT NULL   -- chave de ref_material_piso
```

Leitura exposta em `v_parque_export` e `ip_pontos_bbox` (mesmas assinaturas; *grants*
preservados). Escrita restrita a `authenticated` (editor/admin) — `anon` mantém apenas
leitura, conforme o *hardening* vigente.

### 6.3 Reprodutibilidade (SQL puro)

```sql
-- Distribuição de qualidade de instalação do parque classificado
SELECT
  material_piso,
  angulo_inclinacao_graus,
  count(*)                                             AS pontos,
  round(avg(greatest(0, cosd(angulo_inclinacao_graus)))::numeric, 3) AS eta_piso_medio
FROM pontos_luminaria p
JOIN ref_material_piso r USING (material_piso)          -- garante ρ conhecido
WHERE angulo_inclinacao_graus IS NOT NULL
GROUP BY 1, 2
ORDER BY eta_piso_medio;
```

### 6.4 Exemplo Prático com Coordenadas Reais

**Local:** Rua Quinze de Novembro, Centro de Niterói — Poste ID `c8f4a92c-1234-5678-abcd-ef0123456789`

**Dados brutos (coletados em campo ou do modelo):**

| Campo | Valor | Unidade |
|-------|-------|--------|
| Latitude | -22.8850 | ° |
| Longitude | -43.1050 | ° |
| Potência | 150 | W |
| Tipo lâmpada | LED | — |
| **Ângulo de apontamento (θ)** | **30°** | graus (nadir) |
| **Material do piso (ρ)** | **0,12** | asfalto desgastado |

**Cálculo dos índices de primeira ordem:**

1. **Aproveitamento no piso (η):**
   ```
   η = max(0, cos θ)
     = max(0, cos 30°)
     = max(0, 0,866)
     = 0,866  ← 86,6% do fluxo vai para o piso
   ```

2. **Poluição luminosa (P):**
   ```
   P = (1 − η) + ρ·η·0,5
     = (1 − 0,866) + 0,12 × 0,866 × 0,5
     = 0,134 + 0,052
     = 0,186  ← 18,6% do fluxo escapa ao céu (direto + refletido)
   ```

3. **Luminância relativa (L):**
   ```
   L = η · ρ
     = 0,866 × 0,12
     = 0,104  ← fração percebida pelo olho
   ```

**Interpretação:**
- ✅ **Η = 0,866** (excelente) — facho bem dirigido ao piso (θ = 30°)
- ⚠️ **P = 0,186** (aceitável) — poluição luminosa controlada, mas asfalto desgastado (ρ = 0,12 é baixo) contribui para pouco reflexo útil
- 📊 **L = 0,104** — luminância percebida é moderada; asfalto novo (ρ = 0,07) resultaria em L = 0,061 (mais escuro)

**Comparação com instalações ruins:**

| Cenário | θ | ρ | η | P | L | Qualidade |
|---------|---|---|---|---|---|-----------|
| Exemplo acima (bom) | 30° | 0,12 | 0,866 | 0,186 | 0,104 | 🟢 boa |
| Apontamento alto | 60° | 0,12 | 0,500 | 0,530 | 0,060 | 🟡 ruim (muita poluição) |
| Uplight | 120° | 0,12 | −0,500 → 0 | >0,5 | 0 | 🔴 crítica |

**Expressão no JSON de exportação (CSV/GeoJSON):**

```json
{
  "id": "c8f4a92c-1234-5678-abcd-ef0123456789",
  "codigo": "LM-00123",
  "latitude": -22.8850,
  "longitude": -43.1050,
  "potencia": 150,
  "tipo_lampada": "led",
  "angulo_inclinacao_graus": 30,
  "material_piso": "asfalto_desgastado",
  "indices_fotometricos": {
    "aproveitamento_piso": 0.866,
    "poluicao_luminosa": 0.186,
    "luminancia_relativa": 0.104
  },
  "bairro": "Centro",
  "status": "ok"
}
```

**Simulação interativa:**

Estes cálculos estão implementados em tempo real no painel de detalhes (`index.html`, função `fotometriaIndices()`). Alterar θ ou material no formulário de edição recalcula os índices instantaneamente.

---

## 7. Limitações e caminho para a Fase 3

O modelo é um **proxy geométrico de primeira ordem**, honesto quanto às suas premissas
([§4.1](#41-premissas-declaradas)). Não substitui simulação radiométrica. Evoluções previstas:

| Limitação atual | Evolução (Fase 3) |
|---|---|
| Eixo central (feixe estreito) | Integração da **curva fotométrica .IES** (Tier 2 já armazena o arquivo) |
| Reflexão puramente difusa | Modelo **especular** (Fresnel) para água/superfícies molhadas |
| Atmosfera transparente | **Espalhamento de Mie** por partículas dispersas (**PM2.5**), via série histórica de qualidade do ar (INEA) — corrige eficácia útil e amplifica o *skyglow* |
| Índice adimensional | Calibração para **iluminância absoluta (lux)** e ULR conforme CIE 150 |

A arquitetura já está preparada: `ref_material_piso` é extensível, as colunas são
*nullable*, e os índices são recalculados no cliente — nenhum dado histórico precisa ser
reprocessado ao evoluir o modelo.

---

## 8. Referências

- **ABNT NBR 5101:2024** — *Iluminação pública — Procedimento.*
- **CIE 144:2001** — *Road surface and road marking reflection characteristics.*
- **CIE 30.2:1982** — *Calculation and measurement of luminance and illuminance in road lighting.*
- **CIE 150:2017** — *Guide on the limitation of the effects of obtrusive light from outdoor lighting installations.*
- **IESNA TM-15-11** — *Luminaire Classification System (BUG rating).*
- **IESNA Lighting Handbook**, 10th ed. — reflectance of common surfaces.

---

<div align="center">

*Documento vivo — atualizado a cada evolução do modelo. Modelo implementado em
[`index.html`](../index.html) (`fotometriaIndices`) e no banco pela migration
[`20260710160356_expand_pontos_tier3_photometry.sql`](../supabase/migrations/20260710160356_expand_pontos_tier3_photometry.sql).*

---

**Autor:** Danilo Valim · **DOI:** [10.5281/zenodo.21305310](https://doi.org/10.5281/zenodo.21305310)

</div>
