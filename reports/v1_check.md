# Run a13e32da-5dee-40bd-9d37-f68dfc7dc740

- split: **check**  |  agent: **v1** (prompt-v1)  |  status: completed
- provider/model: azure / gpt-5.6-luna
- versions: dataset `long-brand-answers-50-v4`, facts `speaker-catalogue-v4`, evaluator `sentence-spans-and-labels-v4`
- settings: `{"deployment": "gpt-5.6-luna", "api_version": "2024-10-21", "provider_timeout_s": 120.0, "max_tokens": 4096, "max_retries": 2, "temperature": null, "max_turns": 3}`
- source revision: e8cd5f1
- created: 2026-10-19T10:43:47.258723+00:00  |  total 91.6s, mean answer latency 9163 ms
- file hashes: answers.csv=fa28e813ea54, brand_facts.csv=2190d40fad2d, development_gold.csv=afe84cc78f30

## Counts

scheduled 10 | ok 10 | errors 0 | valid-empty 0 | accepted predictions P=94

## Metrics

Quality metrics are **null** for check runs (no ground truth available to the submitter); G, M, C, matched IDs and correctness are null. Reviewer scores the saved predictions with the private key.


## Per-answer outcomes

| answer | status | claims | latency ms | error |
|---|---|---|---|---|
| A41 | ok | 9 | 10482 |  |
| A42 | ok | 10 | 9877 |  |
| A43 | ok | 9 | 8457 |  |
| A44 | ok | 10 | 8633 |  |
| A45 | ok | 9 | 8023 |  |
| A46 | ok | 11 | 9783 |  |
| A47 | ok | 8 | 8807 |  |
| A48 | ok | 10 | 9886 |  |
| A49 | ok | 8 | 7544 |  |
| A50 | ok | 10 | 10141 |  |
