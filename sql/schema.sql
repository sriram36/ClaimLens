CREATE TABLE IF NOT EXISTS runs (
    run_id            UUID PRIMARY KEY,
    split             TEXT NOT NULL CHECK (split IN ('development', 'check')),
    agent_version     TEXT NOT NULL CHECK (agent_version IN ('v1', 'v2')),
    prompt_version    TEXT NOT NULL,
    dataset_version   TEXT NOT NULL,
    evaluator_version TEXT NOT NULL,
    fact_version      TEXT NOT NULL,
    provider          TEXT NOT NULL,
    model             TEXT NOT NULL,
    settings          JSONB NOT NULL DEFAULT '{}'::jsonb,
    file_hashes       JSONB,
    source_revision   TEXT,
    status            TEXT NOT NULL CHECK (status IN ('running', 'completed', 'failed')),
    counts            JSONB,
    scores            JSONB,            -- metrics + missing/extra/wrong-label ID lists; quality fields null for check runs
    error             JSONB,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at       TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS answer_results (
    id            BIGSERIAL PRIMARY KEY,
    run_id        UUID NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    answer_id     TEXT NOT NULL,
    status        TEXT NOT NULL CHECK (status IN ('ok', 'error')),
    error_type    TEXT,
    error_message TEXT,
    latency_ms    INTEGER,
    trace_ref     TEXT,
    usage         JSONB,
    UNIQUE (run_id, answer_id),
    CHECK ((status = 'ok' AND error_type IS NULL) OR (status = 'error' AND error_type IS NOT NULL))
);

CREATE TABLE IF NOT EXISTS claim_results (
    id            BIGSERIAL PRIMARY KEY,
    run_id        UUID NOT NULL,
    answer_id     TEXT NOT NULL,
    claim_id      TEXT NOT NULL,
    start_char    INTEGER NOT NULL CHECK (start_char >= 0),
    end_char      INTEGER NOT NULL,
    quote         TEXT NOT NULL,
    label         TEXT NOT NULL CHECK (label IN ('supported', 'contradicted', 'unknown')),
    fact_ids      JSONB NOT NULL DEFAULT '[]'::jsonb,
    reason        TEXT NOT NULL,
    matched_gold  BOOLEAN,              -- NULL for check runs (no ground truth)
    expected_label TEXT,
    label_correct BOOLEAN,
    CHECK (end_char > start_char),
    UNIQUE (run_id, answer_id, start_char, end_char),
    FOREIGN KEY (run_id, answer_id) REFERENCES answer_results (run_id, answer_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS claim_results_run_idx ON claim_results (run_id, answer_id, start_char);
