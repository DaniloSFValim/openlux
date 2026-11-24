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

Recomendação: **SQM-L** (com lente). Fatos conferidos nas fontes do fabricante e na literatura (seção 12):

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

## 10. Dois observadores, níveis de instrumento e calibração cruzada

Estado: o piloto terá **duas pessoas** (o autor no RJ e uma pessoa em SP), com o instrumento da segunda ainda não definido (SQM, câmera ou celular).
Desenho aprovado em `docs/superpowers/specs/2026-11-24-field-pilot-design.md`.

- **Risco:** com um aparelho por região, a diferença entre RJ e SP se confunde com a diferença entre aparelhos.
- **Regra:** o **SQM do autor é a referência**. Um segundo aparelho só entra na estatística confirmatória se for calibrado contra ele em **visitas lado a lado** (mesmo
  local e mesma noite, ambas aprovadas no controle de qualidade). O desvio é a mediana de (magnitude do aparelho − magnitude da referência) e a leitura corrigida é `bruta − desvio`.
- **Critérios de aceite da calibração (proposta, a congelar):** pelo menos 2 locais e 2 visitas lado a lado (de preferência um claro e um escuro); desvio médio de no máximo 0,3 mag;
  variação do desvio entre locais de no máximo 0,15 mag (um desvio que muda com o brilho não é constante e não pode ser corrigido por uma soma).
- **Níveis** (`instrument_type` no CSV): `sqm` e `camera_calibrated` chegam ao nível de **validação** se forem a referência ou passarem na calibração; `phone` e `camera_uncalibrated`
  são **sempre exploratórios**. Dado exploratório é relatado em separado e nunca entra no veredito.
- **Câmera ou celular como segundo instrumento:** só contam depois de calibrados contra o SQM; a fotometria de câmera exige redução própria (bias, dark, flat, ponto-zero, extinção) e
  não faz parte do piloto.
- **Conferir o arquivo antes de analisar:** `python scripts/check_measurements.py campo.csv` (esquema, faixas, coordenadas, visitas, duplicatas e proximidade da borda do tile; os limites de
  sanidade são verificações do projeto, não propriedades do SQM). `scripts/run_field_validation.py` recusa arquivos com erros.
- **Cobertura de satélite:** o tile `h13v11` (lon −50 a −40, lat −30 a −20) cobre o RJ e o leste de SP. Locais a menos de 50 km da borda do tile têm contexto incompleto e são recusados
  (antes o corte era silencioso). SP a oeste de −50° ficaria para a expansão.
- **Escolher locais:** `python scripts/suggest_sites.py --ufs RJ SP` sorteia candidatos estratificados pela radiância de satélite do entorno (nas mesmas classes fixas do mapa), com município,
  em `outputs/field/` (não versionado). É **só planejamento**: o satélite não informa acesso, segurança nem permissão, e as coordenadas são do centro do pixel (≈ 460 m). Estratificar pelo
  preditor garante o gradiente sem enviesar a associação testada. A malha de SP vem de `scripts/fetch_mesh.py --uf SP`.

### Instrumento de código aberto como segundo aparelho: o FreeDSM (avaliação em 2026-11-24)

O Gaia4Sustainability (universidades da Catalunha e da Galiza) publica o **FreeDSM**, um fotômetro de baixo custo, de construção doméstica, com plataforma de dados aberta.
O que as fontes lidas dizem: usa um microcontrolador ESP32 com um sensor de luz e sensores de temperatura e umidade, recarga por USB-C ou painel solar; foi **calibrado com instrumentos comerciais**
(a foto mostra vários TESS) por redes neurais e descida de gradiente para calcular a magnitude por segundo de arco quadrado; os dados vão para uma plataforma central e são comparados com
um modelo de brilho natural do céu (Gambons, a partir de dados do satélite Gaia).

**O que a página do projeto no GitLab acrescenta** (lida depois do artigo; corrige a versão anterior deste texto, que dizia que o sensor não era nomeado): sensor de luz **Osram TSL2591**,
sensor AHT2x de temperatura e umidade, cálculo da magnitude por segundo de arco quadrado **a cada minuto**, faixa declarada de **12 a 23 mag/arcsec²**; o firmware é baseado no Tasmota sob **GPL 3.0**, com
processamento adicional em Berry; a plataforma de dados é aberta e o aparelho se registra em `dsm.citic.udc.es`.

**O que continua sem verificação:** o artigo (comunicação de 3 páginas) **não traz nenhum número**: exatidão, incerteza, desvio em relação ao SQM ou ao TESS, repetibilidade, dependência de temperatura,
campo de visão e banda espectral não são declarados nas páginas lidas. Também não vi: custo; a licença do **hardware** e a do script em Berry (não declaradas); a **licença dos dados** da plataforma
(não consta no aviso legal nem na política de privacidade); as instruções de montagem (as subpáginas do wiki não carregaram em ferramenta automática); o mapa de dados e o site do modelo GAMBONS (não legíveis aqui).

