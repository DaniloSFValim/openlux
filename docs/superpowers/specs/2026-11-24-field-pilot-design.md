# Piloto de validação em campo com duas pessoas: desenho

Estado: **aprovado pelo autor em 2026-11-24** (conversa de desenho). Complementa `docs/FIELD_VALIDATION.md`.

## Intenção
Testar se o brilho do céu medido no chão cresce com a radiância de satélite do entorno (`docs/FIELD_VALIDATION.md`), com **duas pessoas**: o autor (RJ) e uma pessoa em SP.
Depois do piloto, a expansão para o Sudeste e, mais tarde, para o Brasil. Não há plataforma de envio nesta etapa: formulário/planilha CSV, revisão pelo autor e verificações automáticas.

## Objetivos, não objetivos
- **Objetivos:** gradiente do escuro ao claro em RJ e leste de SP; dado de campo confiável; nada de resultado confirmatório sem pré-especificação congelada.
- **Não objetivos desta etapa:** plataforma web de envio, contas, moderação, fotos, Sudeste/Brasil, pipeline de fotometria de câmera.
- **Antiobjetivo:** deixar o instrumento ou a região do observador passar por efeito físico (região confundida com aparelho).

## Restrições
- Equipe: o autor e no máximo mais uma pessoa. O instrumento da segunda pessoa **ainda não está definido** (SQM, câmera ou celular).
- O tile `h13v11` (lon −50 a −40, lat −30 a −20) já cobre o RJ e o leste de SP, então o piloto não depende da expansão. Locais a menos de 50 km da borda do tile têm contexto incompleto.
- Dados de campo são dados originais do autor; licença a definir por ele.

## Abordagens consideradas
A. **Rede piloto de poucos voluntários treinados, sem plataforma (escolhida).** Quase nenhum custo e já recruta o gradiente.
B. Plataforma aberta com contas, fotos e moderação: custo e risco (LGPD, abuso, viés de seleção) desproporcionais para duas pessoas; fica para depois do piloto.

## O que foi decidido
1. **O SQM é a referência.** Celular e câmera (calibrada ou não) só entram nas estatísticas confirmatórias depois de **calibrados contra o SQM do autor em medições lado a lado**; celular sem calibração nunca é de nível de validação. Sem calibração, o dado é exploratório.
2. Quatro entregas: (a) validador do CSV; (b) proteção contra corte na borda do tile; (c) gerador de locais candidatos estratificados por radiância de satélite; (d) protocolo com níveis de instrumento e calibração cruzada (`instrument_type`, `device_id`).
3. Os limiares de calibração cruzada são **propostas** do projeto, a congelar na pré-especificação antes da coleta.

## Deixado ao construtor
Nomes dos campos extras, formato das mensagens do validador, quantidade de candidatos por estrato. Decisões menores ficam marcadas como escolha do projeto.
