# Ordem de implementação — Fase 1

Guia de execução do `PHASE_1.md`: **em que ordem** preencher os TODOs e **qual a função**
de cada peça. Os arquivos já estão esqueletados com assinaturas e docstrings; este
documento é o roteiro para preencher os corpos.

Dependência resumida:

```
properties → merchants → perfis → normal → 4 padrões → orquestrador → CLI → notebook
```

Cada bloco termina com um checkpoint visual. Não avance sem ele — a Fase 1 é a fundação, e
dado ruim aqui contamina as Fases 2, 3 e 4 silenciosamente.

---

## Decisão que vem antes de tudo

O mapeamento `merchant_id` → `merchant_category` precisa ser o mesmo em todo lugar:
`normal.py` preenche a categoria da transação, `fraud.py` sorteia merchants do pool global.

**Recomendação:** constante de módulo em [`src/generator/profile.py`](../src/generator/profile.py):

```python
MERCHANT_CATEGORIES: dict[str, str]   # merchant_id -> categoria, construído no import
ALL_MERCHANT_IDS: list[str]           # o pool global
```

Os outros módulos só importam. Zero threading de parâmetro, zero risco de um merchant mudar
de categoria entre camadas.

---

## Bloco A — Perfis (base de tudo)

### 1. `UserProfile.baseline_amount_mean` / `baseline_amount_std`

