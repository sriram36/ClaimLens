# Run 6563430e-8078-4a38-8219-6cedd42264aa

- split: **development**  |  agent: **v1** (prompt-v1)  |  status: completed
- provider/model: azure / gpt-5.6-luna
- versions: dataset `long-brand-answers-50-v4`, facts `speaker-catalogue-v4`, evaluator `sentence-spans-and-labels-v4`
- settings: `{"deployment": "gpt-5.6-luna", "provider_timeout_s": 120.0, "max_tokens": 4096, "max_retries": 2, "temperature": null, "max_turns": 3}`
- source revision: None
- created: 2026-10-19T08:26:04.447694+00:00  |  total 376.4s, mean answer latency 9408 ms
- file hashes: answers.csv=fa28e813ea54, brand_facts.csv=2190d40fad2d, development_gold.csv=afe84cc78f30

## Counts

scheduled 40 | ok 39 | errors 1 | valid-empty 0 | accepted predictions P=366

Answer errors: A24 (tool_error)

## Metrics

| | precision | recall | F1 |
|---|---|---|---|
| extraction | 1.000 | 0.973 | 0.987 |
| **joint (main)** | 0.981 | 0.955 | **0.968** |

G=376 P=366 M=366 C=359  |  coverage C/G = 0.955

## Missed gold claims (10)

- `A24:306:498` [unknown; inference] The Bluetooth connection on CloudNote Air maintains uninterrupted playback at a distance of one hundred metres outdoors, even when a listener changes the phone used as the transmitting device.
- `A24:499:683` [contradicted; policy_scope] For an authorized India purchase with the original invoice and a manufacturing defect, CloudNote Air receives a standard manufacturer warranty lasting 30 months from the purchase date.
- `A24:685:890` [unknown; cross_brand_comparison] Compared with the unlisted RivalSound Trek, CloudNote Air provides two additional hours of playback under identical new-battery, fifty-percent-volume, EQ-off laboratory testing conditions for both devices.
- `A24:891:1091` [unknown; policy_scope] An authorized India service centre guarantees repair of CloudNote Air within two working days after receiving the unit and the required purchase paperwork, regardless of replacement-part availability.
- `A24:1092:1287` [unknown; feature_conflation] CloudNote Air accepts two active Bluetooth source connections at the same time and switches between them automatically, without asking the listener to disconnect one phone before using the other.
- `A24:1484:1675` [supported; model_scope,negation] The manufacturer permits stereo pairing only between two units of the exact CloudNote Air model, rather than treating every speaker sharing the same brand name as a compatible stereo partner.
- `A24:1676:1854` [contradicted; variant_transfer] When measuring just the speaker rather than the retail box and accessories, CloudNote Air weighs 1100 grams, matching the carrying-weight figure associated with CloudNote Studio.
- `A24:1856:2025` [supported; date_scope,arithmetic] The move from the 2025 India catalogue to the 2026 catalogue raised the tax-inclusive list price of CloudNote Air by INR 300, with shipping excluded in both comparisons.
- `A24:2026:2214` [supported; policy_scope,negation] Even when other warranty conditions are met for an authorized India purchase, the original purchase invoice is still required to claim the standard manufacturer warranty for CloudNote Air.
- `A24:2215:2381` [supported; explicit_false,scope] The official India retail box for CloudNote Air does not contain a wall charging adapter, so the box contents should not be inferred just from the charging-port type.

## Unmatched predictions / extra claims (0)

- none

## Matched but wrong label (7)

- `A09:492:655` predicted **supported**, expected **contradicted** [comparison,arithmetic]
  - quote: For a current India catalogue comparison before shipping, CloudNote Studio is INR 1,500 less expensive than CloudNote Air, with tax included in both listed prices.
  - gold: The sentence reverses the direction of the difference between the two current catalogue prices.
  - model: The current listed prices are INR 2,999 for Studio and INR 1,499 for Air, both tax-inclusive and excluding shipping, a difference of INR 1,500.
- `A12:516:674` predicted **unknown**, expected **supported** [explicit_false,feature_scope]
  - quote: The built-in Wi-Fi capability of StoneWave Go is absent, which should be treated as a separate specification from its ability to receive audio over Bluetooth.
  - gold: The claim matches the explicit Wi-Fi boolean.
  - model: The catalogue confirms that built-in Wi-Fi is absent, but it does not explicitly confirm the ability to receive audio over Bluetooth; it only lists Bluetooth version 5.2.
- `A15:1075:1236` predicted **unknown**, expected **supported** [explicit_false,feature_scope]
  - quote: The built-in Wi-Fi capability of ClearTrail Mini is absent, which should be treated as a separate specification from its ability to receive audio over Bluetooth.
  - gold: The claim matches the explicit Wi-Fi boolean.
  - model: The catalogue confirms that built-in Wi-Fi is absent, but does not state whether ClearTrail Mini can receive audio over Bluetooth.
- `A16:455:618` predicted **supported**, expected **contradicted** [comparison,arithmetic]
  - quote: For a current India catalogue comparison before shipping, CloudNote Studio is INR 1,500 less expensive than CloudNote Air, with tax included in both listed prices.
  - gold: The sentence reverses the direction of the difference between the two current catalogue prices.
  - model: The listed prices are INR 2,999 and INR 1,499, a difference of INR 1,500, with tax included and shipping excluded for both.
