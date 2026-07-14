# Tier 1: Conformidade Regulatória - Referência de Campos

**Versão:** 1.0  
**Data:** 2026-07-14  
**Escopo:** Campos de conformidade regulatória e gestão de ciclo de vida de equipamentos em luminarias públicas

---

## 📋 Visão Geral

Tier 1 adiciona quatro campos obrigatórios para auditoria regulatória e gestão de ativos de infraestrutura de iluminação pública:

| Campo | Tipo | Unidade | Obrigatório | Intervalo |
|-------|------|--------|------------|-----------|
| `inmetro_registro` | TEXT | — | ❌ | 8-12 dígitos (NNNNNNNNNN) |
| `vida_util_anos` | INTEGER | anos | ❌ | 1–100 |
| `garantia_anos` | INTEGER | anos | ❌ | 0–50 |
| `dias_manutencao_preventiva` | INTEGER | dias | ❌ | 1–3650 |

Todos os campos são **opcionais** (NOT NULL constraint não aplicado), permitindo coexistência com modelos legados que não possuem registros regulatórios.

---

## 🔍 Descrição Detalhada

### 1. `inmetro_registro` (TEXT)

**Propósito:** Número de registro do Instituto Nacional de Metrologia, Qualidade e Tecnologia (INMETRO).

**Contexto Regulatório:**
- Equipamentos de iluminação pública importados ou fabricados no Brasil devem estar registrados no INMETRO conforme RDC INMETRO aplicáveis
- O registro garante conformidade com NBR (Normas Brasileiras) e especificações técnicas de segurança/desempenho
- Equipamentos sem registro não devem ser instalados em projetos de licitação pública

**Formato Esperado:**
```
Exemplo: 01234567890 (10-12 dígitos, sem espaços ou caracteres especiais)
ou
Exemplo: INMETRO-01234567890 (com prefixo, conforme documento do equipamento)
```

**Aplicação Prática:**
- Auditor confere registro do equipamento adquirido contra documentação de fabricante
- Sistema marca equipamentos SEM registro como "não conforme" para relatórios de compliance
- Filtro: "Mostrar equipamentos SEM registro INMETRO" para planejamento de substituição

**Tabela de Conformidade (Exemplo):**
| Equipamento | INMETRO | Status | Ação |
|------------|---------|--------|------|
| Philips CorePro 150W LED | 00123456 | ✅ Conforme | Aprovado para aquisição |
| Genérico 100W LED (eBay) | — | ❌ Não conforme | Rejeitar / Devolver |
| Osram Eco LED 100W | 00654321 | ✅ Conforme | Aprovado |

---

### 2. `vida_util_anos` (INTEGER)

**Propósito:** Vida útil esperada do equipamento desde a instalação até o fim de operação segura.

**Contexto Técnico:**
- Define o período de tempo em que o equipamento mantém desempenho dentro de especificações
- Lâmpadas LED típicas: 10–20 anos
- Lâmpadas vapor sódio: 5–8 anos
- Luminárias estruturais: 15–25 anos (estrutura) + vida da fonte de luz

**Cálculo de Vida Útil Remanescente:**
```sql
anos_remanescentes = vida_util_anos - EXTRACT(YEAR FROM AGE(CURRENT_DATE, data_instalacao))
```

Exemplo:
- Equipamento instalado: 2023-07-14
- Vida útil: 10 anos
- Data atual: 2026-07-14
- Anos decorridos: 3
- **Anos remanescentes: 7**

**Estados de Ciclo de Vida:**
| Estado | Condição | Ação Recomendada |
|--------|----------|-----------------|
| `ativo` | Remanescente ≥ 2 anos | Operação normal, manutenção de rotina |
| `proximo_vencimento` | Remanescente < 2 anos | Planejamento de substituição no orçamento |
| `vencido` | Remanescente < 0 | PARAR — risco de falha, substituição urgente |

**View de Rastreamento:**
```sql
SELECT * FROM v_equipamentos_vencidos 
WHERE status_vida_util IN ('vencido', 'proximo_vencimento')
ORDER BY anos_remanescentes ASC;
```

---

### 3. `garantia_anos` (INTEGER)

**Propósito:** Período de cobertura de garantia do fabricante contra defeitos de fábrica.

**Contexto Operacional:**
- Define responsabilidade do fornecedor pela substituição de equipamento defeituoso
- Típicamente: 1–5 anos para LED, 1–3 para componentes eletrônicos
- Período de garantia é importante para licitações públicas (critério de avaliação)

