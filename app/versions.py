"""Fixed version strings and constants shared by agent, harness, API and DB."""

DATASET_VERSION = "long-brand-answers-50-v4"
FACT_VERSION = "speaker-catalogue-v4"
EVALUATOR_VERSION = "sentence-spans-and-labels-v4"

AGENT_VERSIONS = ("v1", "v2")
PROMPT_VERSIONS = {"v1": "prompt-v1", "v2": "prompt-v2"}
SPLITS = ("development", "check")
LABELS = ("supported", "contradicted", "unknown")

TOOL_NAME = "get_brand_facts"
MAX_TURNS = 3  # model turns per answer (assessment limit)