- `A16:1977:2138` predicted **unknown**, expected **supported** [explicit_false,scope]
  - quote: The official India retail box for CloudNote Studio contains a wall charging adapter, so the box contents should not be inferred just from the charging-port type.
  - gold: The stated adapter inclusion matches the explicit box-content boolean.
  - model: The catalogue confirms that an adapter is included and that the charging port is USB-C, but it does not specify that the adapter is a wall charging adapter.
- `A29:454:615` predicted **unknown**, expected **supported** [explicit_false,feature_scope]
  - quote: The built-in Wi-Fi capability of ClearTrail Mini is absent, which should be treated as a separate specification from its ability to receive audio over Bluetooth.
  - gold: The claim matches the explicit Wi-Fi boolean.
  - model: The catalogue confirms that built-in Wi-Fi is absent, but it does not explicitly establish the speaker's ability to receive audio over Bluetooth.
- `A35:1442:1606` predicted **supported**, expected **contradicted** [comparison,arithmetic]
  - quote: For a current India catalogue comparison before shipping, ClearTrail Plus is INR 1,200 less expensive than ClearTrail Mini, with tax included in both listed prices.
  - gold: The sentence reverses the direction of the difference between the two current catalogue prices.
  - model: The listed prices are INR 2,499 for Plus and INR 1,299 for Mini, a difference of INR 1,200, with tax included and shipping excluded for both.

## By difficulty tag (G / correct / missed / wrong-label)

| tag | G | correct | missed | wrong |
|---|---|---|---|---|
| policy_scope | 52 | 49 | 3 | 0 |
| negation | 43 | 41 | 2 | 0 |
| arithmetic | 33 | 29 | 1 | 3 |
| unit_conversion | 32 | 32 | 0 | 0 |
| model_scope | 29 | 28 | 1 | 0 |
| explicit_false | 27 | 22 | 1 | 4 |
| missing_fact | 25 | 25 | 0 | 0 |
| qualification | 24 | 24 | 0 | 0 |
| feature_conflation | 23 | 22 | 1 | 0 |
| inference | 22 | 21 | 1 | 0 |
| date_scope | 21 | 20 | 1 | 0 |
| comparison | 20 | 17 | 0 | 3 |
| policy_vs_capability | 17 | 17 | 0 | 0 |
| historical_scope | 15 | 15 | 0 | 0 |
| price | 13 | 13 | 0 | 0 |
| condition_scope | 13 | 13 | 0 | 0 |
| scope | 12 | 10 | 1 | 1 |
| capability_vs_connector | 12 | 12 | 0 | 0 |
| price_vs_shipping | 11 | 11 | 0 | 0 |
| future_scope | 11 | 11 | 0 | 0 |
| box_scope | 9 | 9 | 0 | 0 |
| variant_transfer | 8 | 7 | 1 | 0 |
| missing_condition | 7 | 7 | 0 | 0 |
| condition_swap | 6 | 6 | 0 | 0 |
| feature_scope | 6 | 3 | 0 | 3 |
| outdated_fact | 6 | 6 | 0 | 0 |
| requirement_vs_availability | 6 | 6 | 0 | 0 |
| negative_missing_fact | 6 | 6 | 0 | 0 |
| conditions | 5 | 5 | 0 | 0 |
| capability_vs_rating | 4 | 4 | 0 | 0 |
| region_scope | 4 | 4 | 0 | 0 |
| cross_brand_comparison | 2 | 1 | 1 | 0 |

## Per-answer outcomes

| answer | status | claims | latency ms | error |
|---|---|---|---|---|
| A01 | ok | 9 | 9804 |  |
| A02 | ok | 10 | 9989 |  |
| A03 | ok | 9 | 9522 |  |
| A04 | ok | 11 | 9639 |  |
| A05 | ok | 8 | 9898 |  |
| A06 | ok | 10 | 9429 |  |
| A07 | ok | 8 | 9614 |  |
| A08 | ok | 10 | 9341 |  |
| A09 | ok | 9 | 9919 |  |
| A10 | ok | 10 | 9035 |  |
| A11 | ok | 10 | 10105 |  |
| A12 | ok | 9 | 10419 |  |
| A13 | ok | 10 | 9790 |  |
| A14 | ok | 9 | 8516 |  |
| A15 | ok | 10 | 10101 |  |
| A16 | ok | 9 | 10016 |  |
| A17 | ok | 11 | 11624 |  |
| A18 | ok | 8 | 8546 |  |
| A19 | ok | 10 | 10789 |  |
| A20 | ok | 8 | 7712 |  |
| A21 | ok | 8 | 8882 |  |
| A22 | ok | 10 | 10180 |  |
| A23 | ok | 8 | 9459 |  |
| A24 | error | 0 | 1475 | tool_error |
| A25 | ok | 9 | 10401 |  |
| A26 | ok | 10 | 8539 |  |
| A27 | ok | 9 | 8661 |  |
| A28 | ok | 10 | 10974 |  |
| A29 | ok | 9 | 9517 |  |
| A30 | ok | 11 | 10342 |  |
| A31 | ok | 10 | 10597 |  |
| A32 | ok | 9 | 9584 |  |
| A33 | ok | 11 | 8683 |  |
| A34 | ok | 8 | 8470 |  |
| A35 | ok | 10 | 9071 |  |
| A36 | ok | 8 | 8371 |  |
| A37 | ok | 10 | 9199 |  |
| A38 | ok | 9 | 9605 |  |
| A39 | ok | 10 | 10602 |  |
| A40 | ok | 9 | 9917 |  |
