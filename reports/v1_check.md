# Run d4190397-5ff6-44f1-89ec-0fbc9292475d

- split: **check**  |  agent: **v1** (prompt-v1)  |  status: completed
- provider/model: azure / gpt-5.6-luna
- versions: dataset `long-brand-answers-50-v4`, facts `speaker-catalogue-v4`, evaluator `sentence-spans-and-labels-v4`
- settings: `{"deployment": "gpt-5.6-luna", "provider_timeout_s": 120.0, "max_tokens": 4096, "max_retries": 2, "temperature": null, "max_turns": 3}`
- source revision: None
- created: 2026-10-19T08:43:21.556658+00:00  |  total 104.2s, mean answer latency 10418 ms
- file hashes: answers.csv=fa28e813ea54, brand_facts.csv=2190d40fad2d, development_gold.csv=afe84cc78f30

## Counts

scheduled 10 | ok 10 | errors 0 | valid-empty 0 | accepted predictions P=94

## Metrics

Quality metrics are **null** for check runs (no ground truth available to the submitter); G, M, C, matched IDs and correctness are null. Reviewer scores the saved predictions with the private key.


## Per-answer outcomes

| answer | status | claims | latency ms | error |
|---|---|---|---|---|
| A41 | ok | 9 | 10487 |  |
| A42 | ok | 10 | 12150 |  |
| A43 | ok | 9 | 8675 |  |
| A44 | ok | 10 | 11126 |  |
| A45 | ok | 9 | 8483 |  |
| A46 | ok | 11 | 10922 |  |
| A47 | ok | 8 | 8775 |  |
| A48 | ok | 10 | 13683 |  |
| A49 | ok | 8 | 9133 |  |
| A50 | ok | 10 | 10750 |  |