**O que isso implica para o piloto (proposta):**
- O FreeDSM **não está caracterizado o bastante** para ser tratado como instrumento de validação. Se for usado, entra pelo caminho da calibração cruzada contra o SQM do autor (seção 10) e, enquanto não passar,
  como dado **exploratório**. Seria preciso um tipo de instrumento próprio (fotômetro calibrado de saída em mag/arcsec²), que o código ainda não tem.
- Aparelho de construção doméstica varia **de unidade para unidade**: cada exemplar precisaria da própria calibração, e a banda espectral e o campo de visão diferentes dos do SQM fazem o desvio **depender do tipo de
  iluminação do local**, o que o critério de variação do desvio entre locais (≤ 0,15 mag) tenta detectar.
- Construir e calibrar um aparelho é um subprojeto; para duas pessoas, um segundo SQM é o caminho mais simples. O FreeDSM é uma boa opção **extra**, e o projeto poderia ser procurado para colaboração, com os termos de dados deles lidos antes.
- O modelo GAMBONS (Masana et al., 2021) estima o brilho natural do céu em noites sem nuvens e sem Lua, nas bandas V (Johnson), fotópica e escotópica, e diz poder ser estendido a outras bandas. É uma referência
  possível para o **piso natural** nos locais escuros (o limite que comprime a relação com o satélite, seção 9), mas **a banda do SQM não é a V**, a disponibilidade e a licença do modelo não foram confirmadas
  (o artigo indica `gambons.fqa.ub.edu`, que não consegui ler) e o uso seria uma análise exploratória secundária, nunca o veredito.

**O que dá para aproveitar do projeto deles (proposta, em ordem de valor):**
1. **GAMBONS como referência do piso natural**, depois de confirmar acesso e licença e de tratar a diferença de banda.
2. **FreeDSM como instrumento extra**, só pela calibração cruzada e como dado exploratório até passar (seção 10); registrar `temp_c` e a umidade, que o aparelho já mede.
3. **Contato com a equipe** para perguntar a licença do hardware e dos dados, e se aceitam compartilhar medições no Brasil; sem licença declarada, os dados deles **não** podem ser reutilizados.
4. **Cuidado de licença:** o firmware do FreeDSM é **GPL 3.0** e o OpenLux é **MIT**. Não copiar código ou firmware deles para este repositório; usar e citar, mantendo-os separados.
5. **Não aproveitar:** a calibração por redes neurais como caixa-preta; ela não tem exatidão declarada e não é reprodutível por nós.

## 11. O que depende do autor

1. Aprovar (ou alterar) os limiares e as regras marcados como proposta, preencher `instruments.reference_device_id` e **congelar** a pré-especificação antes da coleta.
2. Adquirir o SQM-L, definir o instrumento da segunda pessoa (seção 10) e escolher os locais seguindo a seção 4.
3. Decidir onde publicar os dados de campo e sob qual licença (são dados originais do autor).
4. Informar a data da campanha, para escolher o ano do produto de satélite.

## 12. Fontes consultadas (2026-11-23)

Não estão em `docs/references.json` (não passaram pela verificação de DOI do projeto); são URLs consultadas nesta data.

- Unihedron, calculadora de conversão mag/arcsec² → cd/m²: https://unihedron.com/projects/darksky/magconv.php
- Unihedron, FAQ do SQM-L (campo de visão): https://unihedron.com/projects/darksky/faqsqml.php
- Manual do SQM-L (Unihedron; incerteza ±0,1 mag/arcsec² e fórmula de conversão): https://unihedron.com/projects/sqm-l/sqmreport2.pdf
- Schnitt, S. et al. (2013). Temperature stability of the Sky Quality Meter. *Sensors*. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3821345/
- Bará, S. et al. (2020). Magnitude to luminance conversions and visual brightness of the night sky. *MNRAS*, 493, 2429. https://ui.adsabs.harvard.edu/abs/2020MNRAS.493.2429B/abstract
- Medição de brilho do céu, métodos e desafios (revisão): https://arxiv.org/pdf/1709.09558
- Comparação entre radiância de satélite e SQM em Madri (log × log): https://arxiv.org/pdf/1908.05482
- Casado Diez, M. (2024). FreeDSM and the Gaia4Sustainability project: a light pollution meter based on IoT technologies. arXiv:2409.10298 (comunicação de 3 páginas): https://arxiv.org/abs/2409.10298
- Projeto FreeDSM no GitLab (página inicial do wiki, com sensor, faixa e licença do firmware): https://gitlab.citic.udc.es/lia2-publico/g4s
- Gaia4Sustainability, página do dispositivo: https://gaia4sustainability.eu/en/device/ (wiki e repositório: https://gitlab.citic.udc.es/lia2-publico/g4s)
- Masana, E.; Carrasco, J. M.; Bará, S.; Ribas, S. J. (2021). A multi-band map of the natural night sky brightness including Gaia and Hipparcos integrated starlight. *MNRAS*, 501, 5443 (citado pelo artigo acima): https://arxiv.org/abs/2101.01500

