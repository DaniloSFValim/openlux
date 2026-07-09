# Tier 2: Fotometria, Energia e Conformidade Regulatória

**Documento:** Referência de campos Tier 2 para gestão avançada de luminárias  
**Última atualização:** 2026-07-09  
**Status:** Campo de aplicação — dados opcionais para auditoria técnica

---

## 📌 Visão Geral

A camada **Tier 2** adiciona parâmetros de engenharia necessários para:
- **Auditoria de eficiência energética** (lumens, eficácia)
- **Conformidade regulatória** (fator de potência, THD)
- **Proteção e robustez** (grau de impacto, proteção contra surto)
- **Interoperabilidade** (conectividade, arquivo fotométrico)
- **Poluição luminosa** (base para futuros cálculos de radiação)

**Todos os campos Tier 2 são opcionais.** Modelos criados sem preenchê-los continuam funcionando normalmente.

---

## 🔋 Seção 1: Desempenho Energético

### 1.1 Fluxo Luminoso (lm) — `fluxo_luminoso_lm`

**Definição:** Quantidade total de luz emitida pela luminária em lumens (lm).

**Tipo:** INTEGER > 0  
**Unidade:** lumens (lm)  
**Intervalo recomendado:** 
- Luminárias viárias pequenas: 3.000–8.000 lm
- Luminárias viárias médias: 8.000–15.000 lm
- Luminárias viárias grandes: 15.000–25.000 lm

**Importância:**
- Define capacidade absoluta de iluminação
- Independente da potência (LED 150W pode ter 12.000 lm vs. Sódio 250W com 25.000 lm)
- Essencial para cálculos de Dialux (design de iluminação)

**Exemplo:**
```
Fabricante: Philips CorePro LED 150W
Potência: 150 W
Fluxo: 12.000 lm  ← 80 lm/W de eficácia (muito bom para LED)
```

**Conformidade:**
- ABNT NBR ISO 9910 (fotometria de luminárias)
- ABNT NBR 15611 (iluminação viária)

---

### 1.2 Eficácia Luminosa (lm/W) — `eficacia_luminosa_lm_w`

**Definição:** Razão entre fluxo luminoso e potência consumida. Quanto maior, mais eficiente.

**Tipo:** NUMERIC(5,2) > 0  
**Unidade:** lumens por watt (lm/W)  
**Intervalo típico:**
- Incandescente: 5–15 lm/W
- Fluorescente: 40–60 lm/W
- Sódio de alta pressão: 80–120 lm/W
- LED (2024+): 80–150+ lm/W

**Importância:**
- Métrica principal de eficiência energética
- Permite comparação direta entre tecnologias
- Essencial para cálculos de custo operacional (W/ano → R$/ano)

**Cálculo manual:**
```
Eficácia = Fluxo luminoso / Potência
Exemplo: 12.000 lm ÷ 150 W = 80 lm/W
```

**Conformidade:**
- ABNT NBR 15611 (eficiência em iluminação pública)
- IEC 62471 (fotossegurança)

---

### 1.3 Fator de Potência (FP) — `fator_potencia_fp`

**Definição:** Razão entre potência real consumida e potência aparente. Mede qualidade de energia reativa.

**Tipo:** NUMERIC(3,2), intervalo [0.90, 1.0]  
**Unidade:** adimensional (0.0–1.0)  
**Valores típicos:**
- 0.90–0.94: Equipamentos eletrônicos com corretor passivo (capacitor)
- 0.95–1.0: Equipamentos com correção ativa (PFC)
- < 0.90: Não conformidade (multado pela concessionária)

**Importância:**
- Cobrado pela concessionária em conta de energia (mesmo se FP < 0.92)
- Penalidades: acréscimo de até 50% na tarifa se FP < 0.92
- LED moderno = FP ≈ 0.98–1.0 (excelente)
- Sódio e Vapor Mercúrio = FP ≈ 0.90–0.95 (com reatores eletromagnéticos)

**Conformidade:**
- ABNT NBR 15611 (FP mínimo 0.90 obrigatório)
- Resolução ANEEL 414/2010 (penalidades por baixo FP)

