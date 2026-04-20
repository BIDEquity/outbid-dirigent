#!/usr/bin/env python3
"""
Outbid Dirigent – Spec Compactor

One-shot LLM call that converts a free-form markdown spec into a structured,
token-efficient CompactSpec (requirements with stable IDs, glossary, entities,
flows). The compacted form is injected into per-task prompts (filtered by
relevant_req_ids) so coders see only the requirements relevant to their task,
plus the full glossary/entities/flows as reference.
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

from claude_agent_sdk import query as sdk_query
from claude_agent_sdk.types import ClaudeAgentOptions, ResultMessage
from pydantic import BaseModel, Field

from outbid_dirigent.logger import get_logger
from outbid_dirigent.utils import strict_json_schema


# ---------------------------------------------------------------------------
# Pydantic schema
# ---------------------------------------------------------------------------


ReqCategory = Literal[
    "data-model",
    "api",
    "ui",
    "auth",
    "integration",
    "infra",
    "policy",
    "workflow",
    "validation",
    "testing",
    "other",
]
ReqPriority = Literal["must", "should", "may"]


class Requirement(BaseModel):
    id: str = Field(description="Stable ID like R1, R2, R3 in source order")
    category: ReqCategory
    priority: ReqPriority
    text: str = Field(description="Single requirement, verbatim domain terms preserved")


class GlossaryTerm(BaseModel):
    name: str
    definition: str = Field(
        description="One-sentence definition. Write 'undefined in source' if not derivable from spec or universal knowledge."
    )


class EntityField(BaseModel):
    name: str
    type: str
    required: bool = True
    constraints: str = ""


class Entity(BaseModel):
    name: str
    fields: list[EntityField] = Field(default_factory=list)


class FlowStep(BaseModel):
    n: int
    action: str


class Flow(BaseModel):
    name: str
    steps: list[FlowStep] = Field(default_factory=list)


class CompactMeta(BaseModel):
    title: str
    scope: str = Field(description="One sentence: what this builds")
    out_of_scope: list[str] = Field(default_factory=list)


class BusinessRule(BaseModel):
    """A business rule extracted from the existing codebase (Legacy route)."""

    id: str = Field(description="Stable ID like BR1, BR2, BR3")
    text: str = Field(description="The business rule as found in the codebase")
    source: str = Field("", description="File:line where this rule is implemented")
    related_reqs: list[str] = Field(
        default_factory=list,
        description="Requirement IDs (R1, R2, ...) that this rule constrains or implements",
    )


class TestingConsideration(BaseModel):
    """A testing consideration for the implementation."""

    aspect: str = Field(description="What needs testing (e.g. 'auth flow', 'data migration')")
    approach: str = Field(description="How to test it (e.g. 'integration test with real DB')")
    risk: str = Field("", description="What could go wrong if not tested")


class CompactSpec(BaseModel):
    """Structured, token-efficient representation of a markdown spec."""

    meta: CompactMeta
    glossary: list[GlossaryTerm] = Field(default_factory=list)
    requirements: list[Requirement] = Field(default_factory=list)
    entities: list[Entity] = Field(default_factory=list)
    flows: list[Flow] = Field(default_factory=list)
    business_rules: list[BusinessRule] = Field(
        default_factory=list,
        description="Business rules from existing codebase (Legacy route only)",
    )
    testing: list[TestingConsideration] = Field(
        default_factory=list,
        description="Testing considerations for the implementation",
    )

    def render_xml(self, only_req_ids: Optional[set[str]] = None) -> str:
        """Render this compact spec as XML for injection into a task prompt.

        Args:
            only_req_ids: If provided, only requirements whose IDs are in this
                set are emitted. Glossary, entities, and flows are ALWAYS
                emitted in full — they are reference context.

        Returns:
            XML-tagged string suitable for inclusion in an LLM prompt.
        """
        lines: list[str] = ["<spec-compact>"]

        # Meta
        lines.append("  <meta>")
        lines.append(f"    <title>{_esc(self.meta.title)}</title>")
        lines.append(f"    <scope>{_esc(self.meta.scope)}</scope>")
        if self.meta.out_of_scope:
            lines.append("    <out-of-scope>")
            for item in self.meta.out_of_scope:
                lines.append(f"      <item>{_esc(item)}</item>")
            lines.append("    </out-of-scope>")
        lines.append("  </meta>")

        # Glossary (always full)
        if self.glossary:
            lines.append("  <glossary>")
            for term in self.glossary:
                lines.append(f'    <term name="{_esc(term.name)}">{_esc(term.definition)}</term>')
            lines.append("  </glossary>")

        # Requirements (filtered if only_req_ids given)
        if only_req_ids is None:
            reqs = self.requirements
        else:
            reqs = [r for r in self.requirements if r.id in only_req_ids]
        if reqs:
            lines.append(
                '  <must-satisfy hint="these are the requirements YOUR task must address">'
            )
            for r in reqs:
                lines.append(
                    f'    <req id="{_esc(r.id)}" category="{r.category}" priority="{r.priority}">{_esc(r.text)}</req>'
                )
            lines.append("  </must-satisfy>")

        # Entities (always full)
        if self.entities:
            lines.append(
                '  <entities hint="data model reference — implement only what your task requires, not all entities">'
            )
            for e in self.entities:
                lines.append(f'    <entity name="{_esc(e.name)}">')
                for f in e.fields:
                    req_attr = "true" if f.required else "false"
                    constraints = _esc(f.constraints) if f.constraints else ""
                    lines.append(
                        f'      <field name="{_esc(f.name)}" type="{_esc(f.type)}" required="{req_attr}">{constraints}</field>'
                    )
                lines.append("    </entity>")
            lines.append("  </entities>")

        # Flows (always full, with explicit "do not implement all" hint)
        if self.flows:
            lines.append(
                '  <flows hint="workflow reference — DO NOT implement all flows, only the parts your task covers">'
            )
            for fl in self.flows:
                lines.append(f'    <flow name="{_esc(fl.name)}">')
                for st in fl.steps:
                    lines.append(f'      <step n="{st.n}">{_esc(st.action)}</step>')
                lines.append("    </flow>")
            lines.append("  </flows>")

        # Business rules (always full — these MUST be preserved)
        if self.business_rules:
            lines.append(
                '  <business-rules hint="these rules exist in the codebase and MUST be preserved">'
            )
            for br in self.business_rules:
                related = f' related-reqs="{",".join(br.related_reqs)}"' if br.related_reqs else ""
                source = f' source="{_esc(br.source)}"' if br.source else ""
                lines.append(
                    f'    <rule id="{_esc(br.id)}"{related}{source}>{_esc(br.text)}</rule>'
                )
            lines.append("  </business-rules>")

        # Testing considerations
        if self.testing:
            lines.append('  <testing hint="testing strategy for this implementation">')
            for t in self.testing:
                risk = f' risk="{_esc(t.risk)}"' if t.risk else ""
                lines.append(
                    f'    <consideration aspect="{_esc(t.aspect)}"{risk}>{_esc(t.approach)}</consideration>'
                )
            lines.append("  </testing>")

        lines.append("</spec-compact>")
        return "\n".join(lines)


def _esc(s: str) -> str:
    """Minimal XML escaping for text content and attributes."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


