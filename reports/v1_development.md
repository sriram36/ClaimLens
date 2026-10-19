# Run 71afdfaf-7440-47f6-b523-7dbd9f73287e

- split: **development**  |  agent: **v1** (prompt-v1)  |  status: completed
- provider/model: azure / gpt-5.6-luna
- versions: dataset `long-brand-answers-50-v4`, facts `speaker-catalogue-v4`, evaluator `sentence-spans-and-labels-v4`
- settings: `{"deployment": "gpt-5.6-luna", "api_version": "2024-10-21", "provider_timeout_s": 120.0, "max_tokens": 4096, "max_retries": 2, "temperature": null, "max_turns": 3}`
- source revision: e8cd5f1
- created: 2026-10-19T10:11:52.076217+00:00  |  total 360.5s, mean answer latency 9010 ms
- file hashes: answers.csv=fa28e813ea54, brand_facts.csv=2190d40fad2d, development_gold.csv=afe84cc78f30

## Counts

scheduled 40 | ok 40 | errors 0 | valid-empty 0 | accepted predictions P=376

## Metrics

| | precision | recall | F1 |
|---|---|---|---|
| extraction | 1.000 | 1.000 | 1.000 |
| **joint (main)** | 0.987 | 0.987 | **0.987** |

G=376 P=376 M=376 C=371  |  coverage C/G = 0.987

## Missed gold claims (0)

- none

## Unmatched predictions / extra claims (0)

- none

## Matched but wrong label (5)

- `A09:492:655` predicted **supported**, expected **contradicted** [comparison,arithmetic]
  - quote: For a current India catalogue comparison before shipping, CloudNote Studio is INR 1,500 less expensive than CloudNote Air, with tax included in both listed prices.
  - gold: The sentence reverses the direction of the difference between the two current catalogue prices.
  - model: The 2026 India prices are INR 2,999 for Studio and INR 1,499 for Air, both tax-inclusive and excluding shipping, a difference of INR 1,500.
- `A15:1075:1236` predicted **unknown**, expected **supported** [explicit_false,feature_scope]
  - quote: The built-in Wi-Fi capability of ClearTrail Mini is absent, which should be treated as a separate specification from its ability to receive audio over Bluetooth.
  - gold: The claim matches the explicit Wi-Fi boolean.
  - model: The catalogue confirms that built-in Wi-Fi is absent, but it does not explicitly confirm the claimed Bluetooth audio-reception capability.
- `A16:455:618` predicted **supported**, expected **contradicted** [comparison,arithmetic]
  - quote: For a current India catalogue comparison before shipping, CloudNote Studio is INR 1,500 less expensive than CloudNote Air, with tax included in both listed prices.
  - gold: The sentence reverses the direction of the difference between the two current catalogue prices.
  - model: CloudNote Studio is INR 2,999 and CloudNote Air is INR 1,499, both tax-inclusive with shipping excluded, so the difference is INR 1,500.
- `A29:454:615` predicted **unknown**, expected **supported** [explicit_false,feature_scope]
  - quote: The built-in Wi-Fi capability of ClearTrail Mini is absent, which should be treated as a separate specification from its ability to receive audio over Bluetooth.
  - gold: The claim matches the explicit Wi-Fi boolean.
  - model: The catalogue confirms that built-in Wi-Fi is absent, but does not provide enough information to verify the Bluetooth audio-reception claim.
- `A35:1442:1606` predicted **supported**, expected **contradicted** [comparison,arithmetic]
  - quote: For a current India catalogue comparison before shipping, ClearTrail Plus is INR 1,200 less expensive than ClearTrail Mini, with tax included in both listed prices.
  - gold: The sentence reverses the direction of the difference between the two current catalogue prices.
  - model: The listed prices are INR 2,499 for Plus and INR 1,299 for Mini, both tax included and excluding shipping, a difference of INR 1,200.

## By difficulty tag (G / correct / missed / wrong-label)

| tag | G | correct | missed | wrong |
|---|---|---|---|---|
| policy_scope | 52 | 52 | 0 | 0 |
| negation | 43 | 43 | 0 | 0 |
| arithmetic | 33 | 30 | 0 | 3 |
| unit_conversion | 32 | 32 | 0 | 0 |
| model_scope | 29 | 29 | 0 | 0 |
| explicit_false | 27 | 25 | 0 | 2 |
| missing_fact | 25 | 25 | 0 | 0 |
| qualification | 24 | 24 | 0 | 0 |
| feature_conflation | 23 | 23 | 0 | 0 |
| inference | 22 | 22 | 0 | 0 |
| date_scope | 21 | 21 | 0 | 0 |
| comparison | 20 | 17 | 0 | 3 |
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
| feature_scope | 6 | 4 | 0 | 2 |
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
| A01 | ok | 9 | 9895 |  |
| A02 | ok | 10 | 10656 |  |
| A03 | ok | 9 | 8034 |  |
| A04 | ok | 11 | 9446 |  |
| A05 | ok | 8 | 8471 |  |
| A06 | ok | 10 | 10282 |  |
| A07 | ok | 8 | 9100 |  |
| A08 | ok | 10 | 7842 |  |
| A09 | ok | 9 | 8901 |  |
| A10 | ok | 10 | 8692 |  |
| A11 | ok | 10 | 9831 |  |
| A12 | ok | 9 | 9469 |  |
| A13 | ok | 10 | 9529 |  |
| A14 | ok | 9 | 9417 |  |
| A15 | ok | 10 | 10328 |  |
| A16 | ok | 9 | 8328 |  |
| A17 | ok | 11 | 10122 |  |
| A18 | ok | 8 | 8121 |  |
| A19 | ok | 10 | 8322 |  |
| A20 | ok | 8 | 7743 |  |
| A21 | ok | 8 | 7553 |  |
| A22 | ok | 10 | 8720 |  |
| A23 | ok | 8 | 7577 |  |
| A24 | ok | 10 | 11012 |  |
| A25 | ok | 9 | 8336 |  |
| A26 | ok | 10 | 9596 |  |
| A27 | ok | 9 | 11924 |  |
| A28 | ok | 10 | 9133 |  |
| A29 | ok | 9 | 8875 |  |
| A30 | ok | 11 | 8417 |  |
| A31 | ok | 10 | 9770 |  |
| A32 | ok | 9 | 7226 |  |
| A33 | ok | 11 | 7671 |  |
| A34 | ok | 8 | 9367 |  |
| A35 | ok | 10 | 8144 |  |
| A36 | ok | 8 | 9030 |  |
| A37 | ok | 10 | 9713 |  |
| A38 | ok | 9 | 8093 |  |
| A39 | ok | 10 | 9584 |  |
| A40 | ok | 9 | 8143 |  |