[`profile.py:49-67`](../src/generator/profile.py#L49-L67) — duas linhas de matemática cada.

**Função:** dar à camada de fraude uma referência de "o que é normal para *este* usuário"
sem varrer o histórico gerado. `inject_amount_anomaly` e `inject_card_testing` dependem
disso. Fazer primeiro porque é trivial e desbloqueia o Bloco C.

Fórmulas (já nas docstrings):

- média: `exp(mu + sigma**2 / 2)`
- desvio: `sqrt((exp(sigma**2) - 1) * exp(2*mu + sigma**2))`

### 2. Universo de merchants

Construído **uma vez**, antes do loop de `generate_user_profiles`. ~200 ids (`m_00000`…),
cada um com uma categoria fixa sorteada da lista (grocery, fuel, restaurant, online,
travel, electronics, pharmacy).

**Função:** define o que significa "merchant desconhecido". Se cada usuário tivesse seu
próprio pool, "desconhecido" perderia sentido — todo merchant seria novo para todo mundo.

### 3. Loop de perfis

[`profile.py:97-119`](../src/generator/profile.py#L97-L119). Siga os valores sugeridos nos
comentários. Função de cada campo:

| Campo | Por que existe |
|---|---|
| `home_lat/long` | Região apertada (ex.: São Paulo) dá escala sã para "distância de casa" e faz o salto geo-impossível saltar aos olhos. |
| `geo_jitter_std` | Per-user: alguns usuários circulam mais que outros. Sem isso, distância vira um limiar único global. |
| `amount_mu` / `amount_sigma` | É o que torna anomalia de valor **relativa** ao usuário. `sigma` grande = cauda pesada = tarefa mais difícil. |
| `active_hours` | Variando por usuário. Se todos dormissem no mesmo horário, hora-do-dia viraria regra determinística e o modelo só memorizaria. |
| `familiar_merchants` | 5–15, sem reposição. Base do sinal fraco "merchant novo". |

Use ids determinísticos (`f"u_{i:05d}"`), **nunca `uuid4`** — uuid4 ignora a seed e quebra
o contrato de reprodutibilidade.

> **Checkpoint:** rode `generate_user_profiles(5)` e olhe os perfis. Rode duas vezes e
> compare — tem que ser idêntico.

---

## Bloco B — Camada normal

### 4. `generate_normal_transactions`

[`normal.py:56-101`](../src/generator/normal.py#L56-L101). Ordem dentro do loop:
usuário → amount → timestamp → localização → merchant → id.

**As válvulas de escape são a parte que a maioria erra.** Cada uma existe para impedir que
o modelo aprenda uma regra determinística em vez de comportamento:

- **~2–5% off-hours** — sem isso, `hour ∉ active_hours` seria um separador perfeito e
  artificial.
- **~5% viagem** (jitter ~20x) — sem isso, "distância de casa" separa fraude com uma linha
  reta e o modelo nunca aprende **velocidade**. É exatamente o que diferencia viagem
  legítima de geo-velocity impossível.
- **Piso de ~1.0 no amount** — valores minúsculos são o sinal de card-testing. Se a camada
  normal emitir R$ 0,40, o padrão de fraude vira ruído.
- **~10% merchant fora do familiar** — merchant novo é sinal *fraco*, não prova.

O `sort` no final não é cosmético: injeção de fraude, features de velocidade e split
temporal todos assumem stream cronológico.

> **Checkpoint (antes de escrever qualquer fraude):**
> - histograma de `amount` → cauda longa à direita;
> - histograma de hora-do-dia → vale de madrugada, **não** zero;
> - scatter lat/long → nuvem densa + pontos esparsos de viagem.
>
> Se algum estiver feio, pare e conserte. Todo o resto do projeto herda o defeito.

---

## Bloco C — Camada de fraude

Ordem por complexidade crescente. Os quatro padrões são **independentes** de propósito: na
Fase 4 você desloca os parâmetros de um sem tocar nos outros, para simular concept drift.

### 5. `inject_amount_anomaly` — 1 transação, sem geometria

[`fraud.py:104`](../src/generator/fraud.py#L104). Só usa as properties do passo 1. Comece
por aqui.

### 6. `inject_geo_velocity` — 1 transação, com trigonometria

[`fraud.py:65`](../src/generator/fraud.py#L65). Bearing aleatório em `[0, 2π)`, converte km
→ graus (`~111 km` por grau de latitude; `111 * cos(lat)` por grau de longitude).

**Função:** é o único padrão detectável apenas *em relação à transação anterior*. Ele
existe para justificar a feature `distância ÷ tempo` da Fase 2.

### 7. `inject_burst` — N transações

[`fraud.py:28`](../src/generator/fraud.py#L28). O `amount_scale=1.0` padrão é intencional:
os valores são **normais**. O sinal é taxa pura — e é ele que valida os contadores de
1 min / 10 min.

Localização perto da **âncora**, não de casa: o atacante está noutro lugar.

### 8. `inject_card_testing` — N+1 transações

[`fraud.py:136`](../src/generator/fraud.py#L136). Sondas minúsculas → payoff grande. O sinal
é a **sequência**, não uma transação isolada. Mantenha o `probe_amount_max` abaixo do piso
da camada normal.

### 9. `inject_fraud` — orquestrador

[`fraud.py:175`](../src/generator/fraud.py#L175). Só cola; nenhuma lógica de padrão aqui.

Três armadilhas:

1. **Budget:** `n * r / (1 - r)`, não `n * r`. O denominador cresce conforme você injeta.
2. **Contar linhas, não chamadas:** burst devolve 8, amount devolve 1.
3. **Âncora do geo:** não use a última transação do usuário, senão o salto cai fora da
   janela temporal gerada.

Guarde os pesos (`{"burst": .3, "geo": .25, "amount": .25, "card_testing": .2}`) como dict
de módulo — a Fase 4 vai deslocá-los.

Prefixe os ids injetados (`f_...`) para não colidir com a camada normal.

> **Checkpoint:** `python -m src.generator.generate --n-users 100 --n-transactions 5000`
> A linha `fraud: X rows (Y%), target Z%` tem que bater.
> [`generate.py`](../src/generator/generate.py) já está pronto — não mexa.

---

## Bloco D — Notebook (`notebooks/01_baseline.ipynb`)

### 10. Carregar + validar

Não pule. Confirme visualmente que fraude *parece* fraude antes de treinar qualquer coisa.

### 11. Features de velocidade

Por card, ordenado por tempo, **só passado**. Use `groupby("card_id")` + `rolling(...)` /
`shift()` — nunca uma agregação que enxergue a linha atual ou futuras. Esta é a fonte nº 1
de métrica inflada e falsa (look-ahead bias).

As quatro do `PHASE_1.md`:

- contadores de transações do card em 1 min / 10 min / 1 h;
- distância desde a transação anterior ÷ tempo decorrido;
- z-score do valor vs. média/desvio móveis do card;
- merchant novo para aquele card.

### 12. Split temporal + LightGBM

Corte por timestamp (ex.: primeiros 80% dos dias treinam, resto testa) — **nunca split
aleatório**. `scale_pos_weight` para o desbalanceamento. Nada de deep learning, nada de
tuning pesado: um baseline sólido basta; guarde energia para a Fase 2.

### 13. Avaliar

PR-AUC, precision, recall, matriz de confusão. **Accuracy é inútil a 0,3%** — um modelo que
sempre diz "não é fraude" acerta 99,7%.

Feature importance é o teste de sanidade: as features de velocidade têm que estar no topo.
Se não estiverem, o passo 11 está errado.