**Exemplo de impacto financeiro:**
```
Consumo: 1.000 kWh/mês
Tarifa base: R$ 0,50/kWh
FP = 0.85 (não conforme):
  Custo adicional ≈ R$ 250/mês (~50% penalidade)

FP = 0.95 (conforme):
  Custo normal: R$ 500/mês
```

---

### 1.4 Distorção Harmônica Total (THD) — `thd_percentual`

**Definição:** Percentual de distorção de frequência que o equipamento introduz na rede elétrica.

**Tipo:** NUMERIC(5,2), intervalo [0, 100]  
**Unidade:** porcentagem (%)  
**Valores típicos:**
- 0–5%: Excelente (LED moderno com PFC ativo)
- 5–10%: Bom (LED com filtro)
- 10–20%: Aceitável (eletrônicos com reatores antigos)
- > 20%: Ruim (equipamentos de baixa qualidade)

**Importância:**
- Elevado THD causa aquecimento em transformadores e cabos
- Interfere em equipamentos sensíveis (informática, telecomunicações)
- Reduz vida útil de equipamentos próximos
- Futuro: podem vir multas por poluição harmônica

**Conformidade:**
- ABNT NBR IEC 61000-3-2 (limites de harmônicas)
- Resolução ANEEL 24/2000 (indicador de qualidade de energia)

**Dica de campo:**
```
Se o gestor notar "lampejo" em equipamentos próximos:
  → Verificar THD do equipamento de iluminação
  → THD > 15% é suspeito
  → Considerar troca por LED com PFC ativo
```

---

## 🛡️ Seção 2: Proteção & Robustez

### 2.1 Grau IK — `grau_ik`

**Definição:** Classificação de resistência mecânica a impactos. Indica proteção contra vandalismo/acidentes.

**Tipo:** TEXT (valores: IK08, IK09, IK10)  
**Padrão:** IEC 62262  
**Valores:**

| Grau | Energia | Descrição | Cenário |
|------|---------|-----------|---------|
| **IK08** | 2 J | Moderada | Protege de quedas pequenas, galhos |
| **IK09** | 5 J | Boa | Resiste a impacto de ferramenta ou galho pesado |
| **IK10** | 20 J | Excelente | Resiste a impacto forte (marreta leve) |

**Importância em Niterói:**
- Áreas de risco (periferias): exigir mínimo IK09
- Áreas com vandalismo frequente: preferir IK10
- Parques e orlas: IK08 suficiente (ambiente controlado)

**Tabela de conversão:**
```
1 Joule = 1 kg caindo 10 cm
2 J (IK08) ≈ impacto com martelo pequeno
5 J (IK09) ≈ ferramenta leve a moderada
20 J (IK10) ≈ ferramenta pesada
```

**Conformidade:**
- IEC 62262 (resistência a impactos)
- ABNT NBR IEC 62262 (equivalente brasileiro)

---

### 2.2 Protetor de Surto (DPS) — `dps_especificacao`

**Definição:** Especificação da proteção contra picos de tensão (raio, manobra).

**Tipo:** TEXT (exemplo: "10kV/10kA", "20kV/5kA")  
**Unidade:** Tensão (kV) / Corrente (kA)  
**Valores típicos:**
- 10kV/10kA: Proteção básica (Niterói padrão)
- 20kV/5kA: Proteção média
- 40kV/10kA: Proteção alta (áreas com raios frequentes)

**Importância:**
- Raios em Niterói: ~20–40 eventos/km²/ano (alta incidência)
- Sem DPS: ≈ 5–10% de equipamentos danificados anualmente
- Com DPS 10kV/10kA: reduz perdas para < 0.5%

**Exemplo de especificação:**
```
Luminária Philips CorePro LED 150W
DPS: 10kV/10kA (proteção padrão)
Vida esperada com raios: 8–10 anos
Vida esperada sem DPS: 2–3 anos
```

**Conformidade:**
- IEC 61643-11 (DPS classe 2/3)
- ABNT NBR IEC 61643-11

---

### 2.3 Tipo de Conectividade — `tipo_conectividade`

**Definição:** Especificação do tipo de tomada para célula fotoelétrica ou sistema de telemanejo.

**Tipo:** TEXT  
**Valores:**

