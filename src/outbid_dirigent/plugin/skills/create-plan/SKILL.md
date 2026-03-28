---
name: create-plan
description: Create a phased execution plan (PLAN.json) from a spec and repo context
arguments: none - reads spec from prompt context
---

# Create Execution Plan

Generate a structured execution plan from a feature spec.

## Task

Erstelle einen Ausfuehrungsplan fuer dieses Feature basierend auf der Spec und dem Repo-Kontext.

## Output Format

Erstelle die Datei `.dirigent/PLAN.json` mit diesem Format:

```json
{
  "title": "Feature-Titel",
  "summary": "Kurze Beschreibung was implementiert wird",
  "assumptions": [
    "Annahmen die du ueber die Codebase/das Feature machst",
    "z.B. 'Tests laufen mit pytest', 'API ist REST-basiert'"
  ],
  "out_of_scope": [
    "Was NICHT Teil dieses Plans ist",
    "z.B. 'Deployment/CI-Pipeline', 'Performance-Optimierung'"
  ],
  "phases": [
    {
      "id": "01",
      "name": "Phase-Name",
      "description": "Was in dieser Phase passiert",
      "tasks": [
        {
          "id": "01-01",
          "name": "Task-Name",
          "description": "Detaillierte Beschreibung was zu tun ist",
          "files_to_create": ["liste/von/neuen/dateien.ext"],
          "files_to_modify": ["liste/von/existierenden/dateien.ext"],
          "depends_on": [],
          "model": "sonnet|haiku|opus",
          "effort": "low|medium|high",
          "test_level": "L1|L2|"
        }
      ]
    }
  ],
  "estimated_complexity": "low|medium|high",
  "risks": ["Liste von potentiellen Risiken"]
}
```

## Rules

1. Maximal 4 Phasen
2. Maximal 4 Tasks pro Phase
3. Jeder Task ist atomar (macht genau eine Sache)
4. Keine Abhaengigkeiten zwischen Tasks innerhalb einer Phase
5. Tasks muessen konkret und ausfuehrbar sein
6. Bei Legacy-Migration: Alle Business Rules muessen erhalten bleiben
7. **model**: Verwende "haiku" fuer einfache Tasks (delete files, add imports, kleine Aenderungen), "sonnet" fuer Standard-Tasks (neue Methoden, Tests, Refactoring), "opus" nur fuer sehr komplexe Architektur-Tasks
8. **effort**: "low" fuer mechanische Tasks, "medium" fuer Standard, "high" fuer komplexe Logik
9. **test_level**: "L1" wenn der Task mit Unit Tests/Lint verifiziert werden soll, "L2" wenn Integration Tests noetig sind, leer wenn kein Testing noetig
10. **assumptions**: Liste alle Annahmen ueber die Codebase auf
11. **out_of_scope**: Liste explizit auf was NICHT gemacht werden soll

## Process

1. Read and understand the spec thoroughly
2. Analyze the repo structure relevant to the feature
3. If business rules context is provided, ensure all rules are covered
4. If repo context (quick scan) is provided, use it for file targeting
5. If test manifest is provided, align test_level with available test commands
6. Create the plan with phases ordered by dependency (foundations first)
7. Write `.dirigent/PLAN.json`
