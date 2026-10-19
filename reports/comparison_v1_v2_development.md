# v1 vs v2 (development, identical inputs and scoring)

- v1 run `6563430e-8078-4a38-8219-6cedd42264aa` (prompt-v1), v2 run `d5db841b-e639-4c02-ae8c-4657cbd3412f` (prompt-v2)
- provider/model: azure / gpt-5.6-luna; settings v1 `{"deployment": "gpt-5.6-luna", "provider_timeout_s": 120.0, "max_tokens": 4096, "max_retries": 2, "temperature": null, "max_turns": 3}` v2 `{"deployment": "gpt-5.6-luna", "provider_timeout_s": 120.0, "max_tokens": 4096, "max_retries": 2, "temperature": null, "max_turns": 3}`

| metric | v1 | v2 | delta |
|---|---|---|---|
| joint F1 (main) | 0.968 | 1.000 | +0.032 |
| joint precision | 0.981 | 1.000 | +0.019 |
| joint recall | 0.955 | 1.000 | +0.045 |
| extraction F1 | 0.987 | 1.000 | +0.013 |
| coverage C/G | 0.955 | 1.000 | +0.045 |

Counts v1: G=376 P=366 M=366 C=359 errors=1
Counts v2: G=376 P=376 M=376 C=376 errors=0

## Fixed by v2 (17)

- `A09:492:655` wrong_label -> correct: For a current India catalogue comparison before shipping, CloudNote Studio is INR 1,500 less expensive than CloudNote Air, with tax included
- `A12:516:674` wrong_label -> correct: The built-in Wi-Fi capability of StoneWave Go is absent, which should be treated as a separate specification from its ability to receive aud
- `A15:1075:1236` wrong_label -> correct: The built-in Wi-Fi capability of ClearTrail Mini is absent, which should be treated as a separate specification from its ability to receive 
- `A16:455:618` wrong_label -> correct: For a current India catalogue comparison before shipping, CloudNote Studio is INR 1,500 less expensive than CloudNote Air, with tax included
- `A16:1977:2138` wrong_label -> correct: The official India retail box for CloudNote Studio contains a wall charging adapter, so the box contents should not be inferred just from th
- `A24:306:498` missed -> correct: The Bluetooth connection on CloudNote Air maintains uninterrupted playback at a distance of one hundred metres outdoors, even when a listene
- `A24:499:683` missed -> correct: For an authorized India purchase with the original invoice and a manufacturing defect, CloudNote Air receives a standard manufacturer warran
- `A24:685:890` missed -> correct: Compared with the unlisted RivalSound Trek, CloudNote Air provides two additional hours of playback under identical new-battery, fifty-perce
- `A24:891:1091` missed -> correct: An authorized India service centre guarantees repair of CloudNote Air within two working days after receiving the unit and the required purc
- `A24:1092:1287` missed -> correct: CloudNote Air accepts two active Bluetooth source connections at the same time and switches between them automatically, without asking the l
- `A24:1484:1675` missed -> correct: The manufacturer permits stereo pairing only between two units of the exact CloudNote Air model, rather than treating every speaker sharing 
- `A24:1676:1854` missed -> correct: When measuring just the speaker rather than the retail box and accessories, CloudNote Air weighs 1100 grams, matching the carrying-weight fi
- `A24:1856:2025` missed -> correct: The move from the 2025 India catalogue to the 2026 catalogue raised the tax-inclusive list price of CloudNote Air by INR 300, with shipping 
- `A24:2026:2214` missed -> correct: Even when other warranty conditions are met for an authorized India purchase, the original purchase invoice is still required to claim the s
- `A24:2215:2381` missed -> correct: The official India retail box for CloudNote Air does not contain a wall charging adapter, so the box contents should not be inferred just fr
- `A29:454:615` wrong_label -> correct: The built-in Wi-Fi capability of ClearTrail Mini is absent, which should be treated as a separate specification from its ability to receive 
- `A35:1442:1606` wrong_label -> correct: For a current India catalogue comparison before shipping, ClearTrail Plus is INR 1,200 less expensive than ClearTrail Mini, with tax include

## Regressions in v2 (0)

- none

Net claims correct: v1 359 -> v2 376 (+17). A zero or negative delta is a valid measured result; state it as such in the write-up.