**Exemplo de Dados:**
| Equipamento | Vida Útil | Garantia | Gap |
|------------|----------|----------|-----|
| Philips CorePro LED | 15 anos | 5 anos | 10 anos desprotegido |
| Osram Eco LED | 15 anos | 3 anos | 12 anos desprotegido |

**Filtro de Risco:** "Equipamentos com garantia próxima do vencimento (< 6 meses)"
```sql
SELECT * FROM equipamentos_modelo
WHERE DATE_ADD(data_instalacao, INTERVAL garantia_anos YEAR) < DATE_ADD(CURDATE(), INTERVAL 6 MONTH)
  AND data_instalacao IS NOT NULL;
```

**Impacto em Manutenção:**
- Equipamentos em período de garantia: contato com fabricante para defeitos
- Equipamentos após garantia: custo de manutenção cabe à municipalidade

---

### 4. `dias_manutencao_preventiva` (INTEGER)

**Propósito:** Intervalo recomendado de manutenção preventiva em dias.

**Contexto de Manutenção:**
- Limpeza de lentes (acúmulo de poeira → 15–20% perda luminosa)
- Inspeção de cabos/conexões
- Verificação de detectores fotoelétricos (dia/noite)
- Aperto de conectores

**Exemplos Típicos:**
| Tipo | Intervalo | Justificativa |
|------|-----------|--------------|
| Luminaria viária urbana | 180 dias | Menor exposição a poluição |
| Luminaria em zona litorânea | 90 dias | Corrosão acelerada por sal |
| Luminaria em zona industrial | 120 dias | Poluição aérea (fuligem) |
| Luminaria em área com chuva ácida | 60 dias | Degradação acelerada |

**Cálculo de Proxima Manutenção:**
```sql
SELECT 
  id,
  codigo_seconser,
  data_ultima_intervencao,
  DATE_ADD(data_ultima_intervencao, INTERVAL dias_manutencao_preventiva DAY) AS proxima_manutencao,
  DATEDIFF(CURDATE(), DATE_ADD(data_ultima_intervencao, INTERVAL dias_manutencao_preventiva DAY)) AS dias_atrasado
FROM pontos_luminaria p
JOIN equipamentos_modelo em ON p.modelo_id = em.id
WHERE em.dias_manutencao_preventiva IS NOT NULL
  AND p.data_ultima_intervencao IS NOT NULL
ORDER BY dias_atrasado DESC;
```

**Alertas Operacionais:**
- 🟢 Verde: Manutenção em dia (próxima em > 30 dias)
- 🟡 Amarelo: Manutenção próxima (próxima em 1–30 dias)
- 🔴 Vermelho: Manutenção atrasada (próxima era há > 30 dias)

---

## 📊 Exemplos de Entrada de Dados

### Exemplo 1: LED Moderno (Completo)
```json
{
  "fabricante": "Philips",
  "modelo": "CorePro 150W LED FOCO",
  "potencia_w": 150,
  "inmetro_registro": "00123456",
  "vida_util_anos": 15,
  "garantia_anos": 5,
  "dias_manutencao_preventiva": 180
}
```

**Interpretação:**
- Equipamento registrado no INMETRO (conforme)
- Vida útil: 15 anos → em 2038 será fim-de-vida
- Cobertura de garantia até 2031
- Verificação recomendada a cada 6 meses

### Exemplo 2: Equipamento Legado (Parcial)
```json
{
  "fabricante": "Desconhecido",
  "modelo": "Vapor Sódio 250W (1980s)",
  "potencia_w": 250,
  "inmetro_registro": null,
  "vida_util_anos": 8,
  "garantia_anos": null,
  "dias_manutencao_preventiva": 120
}
```

**Interpretação:**
- Equipamento antigo, sem registro INMETRO (legado)
- Vida útil de apenas 8 anos (tecnologia antiga)
- Sem garantia ativa (equipamento muito antigo)
- Requer manutenção a cada 4 meses (mais frequente que LED)

### Exemplo 3: Equipamento Novo Sem Dados Completos
```json
{
  "fabricante": "Osram",
  "modelo": "Eco LED 100W",
  "potencia_w": 100,
  "inmetro_registro": "00654321",
  "vida_util_anos": 12,
  "garantia_anos": null,
  "dias_manutencao_preventiva": null
}
```

**Interpretação:**
- INMETRO presente (conforme)
- Vida útil estimada em 12 anos
- Garantia não preenchida (verificar com fornecedor)
- Intervalo de manutenção não definido (usar padrão de 180 dias)

