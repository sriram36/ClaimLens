# Write-up: ClaimLens Assessment & Empirical Evaluation

## Results (development, A01-A40, G=376)

| Metric | v1 (Baseline) | v2 (Refined Prompt) | Delta |
|---|---|---|---|
| **joint F1 (main)** | 0.968 | **1.000** | +0.032 |
| **extraction F1** | 0.987 | **1.000** | +0.013 |
| **joint precision** | 0.981 | **1.000** | +0.019 |
| **joint recall** | 0.955 | **1.000** | +0.045 |
| **G / P / M / C** | 376 / 366 / 366 / 359 | **376 / 376 / 376 / 376** | +17 correct |
| **answer errors** | 1 (`A24`) | **0** | -1 |

Check runs (A41-A50): predictions and errors saved, quality null as required.
- **v1 check**: P=94, errors=0
- **v2 check**: P=94, errors=0

---

## Diagnosis of v1 failures

After completing the full v1 development run (`6563430e-8078-4a38-8219-6cedd42264aa`), I inspected `reports/v1_development.md` to identify why 17 claims fell short of gold:

1. **Tool Invocation on Unlisted Competitors (1 answer error, 10 missed claims)**:
   - In `A24`, the text mentioned *"Compared with the unlisted RivalSound Trek, CloudNote Air provides two additional hours of playback..."*.
   - The model attempted to call `get_brand_facts(brand_id="rivalsound")`. Because `rivalsound` is not a registered catalogue brand (`cleartrail`, `cloudnote`, `stonewave`), the catalogue raised `UnknownBrand`, which bubbled up as a fatal `tool_error` for the answer. This single crash resulted in 10 missed gold claims in one blow.

2. **Comparison Direction Inversion (3 wrong-label claims)**:
   - In `A09:492:655`, `A16:455:618`, and `A35:1442:1606`:
     - *Claim*: "CloudNote Studio is INR 1,500 less expensive than CloudNote Air, with tax included in both listed prices."
     - *Facts*: CloudNote Studio is ₹2,999 and CloudNote Air is ₹1,499. The numerical difference is indeed ₹1,500.
     - *Error*: The model verified $|2999 - 1499| = 1500$ and labeled the claim `supported`, failing to notice that Studio is *more* expensive than Air, so claiming it is *less* expensive is `contradicted`.

3. **Compound Qualifying Clauses Masking Core Booleans (3 wrong-label claims)**:
   - In `A12:516:674`, `A15:1075:1236`, and `A29:454:615`:
     - *Claim*: "The built-in Wi-Fi capability of ClearTrail Mini is absent, which should be treated as a separate specification from its ability to receive audio over Bluetooth."
     - *Facts*: The catalogue clearly lists `wi_fi: false / no`.
     - *Error*: The model correctly saw that Wi-Fi was absent, but marked the claim `unknown` because it assumed the trailing conversational advice ("which should be treated as a separate specification...") was an unverified factual assertion.

4. **Specific Box Inclusion Terminology (1 wrong-label claim)**:
   - In `A16:1977:2138`:
     - *Claim*: "The official India retail box for CloudNote Studio contains a wall charging adapter..."
     - *Facts*: Catalogue lists `adapter: yes`.
     - *Error*: The model marked `unknown` because the catalogue entry said "adapter" rather than specifically "wall charging adapter".

---

## The one change (v2) and its measured effect

### What Changed in `prompts/v2.md`
Rather than changing code or introducing heuristics, I refined the system prompt `prompts/v2.md` with a structured verification checklist targeted directly at these observed failure modes:
1. **Strict Brand Lookup Boundaries**: Explicitly instructed the model that `get_brand_facts` must **only** be called for known brands (`{brand_ids}`). Unlisted competitor brands mentioned in comparisons (like RivalSound) must never be queried and claims asserting specs about them must default to `unknown`.
2. **Comparison Direction Verification**: Explicitly mandated checking both the arithmetic difference **and the directionality** of comparative claims (e.g., verifying if the subject is actually less or more expensive).
3. **Core Feature vs. Qualifying Context**: Instructed the model that when a claim asserts that a feature is absent/present alongside conversational qualification or advice, the core assertion should be matched against the catalogue boolean.
4. **Box Contents Rule**: Confirmed that catalogue adapter inclusion supports wall charging adapter claims.

### Measured Effect
The improvements were directly quantified via `python -m app.cli compare reports/v1_development.json reports/v2_development.json`:
- **Joint F1**: Increased from **0.968** to **1.000** (+0.032).
- **Claims Corrected**: **17 claims fixed** (10 recovered from the `A24` tool error + 7 previously mislabeled claims).
- **Regressions**: **0 regressions** across all 40 development answers.
- **Coverage**: Rose from 95.5% to 100.0%.

---

## Architecture & Engineering Decisions
- **Strict Separation of Concerns**: The LLM is responsible only for extracting exact sentence strings and determining truth values against tool outputs. It never computes character offsets. Character offsets are computed deterministically in Python using cursor tracking across `ai_answer`, completely eliminating hallucinated or drifting offsets.
- **Resilient Tool Execution**: The agent forces tool calling on turn 1 (`tool_choice: required/any`), and switches to `tool_choice: none` on the final turn to guarantee structured JSON output.
- **Deterministic Evaluation**: Pure exact-span evaluation without fuzzy matching or non-deterministic LLM evaluators.

---

## Disclosure
- **Tooling & Assistance**: I designed and orchestrated the ClaimLens architecture using an agentic coding workflow. I reviewed and verified every module, executed tests locally on Windows, configured the Azure OpenAI provider (`gpt-5.6-luna`), analyzed v1 error reports, and iterated on the v2 prompt.
- **Tuning on Final-Check Inputs**: None. The check set (`A41`–`A50`) was evaluated strictly zero-shot using frozen v1 and v2 configurations. Quality metrics were kept null as per specification.
- **Tests Actually Run**: 68 unit and integration tests passing in `evidence/pytest_without_postgres_windows.txt` (7 database tests auto-skipped when running without a live PostgreSQL instance).

---

## Time spent / limitations / unfinished
- **Time spent**: ~5 hours (data verification, provider abstraction, testing harness, live runs, and error analysis).
- **Limitations**:
  - Sequential runner: processing 40 answers sequentially takes ~6 minutes. Can be parallelized using an async worker pool or batch runner.
  - Punctuation folding: unicode normalizer handles standard dashes and curly quotes, but exotic ligatures or whitespace variants could benefit from full NFKC normalization.
- **Unfinished**:
  - Live PostgreSQL persistence was tested via mocked schemas/fixtures and verified against Postgres specs, but live run artifacts are currently persisted to filesystem JSON/Markdown reports rather than a hosted cloud DB.
