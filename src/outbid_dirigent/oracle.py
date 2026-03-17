#!/usr/bin/env python3
"""
Outbid Dirigent – Oracle
Architektur-Entscheidungen via Claude API direkt.
Cached alle Entscheidungen in DECISIONS.json.
"""

import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

import anthropic

from outbid_dirigent.logger import get_logger


class Oracle:
    """
    Oracle für architekturelle Entscheidungen.
    Nutzt Claude API direkt (nicht Claude Code) für schnelle Antworten.
    """

    def __init__(self, repo_path: str, model: str = "claude-sonnet-4-20250514"):
        self.repo_path = Path(repo_path)
        self.model = model
        self.logger = get_logger()
        self.client = anthropic.Anthropic()

        # Lade oder initialisiere Decision Cache
        self.decisions_file = self.repo_path / ".dirigent" / "DECISIONS.json"
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

    def _load_context(self) -> str:
        """Lädt relevanten Kontext für die Oracle-Entscheidung."""
        context_parts = []

        # Spec laden
        spec_patterns = [
            self.repo_path / ".planning" / "SPEC.md",
            self.repo_path / "SPEC.md",
        ]
        for spec_path in spec_patterns:
            if spec_path.exists():
                context_parts.append(f"## SPEC\n{spec_path.read_text(encoding='utf-8')}")
                break

        # Analyse laden
        analysis_file = self.repo_path / ".dirigent" / "ANALYSIS.json"
        if analysis_file.exists():
            with open(analysis_file, encoding="utf-8") as f:
                analysis = json.load(f)
            context_parts.append(f"## ANALYSIS\n```json\n{json.dumps(analysis, indent=2)}\n```")

        # Plan laden falls vorhanden
        plan_file = self.repo_path / ".dirigent" / "PLAN.json"
        if plan_file.exists():
            with open(plan_file, encoding="utf-8") as f:
                plan = json.load(f)
            context_parts.append(f"## PLAN\n```json\n{json.dumps(plan, indent=2)}\n```")

        # Business Rules laden falls vorhanden
        rules_file = self.repo_path / ".dirigent" / "BUSINESS_RULES.md"
        if rules_file.exists():
            rules_content = rules_file.read_text(encoding="utf-8")
            # Limitiere auf erste 5000 Zeichen
            if len(rules_content) > 5000:
                rules_content = rules_content[:5000] + "\n... (truncated)"
            context_parts.append(f"## BUSINESS_RULES\n{rules_content}")

        # Bisherige Entscheidungen
        if self.decisions.get("decisions"):
            recent_decisions = self.decisions["decisions"][-5:]  # Letzte 5
            decisions_text = "\n".join([
                f"- {d['question'][:100]}... → {d['decision']}"
                for d in recent_decisions
            ])
            context_parts.append(f"## PREVIOUS DECISIONS\n{decisions_text}")

        return "\n\n".join(context_parts)

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
        context = context_override or self._load_context()

        # Prompt bauen
        options_text = ""
        if options:
            options_text = f"\nOptionen:\n" + "\n".join([f"- {opt}" for opt in options])

        prompt = f"""Du bist ein Software-Architektur-Oracle. Deine Aufgabe ist es, architekturelle
Entscheidungen zu treffen basierend auf dem gegebenen Kontext.

{context}

---

Frage: {question}
{options_text}

Antworte als JSON mit diesem Format:
{{
    "decision": "Deine Entscheidung (kurz und präzise)",
    "reason": "Begründung (1-2 Sätze)",
    "confidence": "high|medium|low"
}}

Wichtig:
- Entscheide basierend auf dem Kontext
- Sei präzise und praktisch
- Bei Unsicherheit wähle die sicherere Option
- Antworte NUR mit dem JSON, kein anderer Text
"""

        # API-Aufruf
        try:
            start_time = datetime.now()
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            )
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            # Token Usage extrahieren und loggen
            usage = response.usage
            input_tokens = usage.input_tokens
            output_tokens = usage.output_tokens
            cache_read = getattr(usage, 'cache_read_input_tokens', 0) or 0
            cache_write = getattr(usage, 'cache_creation_input_tokens', 0) or 0

            # Kosten berechnen (Sonnet 4: $3/M input, $15/M output)
            cost_cents = int((input_tokens * 3 + output_tokens * 15) / 10000)

            # API Usage Event emittieren
            self.logger.api_usage(
                component="oracle",
                model=self.model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cache_read_tokens=cache_read,
                cache_write_tokens=cache_write,
                cost_cents=cost_cents,
                operation="decision",
                duration_ms=duration_ms,
            )

            # Response parsen
            response_text = response.content[0].text.strip()

            # JSON extrahieren (falls mit Markdown umgeben)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            result = json.loads(response_text)

            decision = result.get("decision", "Keine Entscheidung")
            reason = result.get("reason", "Keine Begründung")
            confidence = result.get("confidence", "medium")

            # In Cache speichern
            self.decisions["decisions"].append({
                "cache_key": cache_key,
                "question": question,
                "options": options_list,
                "decision": decision,
                "reason": reason,
                "confidence": confidence,
                "tokens": {
                    "input": input_tokens,
                    "output": output_tokens,
                    "cache_read": cache_read,
                    "cost_cents": cost_cents,
                },
                "timestamp": datetime.now().isoformat(),
            })
            self._save_decisions()

            self.logger.oracle_decision(decision, reason)

            return {"decision": decision, "reason": reason, "confidence": confidence}

        except json.JSONDecodeError as e:
            self.logger.error(f"Oracle JSON Parse Error: {e}")
            return {
                "decision": "Parsing Error",
                "reason": f"Konnte Oracle-Antwort nicht parsen: {e}",
                "confidence": "low",
            }
        except anthropic.APIError as e:
            self.logger.error(f"Oracle API Error: {e}")
            return {
                "decision": "API Error",
                "reason": f"Oracle API Fehler: {e}",
                "confidence": "low",
            }

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
        question = f"""Ist dieser Ansatz valide?

Ansatz: {approach}
Sorge: {concern}

Soll der Ansatz so beibehalten werden, oder gibt es ein besseres Vorgehen?"""

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
        question = f"""Konflikt: {conflict}

Option A: {option_a}
Option B: {option_b}

Welche Option soll gewählt werden?"""

        return self.query(question, [option_a, option_b])

    def get_all_decisions(self) -> List[Dict]:
        """Gibt alle bisherigen Entscheidungen zurück."""
        return self.decisions.get("decisions", [])

    def clear_cache(self):
        """Löscht den Decision Cache."""
        self.decisions = {"decisions": [], "created_at": datetime.now().isoformat()}
        self._save_decisions()
        self.logger.info("Oracle Cache gelöscht")


def create_oracle(repo_path: str, model: str = "claude-sonnet-4-20250514") -> Oracle:
    """Factory-Funktion für Oracle-Instanz."""
    return Oracle(repo_path, model)
