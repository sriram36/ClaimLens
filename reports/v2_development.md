# Run d5db841b-e639-4c02-ae8c-4657cbd3412f

- split: **development**  |  agent: **v2** (prompt-v2)  |  status: completed
- provider/model: azure / gpt-5.6-luna
- versions: dataset `long-brand-answers-50-v4`, facts `speaker-catalogue-v4`, evaluator `sentence-spans-and-labels-v4`
- settings: `{"deployment": "gpt-5.6-luna", "provider_timeout_s": 120.0, "max_tokens": 4096, "max_retries": 2, "temperature": null, "max_turns": 3}`
- source revision: None
- created: 2026-10-19T08:35:51.567186+00:00  |  total 372.5s, mean answer latency 9310 ms
- file hashes: answers.csv=fa28e813ea54, brand_facts.csv=2190d40fad2d, development_gold.csv=afe84cc78f30

## Counts

scheduled 40 | ok 40 | errors 0 | valid-empty 0 | accepted predictions P=376

## Metrics

| | precision | recall | F1 |
|---|---|---|---|
| extraction | 1.000 | 1.000 | 1.000 |
| **joint (main)** | 1.000 | 1.000 | **1.000** |

G=376 P=376 M=376 C=376  |  coverage C/G = 1.000

## Missed gold claims (0)

- none

## Unmatched predictions / extra claims (0)

- none

## Matched but wrong label (0)

- none

## By difficulty tag (G / correct / missed / wrong-label)

| tag | G | correct | missed | wrong |
|---|---|---|---|---|
| policy_scope | 52 | 52 | 0 | 0 |
| negation | 43 | 43 | 0 | 0 |
| arithmetic | 33 | 33 | 0 | 0 |
| unit_conversion | 32 | 32 | 0 | 0 |
| model_scope | 29 | 29 | 0 | 0 |
| explicit_false | 27 | 27 | 0 | 0 |
| missing_fact | 25 | 25 | 0 | 0 |
| qualification | 24 | 24 | 0 | 0 |
| feature_conflation | 23 | 23 | 0 | 0 |
| inference | 22 | 22 | 0 | 0 |
| date_scope | 21 | 21 | 0 | 0 |
| comparison | 20 | 20 | 0 | 0 |
| policy_vs_capability | 17 | 17 | 0 | 0 |
| historical_scope | 15 | 15 | 0 | 0 |
| price | 13 | 13 | 0 | 0 |
| condition_scope | 13 | 13 | 0 | 0 |
| scope | 12 | 12 | 0 | 0 |
| capability_vs_connector | 12 | 12 | 0 | 0 |
| price_vs_shipping | 11 | 11 | 0 | 0 |
| future_scope | 11 | 11 | 0 | 0 |
| box_scope | 9 | 9 | 0 | 0 |
| variant_transfer | 8 | 8 | 0 | 0 |
| missing_condition | 7 | 7 | 0 | 0 |
| condition_swap | 6 | 6 | 0 | 0 |
| feature_scope | 6 | 6 | 0 | 0 |
| outdated_fact | 6 | 6 | 0 | 0 |
| requirement_vs_availability | 6 | 6 | 0 | 0 |
| negative_missing_fact | 6 | 6 | 0 | 0 |
| conditions | 5 | 5 | 0 | 0 |
| capability_vs_rating | 4 | 4 | 0 | 0 |
| region_scope | 4 | 4 | 0 | 0 |
| cross_brand_comparison | 2 | 2 | 0 | 0 |

## Per-answer outcomes

| answer | status | claims | latency ms | error |
|---|---|---|---|---|
| A01 | ok | 9 | 10987 |  |
| A02 | ok | 10 | 10937 |  |
| A03 | ok | 9 | 8587 |  |
| A04 | ok | 11 | 10194 |  |
| A05 | ok | 8 | 10710 |  |
| A06 | ok | 10 | 10554 |  |
| A07 | ok | 8 | 11094 |  |
| A08 | ok | 10 | 7763 |  |
| A09 | ok | 9 | 9098 |  |
| A10 | ok | 10 | 7717 |  |
| A11 | ok | 10 | 10006 |  |
| A12 | ok | 9 | 8715 |  |
| A13 | ok | 10 | 9435 |  |
| A14 | ok | 9 | 9562 |  |
| A15 | ok | 10 | 8457 |  |
| A16 | ok | 9 | 10405 |  |
| A17 | ok | 11 | 11059 |  |
| A18 | ok | 8 | 9463 |  |
| A19 | ok | 10 | 10592 |  |
| A20 | ok | 8 | 7338 |  |
| A21 | ok | 8 | 6700 |  |
| A22 | ok | 10 | 10987 |  |
| A23 | ok | 8 | 8734 |  |
| A24 | ok | 10 | 10297 |  |
| A25 | ok | 9 | 9339 |  |
| A26 | ok | 10 | 8621 |  |
| A27 | ok | 9 | 8523 |  |
| A28 | ok | 10 | 9639 |  |
| A29 | ok | 9 | 6984 |  |
| A30 | ok | 11 | 10099 |  |
| A31 | ok | 10 | 9950 |  |
| A32 | ok | 9 | 8262 |  |
| A33 | ok | 11 | 9046 |  |
| A34 | ok | 8 | 7680 |  |
| A35 | ok | 10 | 9669 |  |
| A36 | ok | 8 | 10172 |  |
| A37 | ok | 10 | 9386 |  |
| A38 | ok | 9 | 8928 |  |
| A39 | ok | 10 | 8452 |  |
| A40 | ok | 9 | 8267 |  |
