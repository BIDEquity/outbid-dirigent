#!/usr/bin/env python3
"""
Outbid Dirigent – Oracle
Architektur-Entscheidungen via Claude API direkt.
Cached alle Entscheidungen in DECISIONS.json.
"""

import asyncio
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import BaseModel

from claude_agent_sdk import query as sdk_query
from claude_agent_sdk.types import ClaudeAgentOptions, ResultMessage

from outbid_dirigent.logger import get_logger
from outbid_dirigent.utils import strict_json_schema


class OracleDecision(BaseModel):
    decision: str
    reason: str
    confidence: str  # "high" | "medium" | "low"


def _get_questioner():
    """Lazy import um circular imports zu vermeiden."""
    try:
        from outbid_dirigent.dirigent import get_questioner
        return get_questioner()
    except ImportError:
        return None


class Oracle:
    """
    Oracle für architekturelle Entscheidungen.
    Nutzt Claude API direkt (nicht Claude Code) für schnelle Antworten.
    """

    def __init__(self, repo_path: str, model: str = "claude-sonnet-4-6", dirigent_dir: Optional[Path] = None):
        self.repo_path = Path(repo_path)
        self.model = model
        self.logger = get_logger()
        self._dirigent_dir = dirigent_dir or (self.repo_path / ".dirigent")

        # Lade oder initialisiere Decision Cache
        self.decisions_file = self._dirigent_dir / "DECISIONS.json"
        self.decisions = self._load_decisions()

    def _load_decisions(self) -> Dict:
        """Lädt existierende Entscheidungen."""
        if self.decisions_file.exists():
            with open(self.decisions_file, encoding="utf-8") as f:
                return json.load(f)
        return {"decisions": [], "created_at": datetime.now().isoformat()}

    def _save_decisions(self):
        """Speichert Entscheidungen."""
        self.decisions_file.parent.mkdir(parents=True, exist_ok=True)
        self.decisions["updated_at"] = datetime.now().isoformat()

        with open(self.decisions_file, "w", encoding="utf-8") as f:
            json.dump(self.decisions, f, indent=2, ensure_ascii=False)

    def _get_cache_key(self, question: str, options: List[str]) -> str:
        """Generiert einen eindeutigen Cache-Key für eine Frage."""
        content = f"{question}|{'|'.join(sorted(options))}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _check_cache(self, cache_key: str) -> Optional[Dict]:
        """Prüft ob eine Entscheidung bereits gecached ist."""
        for decision in self.decisions.get("decisions", []):
            if decision.get("cache_key") == cache_key:
                self.logger.debug(f"Oracle: Cache-Hit für {cache_key}")
                return decision
        return None

    def _relevant_decisions(self, question: str, top_n: int = 8) -> list[dict]:
        """Return past decisions ranked by keyword overlap with the current question."""
        all_decisions = self.decisions.get("decisions", [])
        if not all_decisions:
            return []
        q_words = set(question.lower().split())
        def score(d: dict) -> float:
            d_words = set(d.get("question", "").lower().split())
            union = len(q_words | d_words)
            return len(q_words & d_words) / union if union else 0.0
        ranked = sorted(all_decisions, key=score, reverse=True)
        # Always include the most recent decision even if score is low
        top = ranked[:top_n]
        if all_decisions[-1] not in top:
            top = top[: top_n - 1] + [all_decisions[-1]]
        return top

    def _load_context(self, question: str = "") -> str:
        """Lädt relevanten Kontext für die Oracle-Entscheidung."""
        context_parts = []

        # Spec laden
        spec_patterns = [
            self.repo_path / ".planning" / "SPEC.md",
            self.repo_path / "SPEC.md",
        ]
        for spec_path in spec_patterns:
            if spec_path.exists():
                context_parts.append(f"<spec>\n{spec_path.read_text(encoding='utf-8')}\n</spec>")
                break

        # Analyse laden
        analysis_file = self._dirigent_dir / "ANALYSIS.json"
        if analysis_file.exists():
            with open(analysis_file, encoding="utf-8") as f:
                analysis = json.load(f)
            context_parts.append(f"<analysis>\n{json.dumps(analysis, indent=2)}\n</analysis>")

        # Plan laden falls vorhanden
        plan_file = self._dirigent_dir / "PLAN.json"
        if plan_file.exists():
            with open(plan_file, encoding="utf-8") as f:
                plan = json.load(f)
            context_parts.append(f"<plan>\n{json.dumps(plan, indent=2)}\n</plan>")

        # Business Rules laden falls vorhanden
        rules_file = self._dirigent_dir / "BUSINESS_RULES.md"
        if rules_file.exists():
            rules_content = rules_file.read_text(encoding="utf-8")
            if len(rules_content) > 5000:
                rules_content = rules_content[:5000] + "\n... (truncated)"
            context_parts.append(f"<business-rules>\n{rules_content}\n</business-rules>")

        # Bisherige Entscheidungen — ranked by relevance to current question
        if self.decisions.get("decisions"):
            relevant = self._relevant_decisions(question)
            decisions_text = "\n".join([
                f"<decision question=\"{d['question'][:100]}\" confidence=\"{d.get('confidence', '?')}\">{d['decision']}</decision>"
                for d in relevant
            ])
            context_parts.append(f"<previous-decisions>\n{decisions_text}\n</previous-decisions>")

        return "\n\n".join(context_parts)

    async def _aquery(self, prompt: str) -> Optional["OracleDecision"]:
        """Run oracle query via claude_agent_sdk. Returns parsed OracleDecision or None."""
        options = ClaudeAgentOptions(
            model=self.model or None,
            cwd=str(self.repo_path),
            allowed_tools=[],
            permission_mode="bypassPermissions",
            output_format={"type": "json_schema", "schema": strict_json_schema(OracleDecision.model_json_schema())},
        )
        async for message in sdk_query(prompt=prompt, options=options):
            if isinstance(message, ResultMessage) and not message.is_error:
                if message.structured_output:
                    return OracleDecision.model_validate(message.structured_output)
        return None

    def query(
        self,
        question: str,
        options: Optional[List[str]] = None,
        context_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Fragt das Oracle um eine Entscheidung.

        Args:
            question: Die zu beantwortende Frage
            options: Liste von Optionen (optional)
            context_override: Überschreibt den automatisch geladenen Kontext

        Returns:
            Dict mit 'decision' und 'reason'
        """
        self.logger.oracle_query(question)

        # Cache prüfen
        options_list = options or []
        cache_key = self._get_cache_key(question, options_list)
        cached = self._check_cache(cache_key)
        if cached:
            self.logger.oracle_decision(cached["decision"], cached["reason"])
            return {"decision": cached["decision"], "reason": cached["reason"]}

        # Kontext laden
        context = context_override or self._load_context(question)

        # Prompt bauen
        options_text = ""
        if options:
            options_text = f"\nOptionen:\n" + "\n".join([f"- {opt}" for opt in options])

        prompt = f"""<role>Du bist ein Software-Architektur-Oracle. Triff architekturelle Entscheidungen basierend auf dem Kontext.</role>

<context>
{context}
</context>

<question>{question}</question>
{options_text}

<rules>
<rule>Entscheide basierend auf dem Kontext</rule>
<rule>Sei praezise und praktisch</rule>
<rule>Bei Unsicherheit waehle die sicherere Option</rule>
</rules>
"""

        # Agent SDK query
        try:
            start_time = datetime.now()
            result = asyncio.run(self._aquery(prompt))
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            if result is None:
                raise Exception("Oracle SDK produced no structured output")

            decision = result.decision
            reason = result.reason
            confidence = result.confidence

            # In Cache speichern
            self.decisions["decisions"].append({
                "cache_key": cache_key,
                "question": question,
                "options": options_list,
                "decision": decision,
                "reason": reason,
                "confidence": confidence,
                "duration_ms": duration_ms,
                "timestamp": datetime.now().isoformat(),
            })
            self._save_decisions()

            self.logger.oracle_decision(decision, reason)

            return {"decision": decision, "reason": reason, "confidence": confidence}

        except Exception as e:
            self.logger.error(f"Oracle error: {e}")
            return {
                "decision": "Error",
                "reason": str(e),
                "confidence": "low",
            }

    def ask_user_or_decide(
        self,
        question: str,
        options: List[str],
        context: Optional[str] = None,
        task_id: Optional[str] = None,
        phase: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Fragt zuerst den User (via Interactive Mode), fällt zurück auf AI-Entscheidung.

        Args:
            question: Die zu beantwortende Frage
            options: Liste von Optionen
            context: Zusätzlicher Kontext für den User
            task_id: Aktuelle Task-ID (für Portal-Anzeige)
            phase: Aktuelle Phase (für Portal-Anzeige)

        Returns:
            Dict mit 'decision', 'reason' und 'source' ('user' oder 'oracle')
        """
        questioner = _get_questioner()

        # Versuche User zu fragen
        if questioner and questioner.is_active():
            self.logger.info(f"Frage User: {question[:80]}...")

            result = questioner.ask(
                question=question,
                options=options,
                context=context,
                task_id=task_id,
                phase=phase,
            )

            if result.answered and result.answer:
                self.logger.info(f"User-Antwort: {result.answer}")

                # Cache auch User-Entscheidungen
                cache_key = self._get_cache_key(question, options)
                self.decisions["decisions"].append({
                    "cache_key": cache_key,
                    "question": question,
                    "options": options,
                    "decision": result.answer,
                    "reason": "Vom User entschieden",
                    "confidence": "high",
                    "source": "user",
                    "timestamp": datetime.now().isoformat(),
                })
                self._save_decisions()

                return {
                    "decision": result.answer,
                    "reason": "Vom User entschieden",
                    "confidence": "high",
                    "source": "user",
                }

            elif result.timeout:
                self.logger.warn("User-Frage Timeout")
            else:
                self.logger.debug("Questioner nicht verfügbar oder keine Antwort")

        # Fallback: Oracle entscheidet
        self.logger.info("Fallback auf Oracle-Entscheidung...")
        result = self.query(question, options, context)
        result["source"] = "oracle"
        return result

    def decide_architecture(
        self,
        component: str,
        options: List[str],
        constraints: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Convenience-Methode für Architektur-Entscheidungen.

        Args:
            component: Die zu entscheidende Komponente (z.B. "Database", "API Framework")
            options: Liste von Optionen
            constraints: Zusätzliche Constraints

        Returns:
            Dict mit 'decision' und 'reason'
        """
        question = f"Welche Option soll für '{component}' verwendet werden?"
        if constraints:
            question += f"\nConstraints: {constraints}"

        return self.query(question, options)

    def validate_approach(
        self,
        approach: str,
        concern: str,
    ) -> Dict[str, Any]:
        """
        Validiert einen Ansatz gegen eine spezifische Sorge.

        Args:
            approach: Der vorgeschlagene Ansatz
            concern: Die Sorge oder das Risiko

        Returns:
            Dict mit 'valid' (bool), 'decision' und 'reason'
        """
        question = f"""<validation>
<approach>{approach}</approach>
<concern>{concern}</concern>
<question>Soll der Ansatz so beibehalten werden, oder gibt es ein besseres Vorgehen?</question>
</validation>"""

        result = self.query(question, ["Ansatz beibehalten", "Ansatz modifizieren", "Anderen Ansatz wählen"])

        return {
            "valid": "beibehalten" in result["decision"].lower(),
            "decision": result["decision"],
            "reason": result["reason"],
        }

    def resolve_conflict(
        self,
        conflict: str,
        option_a: str,
        option_b: str,
    ) -> Dict[str, Any]:
        """
        Löst einen Konflikt zwischen zwei Optionen.

        Args:
            conflict: Beschreibung des Konflikts
            option_a: Erste Option
            option_b: Zweite Option

        Returns:
            Dict mit 'decision' und 'reason'
        """
        question = f"""<conflict>
<description>{conflict}</description>
<option id="A">{option_a}</option>
<option id="B">{option_b}</option>
<question>Welche Option soll gewaehlt werden?</question>
</conflict>"""

        return self.query(question, [option_a, option_b])

    def get_all_decisions(self) -> List[Dict]:
        """Gibt alle bisherigen Entscheidungen zurück."""
        return self.decisions.get("decisions", [])

    def clear_cache(self):
        """Löscht den Decision Cache."""
        self.decisions = {"decisions": [], "created_at": datetime.now().isoformat()}
        self._save_decisions()
        self.logger.info("Oracle Cache gelöscht")


def create_oracle(repo_path: str, model: str = "claude-sonnet-4-6", dirigent_dir: Optional[Path] = None) -> Oracle:
    """Factory-Funktion für Oracle-Instanz."""
    return Oracle(repo_path, model, dirigent_dir=dirigent_dir)
