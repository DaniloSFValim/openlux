# Protocolo de validação em campo com SQM

Estado: **protocolo proposto; nenhuma medição foi feita.** O código de análise existe e foi testado apenas com dados
sintéticos (`tests/test_field.py`). Os limiares e as regras marcados como **proposta** são do projeto, não vêm de norma
nem de literatura, e precisam da aprovação do autor antes da coleta.

## 1. O que se quer testar (e o que não)

**Hipótese.** O brilho zenital medido no chão com um SQM, convertido em luminância, cresce, em ordem de postos, com a
radiância noturna vista pelo satélite no entorno do local.

**Não se testa:** calibração absoluta, causa física, nem a estabilidade temporal da série. O satélite mede luz emitida para
cima; o SQM mede o brilho do céu, que integra luz de dezenas de km e depende da atmosfera. São grandezas diferentes: a pergunta
é de **associação monotônica**, e um resultado favorável não chama o OpenLux de "validado".

## 2. Por que um gradiente e não uma cidade só

Uma cidade quase toda brilhante dá faixa estreita de radiância: com poucos locais e leituras com incerteza, não se distingue
sinal de ruído (restrição de faixa). O desenho precisa de um gradiente do **escuro ao claro** em todo o estado. Niterói e o Rio
entram, se o autor quiser, só como extremo claro. O extremo escuro é o mais informativo, e é onde o ruído do S-NPP
pós-2021 mais pesa (`docs/DECISIONS.md`, seções 3 e 7), por isso o sensor primário é o NOAA-20 (seção 7).

## 3. Instrumento

Recomendação: **SQM-L** (com lente). Fatos conferidos nas fontes do fabricante e na literatura (seção 11):

- Campo de visão do SQM-L: cerca de 20° de largura a meia altura (≈ 10° de meia largura); o modelo sem lente é bem mais amplo.
- Incerteza de calibração informada pelo fabricante: ±0,1 mag/arcsec² (≈ ±10 %).
- As leituras variam com a temperatura (Schnitt et al., 2013); por isso a temperatura é registrada em toda visita.
- Conversão oficial da Unihedron: L [cd/m²] = 10,8×10⁴ × 10^(−0,4·m). É **aproximada**: depende do espectro do céu
  (Bará et al., 2020). Usada aqui só para trabalhar numa escala linear; a análise é por postos, que não depende da constante.

**Decisão minha:** usar **um único** aparelho na campanha inteira, para que o erro de calibração seja comum a todos os locais
(afeta o nível, não a ordem). Se houver mais de um, medir os dois lado a lado numa noite e registrar a diferença.

## 4. Escolha dos locais

**Proposta** (ajustável antes da coleta):

1. Pelo menos **20 locais** (`min_sites`). Esse número é uma proposta; **não vem de um cálculo de poder estatístico**.
2. Estratificar pela radiância de contexto do satélite (escala logarítmica) em pelo menos 4 faixas, com pelo menos 4 locais por
   faixa e pelo menos 3 nos mais escuros.
3. Sem luz direta no campo de visão do aparelho (postes, fachadas, faróis) e horizonte livre em volta; registrar obstruções.
   Estudos com SQM relatam leituras mais escuras que o esperado quando o pixel de satélite inclui emissão direta, o que deixaria
   o local atípico para o satélite, não para o céu.
4. Preferir locais afastados da costa: a máscara de água do produto remove pixels do mar e reduz a área válida do entorno
   (`valid_fraction` é registrado).
5. Registrar coordenadas por GPS com precisão de dezenas de metros e foto do local; obter permissão onde for propriedade privada.

## 5. Procedimento de medição

**Proposta de rotina** (por visita):

1. Só após o fim do crepúsculo astronômico (Sol ≤ −18°), com **Lua abaixo do horizonte** e **céu sem nuvens** (anotação do
   observador; o SQM não detecta nuvens).
2. Apontar o aparelho ao zênite, estável (tripé ou apoio), sem sombra do corpo do observador.
3. Registrar **pelo menos 5 leituras** seguidas, anotando hora, temperatura e identificador do aparelho.
4. Repetir cada local em **pelo menos 2 noites diferentes** (`min_valid_visits_per_site`), para ver a variação entre noites.
5. Anotar a altura do Sol e da Lua a partir de uma efeméride de sua escolha, registrada na coluna `ephemeris_source`.
6. Preencher o CSV no modelo `docs/field/measurements_template.csv` (uma linha por leitura).

## 6. Controle de qualidade (`openlux.field.qc_visits`)

Uma visita é descartada, com o motivo registrado, se: tem menos de 5 leituras; o Sol está acima de −18°; a Lua está acima do
horizonte; houve nuvens; ou a amplitude das leituras passa de 0,2 mag. A mediana das leituras dá a visita; o local usa a **média em
luminância** (não em magnitude) das visitas válidas. Os mesmos valores estão em `docs/field/preregistration.json`, e um teste
garante que o código e esse arquivo não divergem.

## 7. Contexto do satélite

