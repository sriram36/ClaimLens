# v1 vs v2 (development, identical inputs and scoring)

- v1 run `71afdfaf-7440-47f6-b523-7dbd9f73287e` (prompt-v1), v2 run `4015a31f-ac86-4d7c-a596-b18ef7f62f48` (prompt-v2)
- provider/model: azure / gpt-5.6-luna; settings v1 `{"deployment": "gpt-5.6-luna", "api_version": "2024-10-21", "provider_timeout_s": 120.0, "max_tokens": 4096, "max_retries": 2, "temperature": null, "max_turns": 3}` v2 `{"deployment": "gpt-5.6-luna", "api_version": "2024-10-21", "provider_timeout_s": 120.0, "max_tokens": 4096, "max_retries": 2, "temperature": null, "max_turns": 3}`

| metric | v1 | v2 | delta |
|---|---|---|---|
| joint F1 (main) | 0.987 | 1.000 | +0.013 |
| joint precision | 0.987 | 1.000 | +0.013 |
| joint recall | 0.987 | 1.000 | +0.013 |
| extraction F1 | 1.000 | 1.000 | +0.000 |
| coverage C/G | 0.987 | 1.000 | +0.013 |

Counts v1: G=376 P=376 M=376 C=371 errors=0
Counts v2: G=376 P=376 M=376 C=376 errors=0

## Fixed by v2 (5)

- `A09:492:655` wrong_label -> correct: For a current India catalogue comparison before shipping, CloudNote Studio is INR 1,500 less expensive than CloudNote Air, with tax included
- `A15:1075:1236` wrong_label -> correct: The built-in Wi-Fi capability of ClearTrail Mini is absent, which should be treated as a separate specification from its ability to receive 
- `A16:455:618` wrong_label -> correct: For a current India catalogue comparison before shipping, CloudNote Studio is INR 1,500 less expensive than CloudNote Air, with tax included
- `A29:454:615` wrong_label -> correct: The built-in Wi-Fi capability of ClearTrail Mini is absent, which should be treated as a separate specification from its ability to receive 
- `A35:1442:1606` wrong_label -> correct: For a current India catalogue comparison before shipping, ClearTrail Plus is INR 1,200 less expensive than ClearTrail Mini, with tax include

## Regressions in v2 (0)

- none

Net claims correct: v1 371 -> v2 376 (+5). A zero or negative delta is a valid measured result; state it as such in the write-up.
