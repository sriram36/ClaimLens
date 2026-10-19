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

## Disclosure & Methodology
- **Tooling & Workflow**: I architected, built, and evaluated ClaimLens using an agentic coding workflow. I reviewed and verified the code, executed the test suite, configured the live model provider, analyzed the empirical failure reports, and designed the prompt fixes in `v2`.
- **Model Provider**: I used **Azure OpenAI** (`gpt-5.6-luna`) through the official `openai` Python SDK. Azure OpenAI was selected because `gpt-5.6-luna` natively supports function calling (`get_brand_facts`) within the 3-turn budget, fulfilling the requirement for a live, hosted model API.
- **Run Provenance**: The live runs were captured sequentially during evaluation before committing and tagging the repository, which is why `source_revision` is recorded as `None` in the generated report headers. The integrity of the evaluation is anchored in the unmodified dataset hashes (`answers.csv=fa28e813ea54`, `brand_facts.csv=2190d40fad2d`, `development_gold.csv=afe84cc78f30`), complete sanitized exchange logs (`reports/*.exchanges.jsonl`), and git tags `v1` and `v2`.
- **Tuning on Final-Check Inputs**: None. The check set (`A41`–`A50`) was run strictly zero-shot against frozen v1 and v2 prompts. Quality metrics ($G, M, C$, F1) are `null` as required by the blind evaluation specification.
- **Database & Test Suite Verification**:
  - **Full Suite (75 passed)**: In an environment with PostgreSQL running (documented in `evidence/pytest_with_postgres.txt`), all 75 tests pass. The 7 database tests (`tests/test_db.py`) run against a live PostgreSQL server, testing real table creation, foreign keys, cascade deletes, and JSONB queries. To keep DB tests fast, deterministic, and isolated from external network latency, the DB tests use a scripted `FakeProvider`.
  - **Local Suite (68 passed, 7 skipped)**: On machines without a local PostgreSQL daemon (documented in `evidence/pytest_without_postgres_windows.txt`), the 7 database tests auto-skip cleanly so the suite remains runnable anywhere.

---

## Time spent / limitations / unfinished
- **Time spent**: ~5 hours total across data exploration, architecture design, provider adaptation, empirical error diagnosis, and prompt iteration.
- **Limitations**:
  - Sequential runner: The CLI runs sequentially for deterministic order and clean progress reporting (~6 minutes for 40 answers). In production, this can be parallelized with an async worker pool.
  - Punctuation folding: The custom character folding handles common typographic curly quotes, en/em-dashes, and non-breaking spaces. Broader international text would benefit from complete Unicode NFKC normalization.
- **Unfinished**:
  - Automated CI/CD workflow (e.g. GitHub Actions with a PostgreSQL service container) to automatically run all 75 tests on every pull request.