- Para cada local, a radiância média (ponderada pela área do pixel) dos pixels válidos cujo centro está a até **r km**, com
  r ∈ {1, 2, 5, 10, 20, 50}. Raios menores que 1 km não são usados (pixel de ≈ 460 m, inclusão por centro).
- **Sensor primário: NOAA-20 (VJ146A4); secundário: S-NPP (VNP46A4).** Razão: o S-NPP tem piso de ruído muito maior desde 2022.
- Produto anual do ano da campanha; se ainda não existir, o mais recente disponível (o ano usado é gravado no relatório).
- **Limites do contexto:** o composto anual é uma média de muitas noites e só ele é comparado com poucas noites de campo; o
  satélite passa de madrugada e o SQM mede em outra hora, quando parte da iluminação pode estar apagada (a hora é registrada);
  a análise **não usa um modelo de propagação**, só uma família de raios e a escolha do raio entra no teste (seção 8).

## 8. Análise pré-especificada (`openlux.field`, `scripts/run_field_validation.py`)

1. Spearman entre a luminância do céu e a radiância de contexto, **para cada raio**.
2. **Teste de permutação do máximo de ρ sobre os raios**: como o raio é escolhido nos dados, o valor-p já desconta a busca
   (10.000 permutações, semente fixa registrada).
3. **Leave-one-out** no raio escolhido: ρ retirando cada local, para ver se um único local sustenta o resultado.
4. Tudo é calculado para os dois sensores; **o veredito vem só do primário**.

**Critérios (proposta, a congelar):** ρ máximo observado ≥ 0,7; valor-p da permutação ≤ 0,05; ρ mínimo no leave-one-out ≥ 0,6.
Se atendidos: *consistente* com a hipótese; se não, *inconsistente*; com menos de 20 locais utilizáveis: *dados insuficientes*.
Os limiares não vêm da literatura: são o que o autor aceita como "associação forte e não frágil". **Definidos antes de qualquer
medição**, para que não sejam ajustados depois de ver os dados.

**Disciplina.** O executor só emite veredito confirmatório se `status` em `docs/field/preregistration.json` for `frozen`.
Enquanto for `draft`, só roda com `--exploratory`, e o relatório se declara exploratório. Congelar = mudar o `status` e
**fazer o commit antes da primeira medição**.

## 9. Limitações e riscos

- Associação monotônica não é calibração: um bom ρ é compatível com escalas muito diferentes entre radiância e brilho do céu.
- A conversão mag → luminância é aproximada e o SQM tem banda própria; a banda do DNB do VIIRS é outra (e é pouco sensível ao azul
  de LEDs). A análise por postos reduz, mas não elimina, esse efeito.
- O componente natural do céu (aeroluminescência, Via Láctea, luz zodiacal) pode dominar nos locais mais escuros e **comprime** a
  relação no extremo escuro; o piso natural deve ser lido dos próprios locais mais escuros da campanha, sem valor assumido aqui.
- Aerossóis e umidade alteram o brilho do céu entre noites; a repetição em noites diferentes mede essa dispersão, não a corrige.
- Com poucos locais, o ρ é incerto; a permutação controla falso positivo, mas não dá poder para detectar associações fracas.
- Um aparelho único traz um erro de calibração comum; o desvio de temperatura é registrado, mas não corrigido.
- Resultados favoráveis valem para o estado do Rio e para o intervalo de radiância amostrado, não são generalizáveis sem mais dados.

## 10. O que depende do autor

1. Aprovar (ou alterar) os limiares e as regras marcados como proposta e **congelar** a pré-especificação antes da coleta.
2. Adquirir o SQM-L e escolher os locais seguindo a seção 4.
3. Decidir onde publicar os dados de campo e sob qual licença (são dados originais do autor).
4. Informar a data da campanha, para escolher o ano do produto de satélite.

## 11. Fontes consultadas (2026-11-23)

Não estão em `docs/references.json` (não passaram pela verificação de DOI do projeto); são URLs consultadas nesta data.

- Unihedron, calculadora de conversão mag/arcsec² → cd/m²: https://unihedron.com/projects/darksky/magconv.php
- Unihedron, FAQ do SQM-L (campo de visão): https://unihedron.com/projects/darksky/faqsqml.php
- Manual do SQM-L (Unihedron; incerteza ±0,1 mag/arcsec² e fórmula de conversão): https://unihedron.com/projects/sqm-l/sqmreport2.pdf
- Schnitt, S. et al. (2013). Temperature stability of the Sky Quality Meter. *Sensors*. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3821345/
- Bará, S. et al. (2020). Magnitude to luminance conversions and visual brightness of the night sky. *MNRAS*, 493, 2429. https://ui.adsabs.harvard.edu/abs/2020MNRAS.493.2429B/abstract
- Medição de brilho do céu, métodos e desafios (revisão): https://arxiv.org/pdf/1709.09558
- Comparação entre radiância de satélite e SQM em Madri (log × log): https://arxiv.org/pdf/1908.05482
