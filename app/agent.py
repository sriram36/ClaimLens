"""Claim extraction + classification agent.

Flow (max 3 model turns): the model must request `get_brand_facts` via real tool calling, the executor validates and
runs each call, then the model returns JSON claims (exact quotes + labels). Python locates and validates offsets.
Nothing but AgentInput ever reaches the model or the tool."""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

from .config import Settings
from .data import AgentInput, Catalogue
from .errors import AgentError, InvalidOutput, ProviderFailure, ToolError, TurnLimitExceeded, UnknownBrand
from .providers import Provider
from .validate import limit_two_sentences, validate_claims
from .versions import AGENT_VERSIONS, MAX_TURNS, PROMPT_VERSIONS, TOOL_NAME

TOOLS = [{
    "name": TOOL_NAME,
    "description": "Read-only lookup of every catalogue fact row for one brand (fact_version speaker-catalogue-v4).",
    "input_schema": {"type": "object", "properties": {"brand_id": {"type": "string", "description": "e.g. cleartrail"}},
                     "required": ["brand_id"], "additionalProperties": False},
}]

# Length-preserving fold used ONLY to locate a quote; the stored quote is always the exact slice of ai_answer.
_FOLD = str.maketrans({"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"', "\u2013": "-", "\u2014": "-", "\u00a0": " "})


@dataclass
class AgentResult:
    answer_id: str
    claims: list
    trace: list = field(default_factory=list)
    usage: dict = field(default_factory=dict)
    turns: int = 0


def locate(ai_answer: str, quote: str, cursor: int) -> tuple[int, int]:
    """Find `quote` at or after `cursor` (claims arrive in answer order, so repeated sentences resolve by position)."""
    q = quote.strip()
    if not q:
        raise InvalidOutput("empty quote")
    i = ai_answer.find(q, cursor)
    if i == -1:
        i = ai_answer.translate(_FOLD).find(q.translate(_FOLD), cursor)
    if i == -1:
        raise InvalidOutput("quote not found in ai_answer at or after the previous claim")
    return i, i + len(q)


def parse_model_json(text: str) -> dict:
    t = text.strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t)
    try:
        data = json.loads(t)
    except json.JSONDecodeError:
        a, b = t.find("{"), t.rfind("}")
        if a == -1 or b <= a:
            raise InvalidOutput("model output is not JSON")
        try:
            data = json.loads(t[a:b + 1])
        except json.JSONDecodeError as e:
            raise InvalidOutput(f"model output is not valid JSON: {e.msg}")
    if not isinstance(data, dict) or not isinstance(data.get("claims"), list):
        raise InvalidOutput('model output must be an object with a "claims" list')
    return data


class ClaimsAgent:
    def __init__(self, provider: Provider, catalogue: Catalogue, agent_version: str, settings: Settings | None = None):
        if agent_version not in AGENT_VERSIONS:
            raise ValueError(f"unknown agent_version {agent_version!r}")
        self.provider = provider
        self.catalogue = catalogue
        self.version = agent_version
        self.settings = settings or Settings()
        # Load the prompt template and bake in the known brand list.
        # Brand IDs come from the catalogue at runtime, not hardcoded.
        template = (Path(self.settings.prompt_dir) / f"{agent_version}.md").read_text(encoding="utf-8")
        self.system = template.replace("{brand_ids}", ", ".join(catalogue.brand_ids))
        self.prompt_version = PROMPT_VERSIONS[agent_version]

    # ---- prompt -----------------------------------------------------------------
    @staticmethod
    def user_message(inp: AgentInput) -> str:
        return (f"answer_id: {inp.answer_id}\nprimary brand_id: {inp.brand_id}\n\n"
                f"<question>\n{inp.question}\n</question>\n\n<ai_answer>\n{inp.ai_answer}\n</ai_answer>")

    # ---- tool executor ------------------------------------------------------------
    def _execute_tool(self, block: dict) -> str:
        if block.get("name") != TOOL_NAME:
            raise ToolError(f"illegal tool requested: {str(block.get('name'))[:60]!r}")
        args = block.get("input")
        if not isinstance(args, dict) or set(args) != {"brand_id"} or not isinstance(args["brand_id"], str):
            raise ToolError("get_brand_facts requires exactly one string argument: brand_id")
        try:
            return json.dumps(self.catalogue.get_brand_facts(args["brand_id"]), ensure_ascii=False)
        except UnknownBrand as e:
            raise ToolError(str(e))

    # ---- main loop ------------------------------------------------------------------
    def run(self, inp: AgentInput) -> AgentResult:
        messages = [{"role": "user", "content": self.user_message(inp)}]
        trace: list = [{"role": "user", "content": messages[0]["content"]}]
        usage = {"input_tokens": 0, "output_tokens": 0}
        looked_up = False
        for turn in range(1, MAX_TURNS + 1):
            choice = {"type": "any"} if turn == 1 else ({"type": "none"} if turn == MAX_TURNS else {"type": "auto"})
            resp = self.provider.create(system=self.system, messages=messages, tools=TOOLS, tool_choice=choice,
                                        max_tokens=self.settings.max_tokens, timeout=self.settings.provider_timeout_s)
            for k in usage:
                usage[k] += (resp.usage or {}).get(k) or 0
            trace.append({"role": "assistant", "turn": turn, "content": resp.content, "stop_reason": resp.stop_reason})
            calls = [b for b in resp.content if b.get("type") == "tool_use"]
            if calls:
                if turn == MAX_TURNS:
                    raise TurnLimitExceeded("model still requested tools on the last allowed turn")
                results = [{"type": "tool_result", "tool_use_id": b["id"], "content": self._execute_tool(b)} for b in calls]
                looked_up = True
                messages.append({"role": "assistant", "content": resp.content})
                messages.append({"role": "user", "content": results})
                trace.append({"role": "user", "turn": turn, "content": results})
                continue
            if not looked_up:
                raise InvalidOutput("model answered without requesting get_brand_facts")
            text = "".join(b.get("text", "") for b in resp.content if b.get("type") == "text")
            claims = self._build_claims(inp, text)
            return AgentResult(inp.answer_id, claims, trace, usage, turn)
        raise TurnLimitExceeded("no final answer within the turn limit")

    # ---- output assembly -----------------------------------------------------------------
    def _build_claims(self, inp: AgentInput, text: str) -> list[dict]:
        data = parse_model_json(text)
        claims, cursor = [], 0
        for i, item in enumerate(data["claims"]):
            if not isinstance(item, dict) or not isinstance(item.get("quote"), str):
                raise InvalidOutput(f"claim[{i}]: missing quote")
            if not isinstance(item.get("reason", ""), str):
                raise InvalidOutput(f"claim[{i}]: reason must be a string")
            s, e = locate(inp.ai_answer, item["quote"], cursor)
            cursor = e
            claims.append({
                "claim_id": f"{inp.answer_id}:{s}:{e}", "start_char": s, "end_char": e,
                "quote": inp.ai_answer[s:e], "label": item.get("label"),
                "fact_ids": item.get("fact_ids", []), "reason": limit_two_sentences(item.get("reason", "")),
            })
        return validate_claims(inp.answer_id, inp.ai_answer, claims, self.catalogue.fact_ids)
