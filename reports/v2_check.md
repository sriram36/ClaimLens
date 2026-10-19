# Run 68c9022f-f6f2-4fa8-b63d-8d1f63a18a05

- split: **check**  |  agent: **v2** (prompt-v2)  |  status: completed
- provider/model: azure / gpt-5.6-luna
- versions: dataset `long-brand-answers-50-v4`, facts `speaker-catalogue-v4`, evaluator `sentence-spans-and-labels-v4`
- settings: `{"deployment": "gpt-5.6-luna", "provider_timeout_s": 120.0, "max_tokens": 4096, "max_retries": 2, "temperature": null, "max_turns": 3}`
- source revision: None
- created: 2026-10-19T08:45:44.263732+00:00  |  total 94.0s, mean answer latency 9402 ms
- file hashes: answers.csv=fa28e813ea54, brand_facts.csv=2190d40fad2d, development_gold.csv=afe84cc78f30

## Counts

scheduled 10 | ok 10 | errors 0 | valid-empty 0 | accepted predictions P=94

## Metrics

Quality metrics are **null** for check runs (no ground truth available to the submitter); G, M, C, matched IDs and correctness are null. Reviewer scores the saved predictions with the private key.


## Per-answer outcomes

| answer | status | claims | latency ms | error |
|---|---|---|---|---|
| A41 | ok | 9 | 10804 |  |
| A42 | ok | 10 | 11152 |  |
| A43 | ok | 9 | 8315 |  |
| A44 | ok | 10 | 9366 |  |
| A45 | ok | 9 | 8418 |  |
| A46 | ok | 11 | 10151 |  |
| A47 | ok | 8 | 8499 |  |
| A48 | ok | 10 | 9299 |  |
| A49 | ok | 8 | 8846 |  |
| A50 | ok | 10 | 9175 |  |