# ---------------------------------------------------------------------------
# Compactor
# ---------------------------------------------------------------------------


COMPACTOR_SYSTEM_PROMPT = """\
You are a spec compactor. Convert a free-form markdown spec into a structured,
token-efficient CompactSpec that downstream coding agents can scan in
O(requirements) instead of O(prose).

## Hard rules

1. **Lossless on requirements.** Every testable, implementable, or
   behavior-defining statement in the source MUST appear as a Requirement.
   When in doubt, include it. Better to over-include than to drop.

2. **Lossy on prose only.** Strip narrative, motivation, background, and
   rationale UNLESS they define behavior. Marketing language and history go.

3. **Stable IDs.** Number requirements R1, R2, R3 ... in source order.

4. **Verbatim domain terms.** Do NOT translate, paraphrase, or "clean up"
   domain-specific terminology (legal terms, product names, regulatory codes,
   proper nouns, foreign-language terms). Copy them exactly.

5. **One requirement per Requirement.** If a sentence contains "X and Y and Z",
   split into three reqs unless they are inseparable.

6. **No invention. Zero tolerance.**
   - Do NOT add requirements not in the source.
   - Do NOT add fields, enum values, status names, or constraints not in source.
   - Do NOT "complete" partial lists. "e.g., A, B, C" → emit exactly A, B, C.
   - Do NOT infer requirements from absence.
   - Do NOT normalize apparent typos in domain terms.
   - For glossary definitions: write ONLY what is derivable from the spec or
     universally known. If neither, set definition to "undefined in source".

7. **Self-verification.** Before returning, re-scan your output and ask for
   each Requirement: "Can I point to a specific sentence or table cell in the
   source that states this?" If no, drop it.

## Categories

data-model, api, ui, auth, integration, infra, policy, workflow, validation, testing, other

## Glossary criteria

Add a term for any keyword that is: a domain-specific abbreviation, a
product/service name with non-obvious meaning, a foreign-language term, or a
technical term with spec-specific meaning. Skip things any developer knows
(PDF, API, UUID, HTTP).

## Entities and flows

Emit <entities> only if the spec defines data models, schemas, or enumerated
types. Emit <flows> only if the spec defines step-by-step processes or state
machines. Both are OPTIONAL — empty lists are fine.

## Business rules (Legacy route)

If business rules are provided (from Proteus extraction of an existing codebase):
- Create a BusinessRule for each rule with a stable ID (BR1, BR2, ...)
- Link each rule to the requirements it constrains via `related_reqs`
- Preserve the source file:line reference
- These rules represent EXISTING behavior that MUST be preserved during refactoring

## Testing considerations

Always emit testing considerations. For each major area of the spec, identify:
- What needs testing and how (integration, unit, e2e)
- What could go wrong if not tested
- This helps downstream agents write tests alongside implementation

## Token budget

Aim for 30-50% of source token count. Drop prose. Keep behavior.
"""


