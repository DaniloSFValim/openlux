# Análise exploratória: luz noturna e unidades de conservação (2025)

**Estado:** calculada, **não publicada no site**. Aguarda revisão do responsável antes de qualquer divulgação.
**Escopo:** associação espacial exploratória. Não é causa, não é medição de impacto sobre fauna, flora ou saúde humana, e não controla urbanização.

## Dados

| Item | Fonte |
|---|---|
| Unidades de conservação | CNUC (MMA), `shp_cnuc_2025_08`, CC BY (licença lida na página do conjunto). 3.122 feições; 508 UCs tocam o estado. |
| Limites municipais | IBGE, Malha Municipal Digital 2024 (RJ). |
| Radiância | NASA Black Marble VJ146A4 (NOAA-20), ano 2025, qualidade 0, máscara de terra. |

Script: `scripts/analise_areas_protegidas.py`. Saídas em `outputs/ambiental/` (`uc_por_municipio.csv`, `resumo.json`).

## Resultados

| Medida | Valor |
|---|---|
| Correlação de Spearman entre a fração da área municipal em UC e a radiância média de 2025 (92 municípios) | ρ = 0,32; p = 0,002 |
| Correlação entre área do município e radiância | ρ = −0,43 |
| Correlação entre área do município e fração em UC | ρ = 0,02 (a área não explica a fração em UC) |
| Radiância média dos pixels dentro das UCs | 2,14 nW·cm⁻²·sr⁻¹ (n = 56.560) |
| Radiância média dos pixels fora das UCs | 4,56 nW·cm⁻²·sr⁻¹ (n = 162.447) |
| Mediana dentro e fora | 0 nos dois casos: a maioria dos pixels é escura |

## Limitações

1. **Urbanização não controlada.** A camada de áreas urbanizadas do IBGE está bloqueada por licença não verificada. A associação pode refletir urbanização, e não efeito das UCs.
2. **Radiância de superfície orbital, não brilho do céu.**
3. **Sobreposição de UCs.** Em Paracambi, a soma das áreas das UCs (259,9 km²) excede a área municipal (190,9 km²) porque há sobreposição real (APA do Rio Guandu cobre 189,7 km²). A análise usa a união das geometrias, sem dupla contagem.
4. **Nomes das UCs.** A codificação do `.dbf` está danificada (ex.: "ÃREA DE PROTEÃÃO"). A correção parcial está em `outputs/ambiental/cnuc_2025_08_atributos_corrigidos.csv`. Não use nomes de UC sem conferir no site oficial do CNUC. A análise usou só geometria e códigos.

## Para publicar

- Revisão do responsável sobre o método e os resultados.
- Controle da urbanização, que depende da licença das áreas urbanizadas do IBGE.
- Conferência dos nomes das UCs no site oficial do CNUC.

## Atualização: controle de urbanização (municipal)

Feito com `scripts/analise_controle_urbanizacao.py` (saída em `outputs/ambiental/controle_urbanizacao.json`).

- Sem controle: ρ = 0.32 (p = 0.002).
- Fração urbana (2019) x radiância (2025): ρ = 0.97. Fração em UC x fração urbana: ρ = 0.39.
- Controlando pela fração urbana: ρ parcial = -0.26 (p ≈ 0.016, permutação).
- Controlando também pela área municipal: ρ parcial = -0.23.

**Conclusão corrigida:** a associação positiva inicial se deve à urbanização. Ajustada, a associação é negativa: municípios com mais área em UC são mais escuros do que o esperado para o seu grau de urbanização. Continua exploratória e não causal. O controle no nível dos pixels depende dos polígonos do CNUC, que não estão neste ambiente.
