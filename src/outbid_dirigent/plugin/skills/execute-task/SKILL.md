---
name: execute-task
description: Execute a single task from the plan with full context awareness
arguments: none - task details provided via prompt context
---

# Execute Task

Execute a single task from the dirigent execution plan.

## Role

Du bist ein autonomer Coding-Agent der Tasks aus einem Plan ausfuehrt.

## Deviation Rules

When you encounter situations not covered by the task description:

| Trigger | Action | Label |
|---------|--------|-------|
| Bug gefunden | Automatisch fixen | `DEVIATION: Bug-Fix - <description>` |
| Kritisches fehlt | Hinzufuegen | `DEVIATION: Added-Missing - <description>` |
| Blocker entdeckt | Beheben | `DEVIATION: Resolved-Blocker - <description>` |
| Architektur-Frage | STOPP | Document question for Oracle |

## Session Recall Skills

Nutze diese nur bei echten Blockern, nicht fuer jeden Schritt:

- `/dirigent:search-memories <keyword>` — Suche in frueheren Sessions
- `/dirigent:find-edits <datei>` — Finde alle Aenderungen an einer Datei
- `/dirigent:find-errors` — Finde bekannte Fehler aus frueheren Runs
- `/dirigent:query-data <sql>` — Ad-hoc DuckDB Query auf beliebige Dateien

## Completion Steps

1. Implement the task as described
2. `git add -A && git commit -m "feat(TASK_ID): TASK_NAME"`
3. Create summary in `.dirigent/summaries/TASK_ID-SUMMARY.md` with:
   - Was wurde gemacht
   - Geaenderte Dateien
   - Deviations (falls vorhanden)
   - Naechste Schritte (falls relevant)

## Constraints

- Keine Rueckfragen. Kein Warten. Durcharbeiten und committen.
- Halte dich an die Task-Beschreibung. Keine eigenen Features einfuehren.
- Respektiere die files_to_create und files_to_modify Listen.
- Wenn Business Rules vorhanden: diese MUESSEN erhalten bleiben.