def compact_spec(
    spec_content: str,
    model: str = "claude-haiku-4-5",
    dirigent_dir: Optional[Path] = None,
    business_rules: Optional[str] = None,
) -> Optional[CompactSpec]:
    """Compact a markdown spec into a structured CompactSpec via one LLM call.

    Args:
        spec_content: Full markdown spec text.
        model: Model to use (haiku for speed/cost).
        dirigent_dir: Where to save SPEC.compact.json. If None, no file is written.
        business_rules: Proteus-extracted business rules as JSON string (Legacy route).
            When provided, the compactor links rules to requirements and includes
            them in the CompactSpec.

    Returns:
        CompactSpec on success, None on API error or refusal.
    """
    logger = get_logger()

    parts = [f"<spec>\n{spec_content}\n</spec>"]
    if business_rules:
        parts.append(f"\n<business-rules-input>\n{business_rules}\n</business-rules-input>")
    parts.append("\n\nCompact this spec per the rules.")
    user_prompt = "".join(parts)

    try:
        start = datetime.now()
        structured, usage = asyncio.run(_aquery_compact(user_prompt, model))
        duration_ms = int((datetime.now() - start).total_seconds() * 1000)

        if structured is None:
            logger.error("Spec compactor: model refused to produce a compact spec")
            return None

        try:
            compact = CompactSpec.model_validate(structured)
        except Exception as e:
            logger.error(f"Spec compactor: failed to parse output: {e}")
            return None

        input_tokens = int(usage.get("input_tokens", 0) or 0)
        output_tokens = int(usage.get("output_tokens", 0) or 0)
        logger.api_usage(
            component="spec_compactor",
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_tokens=int(usage.get("cache_read_input_tokens", 0) or 0),
            cache_write_tokens=int(usage.get("cache_creation_input_tokens", 0) or 0),
            cost_cents=int((input_tokens * 1 + output_tokens * 5) / 10000),
            operation="compact_spec",
            duration_ms=duration_ms,
        )

        logger.info(
            f"Spec compacted: {len(compact.requirements)} reqs, "
            f"{len(compact.glossary)} glossary terms, "
            f"{len(compact.entities)} entities, "
            f"{len(compact.flows)} flows"
        )

        if dirigent_dir is not None:
            _save_compact_spec(dirigent_dir, compact)

        return compact

    except Exception as e:
        logger.error(f"Spec compactor error: {e}")
        return None


async def _aquery_compact(user_prompt: str, model: str) -> tuple[Optional[dict], dict]:
    """Run compaction via claude_agent_sdk. Returns (structured_output, usage).

    Drains the generator to completion before returning — see the matching
    comment in llm_router._aquery_route for the subprocess-cleanup reason.
    """
    options = ClaudeAgentOptions(
        model=model,
        allowed_tools=[],
        permission_mode="bypassPermissions",
        setting_sources=[],  # don't load user/project/local settings; minimal context
        system_prompt=COMPACTOR_SYSTEM_PROMPT,
        output_format={
            "type": "json_schema",
            "schema": strict_json_schema(CompactSpec.model_json_schema()),
        },
    )
    structured: Optional[dict] = None
    usage: dict = {}
    async for message in sdk_query(prompt=user_prompt, options=options):
        if isinstance(message, ResultMessage) and not message.is_error:
            structured = message.structured_output
            usage = message.usage or {}
    return structured, usage


def _save_compact_spec(dirigent_dir: Path, compact: CompactSpec) -> None:
    """Persist CompactSpec to $DIRIGENT_RUN_DIR/SPEC.compact.json."""
    dirigent_dir.mkdir(parents=True, exist_ok=True)
    path = dirigent_dir / "SPEC.compact.json"
    path.write_text(
        compact.model_dump_json(indent=2),
        encoding="utf-8",
    )