---

## 🔄 Integração com Outros Tiers

### Tier 2 → Tier 1
Tier 1 (conformidade) é **complementar** a Tier 2 (fotometria):
- Tier 2 campos: `fluxo_luminoso_lm`, `eficacia_luminosa_lm_w`, `fator_potencia_fp`, `thd_percentual`
- Tier 1 campos: `inmetro_registro`, `vida_util_anos`, `garantia_anos`, `dias_manutencao_preventiva`

Exemplo integrado:
```json
{
  "modelo": "Philips LED 150W",
  "potencia_w": 150,
  
  // Tier 2
  "fluxo_luminoso_lm": 12000,
  "eficacia_luminosa_lm_w": 80.0,
  
  // Tier 1
  "inmetro_registro": "00123456",
  "vida_util_anos": 15,
  "garantia_anos": 5
}
```

### Futuros (Fase 3)
- Tier 3: Visualização fotométrica (.IES) — complementa Tier 2 com curva polar
- Fase 4: PWA Offline — permite visualizar dados Tier 1 em campo sem internet

---

## 🛠️ API / RPC

### Criar Modelo com Tier 1

```javascript
const { data: modeloId, error } = await sb.rpc('ip_criar_modelo', {
  p_fabricante: 'Philips',
  p_modelo: 'CorePro 150W LED',
  p_potencia_w: 150,
  p_inmetro_registro: '00123456',
  p_vida_util_anos: 15,
  p_garantia_anos: 5,
  p_dias_manutencao_preventiva: 180
});
```

### Atualizar Modelo com Tier 1

```javascript
const { error } = await sb.rpc('ip_atualizar_modelo', {
  p_id: 'uuid-do-modelo',
  p_inmetro_registro: '00123456',
  p_vida_util_anos: 15,
  p_garantia_anos: 5
});
```

### Listar Modelos com Tier 1

```javascript
const { data: modelos, error } = await sb.rpc('ip_listar_modelos');
// Cada modelo inclui campos Tier 1 (podem ser null)
modelos.forEach(m => {
  console.log(`${m.modelo}: INMETRO=${m.inmetro_registro}, Vida=${m.vida_util_anos}a`);
});
```

---

## ✅ Checklist de Implementação

- [x] Schema database: 4 colunas adicionadas a `equipamentos_modelo`
- [x] RPC `ip_criar_modelo`: parâmetros Tier 1 adicionados
- [x] RPC `ip_atualizar_modelo`: parâmetros Tier 1 adicionados
- [x] Helper function: `calcular_vida_util_remanescente()`
- [x] View: `v_equipamentos_vencidos` para rastreamento de ciclo de vida
- [x] UI Form: campos de entrada para Tier 1 no painel de administrador
- [x] Validação Frontend: ranges de valores (vida útil > 0, garantia >= 0)
- [x] Testes E2E: criação de modelo com Tier 1, cálculo de vida útil
- [x] Documentação: este arquivo (FIELD_REFERENCE_TIER1_COMPLIANCE.md)

---

## 📚 Referências Normativas

- **ABNT NBR 5101**: Iluminação pública – Especificações gerais
- **ABNT NBR IEC 60529**: Graus de proteção proporcionados por invólucros
- **INMETRO Portaria N° 526/2020**: Conformidade de equipamentos de iluminação
- **ABNT NBR ISO/IEC Guide 50**: Segurança de crianças e consumidores vulneráveis

---

## 🆘 Perguntas Frequentes

**P: Posso deixar campos Tier 1 em branco?**  
R: Sim, todos são opcionais (DEFAULT NULL). Modelos legados podem não ter essa informação.

**P: Como saber qual é a vida útil de um equipamento existente?**  
R: Consultar datasheet do fabricante ou especificação original de licitação. Se não disponível, usar valores típicos:
- LED: 10–20 anos
- Vapor sódio: 5–8 anos
- Fluorescente: 5–7 anos

**P: Qual intervalo de manutenção usar se não estiver especificado?**  
R: Padrão sugerido: 180 dias (6 meses). Ajustar conforme clima e poluição local.

**P: Como integrar com software de gestão de ativos (CMMS)?**  
R: Via API REST: exportar dados de Tier 1 (inmetro_registro, vida_util_anos, garantia_anos) em JSON ou CSV para importação em software de terceiros (SAP, Oracle, Maximo, etc).

---

**Última atualização:** 2026-07-14  
**Mantido por:** Equipe de DevOps & Reprodutibilidade
