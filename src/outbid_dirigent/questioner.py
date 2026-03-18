#!/usr/bin/env python3
"""
Outbid Dirigent - Interactive Questioner
Ermöglicht Fragen an User via Portal.
"""

import os
import time
import requests
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from outbid_dirigent.logger import get_logger


@dataclass
class QuestionResult:
    """Ergebnis einer Frage."""
    answered: bool
    answer: Optional[str]
    timeout: bool
    skipped: bool = False


class Questioner:
    """Stellt Fragen an User via Portal und wartet auf Antworten."""

    POLL_INTERVAL = 5  # Sekunden

    def __init__(
        self,
        portal_url: str,
        reporter_token: str,
        execution_id: str,
        timeout_minutes: int = 30,
    ):
        self.portal_url = portal_url.rstrip('/')
        self.reporter_token = reporter_token
        self.execution_id = execution_id
        self.timeout_minutes = timeout_minutes
        self.logger = get_logger()
        self._enabled = True

    def disable(self):
        """Deaktiviert den Questioner (für non-interactive Mode)."""
        self._enabled = False

    def is_enabled(self) -> bool:
        """Prüft ob der Questioner aktiviert ist."""
        return self._enabled

    def is_active(self) -> bool:
        """Alias für is_enabled() - für Kompatibilität mit Oracle."""
        return self._enabled

    def set_logger(self, logger):
        """Setzt den Logger (optional, da bereits in __init__ gesetzt)."""
        self.logger = logger

    def ask(
        self,
        question: str,
        options: Optional[List[str]] = None,
        context: Optional[str] = None,
        task_id: Optional[str] = None,
        phase: Optional[int] = None,
        question_type: str = "choice",
        default_on_timeout: Optional[str] = None,
    ) -> QuestionResult:
        """
        Stellt eine Frage und wartet auf Antwort.

        Args:
            question: Die Frage
            options: Liste von Auswahlmöglichkeiten
            context: Zusätzlicher Kontext
            task_id: Aktueller Task
            phase: Aktuelle Phase
            question_type: 'choice', 'text', oder 'confirm'
            default_on_timeout: Standardantwort bei Timeout

        Returns:
            QuestionResult mit Antwort oder Timeout-Info
        """
        if not self._enabled:
            self.logger.debug(f"Questioner deaktiviert, überspringe Frage: {question[:50]}...")
            return QuestionResult(answered=False, answer=None, timeout=False, skipped=True)

        self.logger.info(f"Frage an User: {question[:100]}...")

        # Event an Portal senden
        try:
            response = requests.post(
                f"{self.portal_url}/api/execution-event",
                headers={"X-Reporter-Token": self.reporter_token},
                json={
                    "execution_id": self.execution_id,
                    "event": {
                        "type": "question",
                        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "data": {
                            "question": question,
                            "options": options,
                            "context": context,
                            "taskId": task_id,
                            "phase": phase,
                            "questionType": question_type,
                            "timeoutMinutes": self.timeout_minutes,
                        }
                    }
                },
                timeout=30,
            )

            if response.status_code != 200:
                self.logger.error(f"Frage konnte nicht gesendet werden: {response.text}")
                if default_on_timeout:
                    self.logger.info(f"Nutze Default-Antwort: {default_on_timeout}")
                    return QuestionResult(answered=True, answer=default_on_timeout, timeout=True)
                return QuestionResult(answered=False, answer=None, timeout=False)

            data = response.json()
            question_id = data.get("question_id")
            if not question_id:
                self.logger.error("Keine question_id erhalten")
                if default_on_timeout:
                    return QuestionResult(answered=True, answer=default_on_timeout, timeout=True)
                return QuestionResult(answered=False, answer=None, timeout=False)

        except requests.RequestException as e:
            self.logger.error(f"Netzwerk-Fehler beim Senden der Frage: {e}")
            if default_on_timeout:
                return QuestionResult(answered=True, answer=default_on_timeout, timeout=True)
            return QuestionResult(answered=False, answer=None, timeout=False)

        # Polling für Antwort
        self.logger.info(f"Warte auf Antwort (max {self.timeout_minutes} Min)...")

        max_polls = (self.timeout_minutes * 60) // self.POLL_INTERVAL
        for poll_num in range(max_polls):
            time.sleep(self.POLL_INTERVAL)

            try:
                poll_response = requests.get(
                    f"{self.portal_url}/api/poll-answer",
                    headers={"X-Reporter-Token": self.reporter_token},
                    params={"question_id": question_id},
                    timeout=30,
                )

                if poll_response.status_code == 200:
                    poll_data = poll_response.json()

                    if poll_data.get("answered"):
                        answer = poll_data.get("answer")
                        self.logger.info(f"Antwort erhalten: {answer}")
                        return QuestionResult(answered=True, answer=answer, timeout=False)

                    if poll_data.get("timeout"):
                        self.logger.info("Frage-Timeout erreicht")
                        if default_on_timeout:
                            self.logger.info(f"Nutze Default-Antwort: {default_on_timeout}")
                            return QuestionResult(answered=True, answer=default_on_timeout, timeout=True)
                        return QuestionResult(answered=False, answer=None, timeout=True)

            except requests.RequestException as e:
                self.logger.debug(f"Polling-Fehler (Versuch {poll_num + 1}): {e}")
                # Weiter versuchen

            # Progress-Log alle 30 Sekunden
            if (poll_num + 1) % 6 == 0:
                elapsed = (poll_num + 1) * self.POLL_INTERVAL
                remaining = (self.timeout_minutes * 60) - elapsed
                self.logger.debug(f"Warte auf Antwort... ({remaining // 60} Min verbleibend)")

        # Polling-Timeout
        self.logger.info("Polling-Timeout erreicht")
        if default_on_timeout:
            self.logger.info(f"Nutze Default-Antwort: {default_on_timeout}")
            return QuestionResult(answered=True, answer=default_on_timeout, timeout=True)
        return QuestionResult(answered=False, answer=None, timeout=True)

    def confirm(
        self,
        question: str,
        context: Optional[str] = None,
        task_id: Optional[str] = None,
        phase: Optional[int] = None,
        default_on_timeout: bool = True,
    ) -> bool:
        """
        Stellt eine Ja/Nein Frage.

        Args:
            question: Die Ja/Nein Frage
            context: Zusätzlicher Kontext
            task_id: Aktueller Task
            phase: Aktuelle Phase
            default_on_timeout: Default bei Timeout (True = Ja)

        Returns:
            True für Ja, False für Nein
        """
        result = self.ask(
            question=question,
            options=["Ja", "Nein"],
            context=context,
            task_id=task_id,
            phase=phase,
            question_type="confirm",
            default_on_timeout="Ja" if default_on_timeout else "Nein",
        )

        if result.answered and result.answer:
            return result.answer.lower() in ["ja", "yes", "true", "1"]
        return default_on_timeout

    def choose(
        self,
        question: str,
        options: List[str],
        context: Optional[str] = None,
        task_id: Optional[str] = None,
        phase: Optional[int] = None,
        default_on_timeout: Optional[str] = None,
    ) -> Optional[str]:
        """
        Stellt eine Multiple-Choice Frage.

        Args:
            question: Die Frage
            options: Liste von Optionen
            context: Zusätzlicher Kontext
            task_id: Aktueller Task
            phase: Aktuelle Phase
            default_on_timeout: Default-Option bei Timeout

        Returns:
            Die gewählte Option oder None
        """
        if default_on_timeout is None and options:
            default_on_timeout = options[0]

        result = self.ask(
            question=question,
            options=options,
            context=context,
            task_id=task_id,
            phase=phase,
            question_type="choice",
            default_on_timeout=default_on_timeout,
        )

        return result.answer if result.answered else None

    def ask_text(
        self,
        question: str,
        context: Optional[str] = None,
        task_id: Optional[str] = None,
        phase: Optional[int] = None,
        default_on_timeout: str = "",
    ) -> str:
        """
        Stellt eine Freitext-Frage.

        Args:
            question: Die Frage
            context: Zusätzlicher Kontext
            task_id: Aktueller Task
            phase: Aktuelle Phase
            default_on_timeout: Default-Text bei Timeout

        Returns:
            Die Antwort oder der Default
        """
        result = self.ask(
            question=question,
            options=None,
            context=context,
            task_id=task_id,
            phase=phase,
            question_type="text",
            default_on_timeout=default_on_timeout,
        )

        return result.answer if result.answered and result.answer else default_on_timeout

    def submit_plan_for_approval(
        self,
        plan_content: Dict[str, Any],
        timeout_minutes: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Sendet Plan zur Genehmigung und wartet auf Antwort.

        Args:
            plan_content: Der Plan als Dict (aus PLAN.json)
            timeout_minutes: Timeout für Genehmigung (default: self.timeout_minutes)

        Returns:
            Dict mit:
                - status: 'approved' | 'rejected' | 'edited' | 'timeout' | 'error'
                - plan: Der (ggf. editierte) Plan
                - message: Optional Nachricht vom User
        """
        if not self._enabled:
            self.logger.debug("Questioner deaktiviert, überspringe Plan-Approval")
            return {"status": "approved", "plan": plan_content, "message": None}

        timeout = timeout_minutes or self.timeout_minutes
        self.logger.info(f"Plan zur Genehmigung gesendet (Timeout: {timeout}min)")

        # Plan-Event an Portal senden
        try:
            response = requests.post(
                f"{self.portal_url}/api/execution-event",
                headers={"X-Reporter-Token": self.reporter_token},
                json={
                    "execution_id": self.execution_id,
                    "event": {
                        "type": "plan",
                        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "data": {
                            "planContent": plan_content,
                            "timeoutMinutes": timeout,
                        }
                    }
                },
                timeout=30,
            )

            if response.status_code != 200:
                self.logger.error(f"Plan konnte nicht gesendet werden: {response.text}")
                return {"status": "error", "plan": plan_content, "message": response.text}

        except requests.RequestException as e:
            self.logger.error(f"Netzwerkfehler beim Plan-Senden: {e}")
            return {"status": "error", "plan": plan_content, "message": str(e)}

        # Auf Genehmigung pollen
        start_time = time.time()
        timeout_seconds = timeout * 60

        while True:
            elapsed = time.time() - start_time
            if elapsed >= timeout_seconds:
                self.logger.warn(f"Plan-Approval Timeout nach {timeout}min")
                return {"status": "timeout", "plan": plan_content, "message": None}

            try:
                poll_response = requests.get(
                    f"{self.portal_url}/api/poll-plan-approval",
                    params={
                        "execution_id": self.execution_id,
                        "reporter_token": self.reporter_token,
                    },
                    timeout=30,
                )

                if poll_response.status_code == 200:
                    data = poll_response.json()
                    status = data.get("status")

                    if status == "pending":
                        # Noch keine Entscheidung, weiter pollen
                        remaining = int((timeout_seconds - elapsed) / 60)
                        self.logger.debug(f"Warte auf Plan-Approval... ({remaining}min verbleibend)")
                        time.sleep(self.POLL_INTERVAL)
                        continue

                    elif status == "approved":
                        self.logger.info("Plan genehmigt")
                        return {"status": "approved", "plan": plan_content, "message": None}

                    elif status == "rejected":
                        message = data.get("message", "Keine Begründung angegeben")
                        self.logger.warn(f"Plan abgelehnt: {message}")
                        return {"status": "rejected", "plan": plan_content, "message": message}

                    elif status == "edited":
                        edited_plan = data.get("plan", plan_content)
                        self.logger.info("Plan wurde editiert und genehmigt")
                        return {"status": "edited", "plan": edited_plan, "message": None}

                    else:
                        self.logger.warn(f"Unbekannter Plan-Status: {status}")
                        time.sleep(self.POLL_INTERVAL)
                        continue

                else:
                    self.logger.debug(f"Poll-Fehler: {poll_response.status_code}")
                    time.sleep(self.POLL_INTERVAL)

            except requests.RequestException as e:
                self.logger.debug(f"Poll-Netzwerkfehler: {e}")
                time.sleep(self.POLL_INTERVAL)


def create_questioner(
    portal_url: str,
    reporter_token: str,
    execution_id: str,
    timeout_minutes: int = 30,
) -> Questioner:
    """Factory-Funktion für Questioner-Instanz."""
    return Questioner(portal_url, reporter_token, execution_id, timeout_minutes)


# Dummy Questioner für non-interactive Mode
class DummyQuestioner:
    """Dummy-Questioner der alle Fragen überspringt."""

    def __init__(self):
        self.logger = get_logger()

    def is_enabled(self) -> bool:
        return False

    def is_active(self) -> bool:
        """Alias für is_enabled() - für Kompatibilität."""
        return False

    def ask(self, question: str, **kwargs) -> QuestionResult:
        self.logger.debug(f"[NON-INTERACTIVE] Frage übersprungen: {question[:50]}...")
        return QuestionResult(answered=False, answer=None, timeout=False, skipped=True)

    def confirm(self, question: str, default_on_timeout: bool = True, **kwargs) -> bool:
        self.logger.debug(f"[NON-INTERACTIVE] Confirm übersprungen: {question[:50]}...")
        return default_on_timeout

    def choose(self, question: str, options: List[str], default_on_timeout: Optional[str] = None, **kwargs) -> Optional[str]:
        self.logger.debug(f"[NON-INTERACTIVE] Choice übersprungen: {question[:50]}...")
        return default_on_timeout or (options[0] if options else None)

    def ask_text(self, question: str, default_on_timeout: str = "", **kwargs) -> str:
        self.logger.debug(f"[NON-INTERACTIVE] Text-Frage übersprungen: {question[:50]}...")
        return default_on_timeout

    def submit_plan_for_approval(
        self,
        plan_content: Dict[str, Any],
        timeout_minutes: Optional[int] = None,
    ) -> Dict[str, Any]:
        self.logger.debug("[NON-INTERACTIVE] Plan-Approval übersprungen")
        return {"status": "approved", "plan": plan_content, "message": None}


def create_dummy_questioner() -> DummyQuestioner:
    """Factory-Funktion für Dummy-Questioner."""
    return DummyQuestioner()