| Tipo | Descrição | Compatibilidade |
|------|-----------|-----------------|
| **sem_tomata** | Sem conector | Sem célula fotoelétrica |
| **ansi_3pin** | 3 pinos ANSI | Células simples (on/off) |
| **ansi_7pin** | 7 pinos NEMA | Células inteligentes, 0-10V dim |
| **zhaga** | Padrão Zhaga | Conectores padronizados (futuro) |

**Importância:**
- Define compatibilidade com células fotoeléctricas
- ANSI 7-pin permite telemanejo (dimming remoto)
- Zhaga é o padrão futuro (compatibilidade entre marcas)

**Cenários:**
```
1. Luminária sem célula:
   tipo_conectividade = "sem_tomata"
   
2. Luminária com célula simples (on/off):
   tipo_conectividade = "ansi_3pin"
   
3. Luminária com célula inteligente (dimming, telemanejo):
   tipo_conectividade = "ansi_7pin"
```

**Conformidade:**
- ANSI C136.10 (conector 7-pin)
- Zhaga Standard (futuro padrão aberto)

---

## 📄 Seção 3: Arquivo Fotométrico

### 3.1 Arquivo .IES — `arquivo_ies_url`

**Definição:** URL do arquivo fotométrico em formato IES (Illuminating Engineering Society) para simulação em Dialux.

**Tipo:** TEXT (URL)  
**Formato:** Arquivo .ies (ASCII)  
**Tamanho máximo:** 5 MB  
**Armazenamento:** Supabase Storage bucket `luminarias-ies`

**Importância:**
- Arquivo padrão internacional para fotometria
- Essencial para design de iluminação em Dialux/Relux
- Contém distribuição 3D de intensidade luminosa
- Permite simulação de iluminação antes de instalação

**Como obter:**
1. Solicitar ao fabricante da luminária
2. Disponível normalmente no website do fabricante
3. Padrão: download gratuito do catálogo técnico

**Exemplo de arquivo:**
```
IESNA:LM-63-2002
[Cabeçalho com metadados]
[Dados de intensidade em diferentes ângulos]
[Típico: 10–50 kB por arquivo]
```

**Conformidade:**
- IESNA LM-63-2002 (padrão de formato .ies)
- IEC 62884 (equivalente internacional)

---

## 📊 Tabela de Conformidade por Tipo de Tecnologia

| Campo | LED | Vapor Sódio | Metálico | Fluorescente | Sem Lâmpada |
|-------|-----|------------|---------|-------------|------------|
| Fluxo | ✅ Obrigatório | ✅ Recomendado | ✅ Recomendado | ✅ Recomendado | ❌ N/A |
| Eficácia | ✅ Obrigatório | ✅ Recomendado | ✅ Recomendado | ✅ Recomendado | ❌ N/A |
| Fator Potência | ✅ 0.98–1.0 | ⚠️ 0.90–0.94 | ⚠️ 0.90–0.94 | ⚠️ 0.90–0.94 | ❌ N/A |
| THD | ✅ 3–8% | ⚠️ 10–15% | ⚠️ 10–15% | ⚠️ 5–10% | ❌ N/A |
| Grau IK | ✅ Recomendado | ✅ Recomendado | ✅ Recomendado | ✅ Recomendado | ⚠️ Se possível |
| DPS | ✅ Recomendado | ✅ Recomendado | ✅ Recomendado | ✅ Recomendado | ⚠️ Se possível |
| Conectividade | ✅ Recomendado | ✅ Recomendado | ✅ Recomendado | ⚠️ Raro | ❌ N/A |
| Arquivo .IES | ✅ Recomendado | ⚠️ Raro | ⚠️ Raro | ⚠️ Raro | ❌ N/A |

**Legenda:**
- ✅ Importante / Disponível
- ⚠️ Condicional
- ❌ Não se aplica

---

## 🔍 Checklist de Preenchimento

### Quando Preencher Tier 2?

**✅ Sempre, para:**
- LED (tecnologia dominante em Niterói 2026)
- Projetos novos de expansão/modernização
- Auditoria técnica de parque existente

**⚠️ Quando possível, para:**
- Retrofit de equipamentos antigos (Sódio, Metálico)
- Reparos emergenciais (informações reduzidas aceitáveis)
- Histórico de equipamentos descontinuados

**❌ Não necessário, para:**
- Luminárias "Sem Lâmpada" (carcaça vazia)
- Equipamentos de status desconhecido
- Protótipos/testes internos

