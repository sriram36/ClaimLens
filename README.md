# ClaimLens: Grounded Claim Extraction & Fact-Verification Engine

ClaimLens is an intelligent verification system that parses long-form generated answers about audio products, pulls out every individual verifiable factual claim sentence, and cross-references each claim against ground-truth product specifications (`data/brand_facts.csv`). Each extracted claim is classified as `supported`, `contradicted`, or `unknown`.

The system features real tool calling (`get_brand_facts`), exact character-offset span mapping, a deterministic evaluation and scoring harness, production FastAPI endpoints, and optional PostgreSQL persistence. Provider: **Azure OpenAI (`gpt-5.6-luna`), native tool calling**.

## Layout
| Path | Purpose |
|---|---|
| `app/agent.py` | 3-turn agent loop, tool executor, quote location, output assembly |
| `app/validate.py` | strict output validation (spans, quote equality, IDs, labels, fact IDs, ordering/overlap) |
| `app/scoring.py` | exact-span scorer: extraction + joint P/R/F1, missed/extra/wrong-label IDs, error accounting |
| `app/runner.py`, `app/reports.py`, `app/cli.py` | sequential runner, JSON/MD reports, v1-vs-v2 comparison |
| `app/api.py`, `app/db.py`, `sql/schema.sql` | FastAPI routes, PostgreSQL store (parameterized SQL), schema |
| `prompts/v1.md`, `prompts/v2.md` | baseline and candidate prompts (frozen per version) |
| `data/` | issued CSVs + `SHA256SUMS` (unmodified) |
| `tests/` | controlled tests (fake provider, scorer arithmetic, API, Postgres) |
| `evidence/` | actual test output; put live-run reports here too (see below) |

## Install
```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1

pip install -r requirements.txt
cp .env.example .env                        # fill AZURE_OPENAI_API_KEY, ENDPOINT, DEPLOYMENT
python -m app.cli verify-data               # checks 50/132/376 rows, gold slices, prints file hashes
createdb kasparro && python -m app.cli init-db    # optional: only needed for the API / --save-db
```

## Tests
```bash
python -m pytest -v                         # DB tests auto-skip unless DATABASE_URL points at a Postgres
```
Tests never call a live provider. Fakes do not replace the four live runs.

## The required sequence (4 live runs, ~sequential)
```bash
python -m app.cli run --agent-version v1 --split development --limit 2   # smoke test only, not evidence
python -m app.cli run --agent-version v1 --split development --save-db   # -> reports/v1_development.{json,md,exchanges.jsonl}
# inspect reports/v1_development.md (missed / extra / wrong-label / by-tag), decide ONE change, edit prompts/v2.md
python -m app.cli run --agent-version v2 --split development --save-db
python -m app.cli compare reports/v1_development.json reports/v2_development.json
# freeze v1 and v2 (git commit + tag), then:
python -m app.cli run --agent-version v1 --split check --save-db
python -m app.cli run --agent-version v2 --split check --save-db
```
Check runs save predictions, errors, counts and timing only. G, M, C and every quality metric are `null`.
Commit the four reports + `reports/comparison_v1_v2_development.md` + `evidence/` before submitting.

## API
```bash
uvicorn app.api:app --reload
curl -X POST localhost:8000/classify -H 'content-type: application/json' -d '{"answer_id":"A01","brand_id":"cleartrail","question":"...","ai_answer":"...","agent_version":"v1"}'
curl -X POST localhost:8000/evaluation-runs -H 'content-type: application/json' -d '{"agent_version":"v1","split":"development"}'
curl localhost:8000/evaluation-runs/<run_id>
```
Status codes: 200/201 ok; 422 invalid request (incl. gold or claim-list fields); 404 unknown primary brand / missing run; 502 provider error or
invalid model output; 504 provider timeout; 503 no `DATABASE_URL`. Error bodies are `{"error":{"type","message"}}`, sanitized.

## Design decisions
- **Tool use is real**: turn 1 forces a tool call (`tool_choice: any`) so the model must request `get_brand_facts` itself, choosing which brand(s) (including a comparison brand). Several calls per turn are allowed. The last allowed turn uses `tool_choice: none`. The executor accepts only the tool name `get_brand_facts` with exactly `{brand_id}` for a known brand; anything else is an answer-level `tool_error`. Text in the answer can never trigger an action.
- **Model returns quotes, Python computes offsets.** Claims arrive in answer order; each quote is searched from the end of the previous claim, so repeated sentences resolve by position. A length-preserving fold (curly quotes, nbsp, en/em dash) is used only to *locate*; the stored `quote` is always the exact slice of `ai_answer`. Everything is then validated (bounds, quote equality, derived `claim_id`, labels, fact IDs, order, overlap).
- `reason` longer than two sentences is truncated deterministically to two before validation.
- **Errors are never `unknown`.** Provider failure, timeout, invalid output, illegal tool, unknown brand and turn exhaustion create an answer-level error with no accepted predictions; the answer's gold claims stay in G as missed.
- **Gold never reaches the model path.** `AgentInput` has four fields; gold is joined only in `scoring`/`runner` after predictions are saved (and in the DB, after prediction rows exist). Tested.
- Timeouts: **120 s per provider request** (`KASPARRO_TIMEOUT_S`), SDK retries 2 (`KASPARRO_MAX_RETRIES`) for 429/5xx/connection errors.
- Scorer: exact `(answer_id, start, end)` plus quote equality, each gold matched at most once; no fuzzy matching, no judge.

## Prompt Versions: v1 vs v2

- **v1** (`prompts/v1.md`): Baseline prompt defining the task, factual extraction boundaries (excluding generic advice), truth-labeling rules (`supported`, `contradicted`, `unknown`), and JSON response schema.
- **v2** (`prompts/v2.md`): Refined prompt directly targeting the failure modes diagnosed from the v1 development error report:
  1. *Catalogue Brand Boundary*: Enforces strict restriction that `get_brand_facts` may only be called for registered brands (`cleartrail`, `cloudnote`, `stonewave`), preventing fatal tool errors on unlisted competitors (such as `rivalsound` in `A24`).
  2. *Comparison Direction*: Mandates validating both the difference magnitude and directionality on comparative price claims (fixing reverse price comparisons in `A09`, `A16`, `A35`).
  3. *Core Feature Booleans vs. Qualification*: Instructs the agent to match core feature assertions against catalogue booleans without rejecting claims due to trailing conversational context (fixing `A12`, `A15`, `A29`).
  4. *Box Inclusions*: Clarifies adapter inclusion semantics.

All data, scoring logic, model configuration, and runtime settings remained strictly fixed between v1 and v2. See `reports/comparison_v1_v2_development.md` for the full empirical comparison.

## Evaluation Write-up
See `WRITEUP.md` for detailed results, failure analysis, architecture decisions, and disclosures.