---

## 📈 Exemplo Completo: Preenchimento

### Caso 1: LED Novo (Completo)

```sql
INSERT INTO equipamentos_modelo (
  fabricante, modelo, potencia_w,
  tecnologia, tipo_lampada, tipo_luminaria,
  -- Tier 1
  temperatura_cor_k, ip, classe_nbr,
  -- Tier 2 (Desempenho)
  fluxo_luminoso_lm, eficacia_luminosa_lm_w,
  fator_potencia_fp, thd_percentual,
  -- Tier 2 (Proteção)
  grau_ik, dps_especificacao, tipo_conectividade,
  arquivo_ies_url
) VALUES (
  'Philips', 'CorePro LED 150W', 150,
  'LED', 'led', 'viaria',
  4000, 'IP65', 'V3',
  12000, 80.0,      ← Fluxo: 12.000 lm, Eficácia: 80 lm/W
  0.98, 5.0,        ← Excelente FP + baixo THD
  'IK09', '10kV/10kA', 'ansi_7pin',
  'https://storage.supabase.co/...philips-corepo-150w.ies'
);
```

### Caso 2: Vapor de Sódio Antigo (Parcial)

```sql
INSERT INTO equipamentos_modelo (
  fabricante, modelo, potencia_w,
  tecnologia, tipo_lampada, tipo_luminaria,
  -- Tier 1
  temperatura_cor_k, ip, classe_nbr,
  -- Tier 2 (apenas dados disponíveis)
  fluxo_luminoso_lm, eficacia_luminosa_lm_w,
  fator_potencia_fp, thd_percentual,
  grau_ik, dps_especificacao, tipo_conectividade,
  arquivo_ies_url
) VALUES (
  'General Electric', 'Sodium 250W', 250,
  'vapor_sodio', 'vapor_sodio', 'viaria',
  2100, 'IP64', 'P2',
  22000, 88.0,      ← Dados do catálogo
  0.92, 12.0,       ← Valores típicos (reator EM)
  'IK08', NULL, 'sem_tomata',  ← Sem DPS/conectividade
  NULL               ← Sem .IES disponível
);
```

---

## 🆘 Troubleshooting

**P: Qual é o valor padrão se não preencher?**  
R: `NULL` (vazio). Sistema aceita normalmente. Use valores `NULL` para indicar "não disponível".

**P: Posso editar um modelo já criado para adicionar Tier 2?**  
R: Sim. Use botão "Editar" no catálogo → preencha os campos vazios → salve.

**P: Por que meu arquivo .IES não faz upload?**  
R: Verificar:
1. Extensão é `.ies` (case-insensitive)?
2. Arquivo < 5 MB?
3. Bucket `luminarias-ies` existe no Supabase?
4. Token de acesso válido?

**P: O que significa "Fator de Potência = 1.0"?**  
R: Perfeito (potência real = potência aparente). Sem energia reativa. Raro, mas possível com correção ativa (PFC).

**P: Preciso de diploma de engenharia para preencher?**  
R: Não. Use valores do fabricante (catálogo técnico). Se não tiver = deixe em branco.

---

## 📚 Referências

### Normas Técnicas
- **ABNT NBR 15611:2022** — Iluminação de vias de tráfego
- **ABNT NBR IEC 62262:2016** — Grau de proteção contra impacto (IK)
- **IEC 61643-11:2022** — Proteção contra surto
- **IESNA LM-63-2002** — Formato de arquivo fotométrico

### Recursos Online
- Supabase Docs: https://supabase.com/docs
- Philips Lighting Tools: https://www.philips.com/lighting
- Dialux (simulação): https://www.dialuxevo.de/
- Padrão Zhaga: https://www.zhagastandard.org/

### Documentação Interna
- `README.md` — Overview do projeto
- `ARCHITECTURE.md` — Fluxos e componentes
- `/supabase/migrations/` — Historia de schema

---

## 📋 Histórico de Versões

| Versão | Data | Descrição |
|--------|------|-----------|
| 1.0 | 2026-07-09 | Tier 2 implementado (Fotometria + Energia + Proteção) |

---

**Última atualização:** 2026-07-09  
**Status:** ✅ Tier 2 completo | ⏳ Tier 1 (issues abertas) | 🚀 Tier 3 (futuro)
