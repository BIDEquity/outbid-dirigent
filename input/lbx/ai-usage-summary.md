# AI Usage in Our Company

## Overview

This document summarizes how AI is integrated across our organization — both as general-purpose productivity tooling and as purpose-built automation embedded into the software development lifecycle.

---

## General-Purpose AI Usage

### ChatGPT, Gemini, and Similar Assistants

Used company-wide as everyday productivity tools, independent of any specific lifecycle phase. Common use cases include:

- **Research & exploration** — Quick answers, technology comparisons, evaluating approaches.
- **Writing & communication** — Drafting emails, summarizing meetings, refining documentation.
- **Ad-hoc problem solving** — Debugging snippets, generating regex, explaining error messages, data analysis.
- **Learning & onboarding** — Understanding unfamiliar domains, frameworks, or internal systems faster.

**Status:** General availability

### Knowledge Management & Documentation

**ClickUp Docs synced to Teams Bot LLM**

A company-wide knowledge layer powered by an LLM-backed Teams bot, fed from ClickUp Docs. Covers three domains:

- **Product Documentation & Customer Manual** — Externally relevant content available for quick lookup and contextual answers.
- **Dev Wiki** — Best practices, architecture decisions, latest meeting protocols. Continuously updated to reflect current standards.
- **Internal Company Wiki** — Company processes, team structure, organizational knowledge.

**Status:** General availability

---

## Development Lifecycle

### 1. Concept Phase

**ConceptForge** *(WIP)*

A Claude Code plugin managing the full feature lifecycle — from stakeholder intake to release — with role-based collaboration, automatic versioning, and ClickUp integration.

Key capabilities:

- **ClickUp task ID as single entry point** — Every concept is anchored to a task.
- **Automatic versioning** — Each publish creates a new dated markdown file with incremented version number.
- **Author tracking** — Derived from git config; who changed what and when.
- **ClickUp sync** — Task description updated with the full concept on every publish.
- **HTML export** — Non-technical stakeholders can view concepts in-browser.
- **Status workflow** — Status change offered on every publish.

**Roles involved:** Product Owners, Customer Success, Dev Leads, Developers

**Status:** Work in progress

### 2. Development

**Claude-assisted coding with custom skills and rules**

Developers use Claude with a curated set of skills and rule definitions that are subject to continuous refinement. This provides context-aware assistance during active development, adapting as our practices evolve.

**Status:** Active, iterating on skill/rule definitions

### 3. Code Review

Two complementary AI-driven review layers run in the GitLab MR pipeline:

#### 3a. Claude-based Deep Review (Local Execution)

Runs locally using subscription. Analyzes the diff plus extended codebase context.

- **Inputs:** Diff, codebase context, best practices ruleset, task context from ClickUp (via MCP).
- **Checks:** Do changes match task requirements? Are best practices followed?
- **Output:** Structured review with an overall verdict.
- **Pipeline impact:** A positive verdict is required to pass the GitLab MR AI pipeline stage.
- **WIP extension:** Extract potential reasonable tests from predefined requirements and add suggestions to the review. Once this delivers reliable results, realization of suggested tests may become enforced.

#### 3b. GitLab AI Diff-based Review (Lightweight Model)

A secondary, cost-efficient model-based review operating purely on the diff.

- **Checks:** Validates that a Claude-based review exists in the diff and that the overall verdict is approved. Runs additional checks based on model assumptions.
- **Pipeline impact:** Blocking — MR cannot proceed without approval.

### 4. QA Handoff

**AI-generated manual testing instructions** *(Soft-launched, WIP)*

Automatically generates instructions for manual QA based on:

- ClickUp task description and comments
- Written code changes
- Tracked-down entrypoints and affected domains

Reduces the gap between development and manual testing by giving QA engineers structured, context-rich test guidance without requiring them to read code.

**Status:** Soft-launched, work in progress

### 5. Automated End-to-End Testing

**Computer-use model-driven blackbox E2E testing** *(Ongoing)*

Utilizing computer-use models to execute test cases written in human language.

#### Architecture

- **Test authoring:** Tests are written in ClickUp Docs in natural language.
- **Test organization:** Domain-specific test suites.
- **Synergy with code review:** Reviews can extract affected domains and suggest which suites to run, connecting review insights to test coverage.
- **Execution environment:** Suites run against a dedicated testing environment reflecting the working branch.
- **Reporting:** Results are created and reported in ClickUp tasks.

#### Result Structure (Example)

```
Agent Test DV-123:
  Selected Suites: [domain-specific suites]

  Subtasks:
  - Test 1 — Passed
  - Test 2 — In Progress
  - Test 3 — Failed
```

Results are always documented in the test-specific ClickUp task, providing full traceability from code change to test outcome.

**Status:** Ongoing development

---

## Open Questions / TODOs

### Plugin & Framework Evaluation for Claude Code

Evaluate useful plugins, frameworks, and tools to enhance the Claude-assisted development workflow and introduce them as standard tooling.

**Evaluated so far:**

- **Get Shit Done** — Tested; excessive token consumption without proportional improvement in output quality. Did not align well with our existing processes. **Dropped.**
- **RuFlo** — Currently under evaluation. Initial results are positive. Candidate for shipping as a default plugin in our Claude container setup.

**Next steps:**

- Continue evaluating RuFlo across more use cases and team members.
- Decision: ship RuFlo as default plugin in the Claude container?
- Ongoing: scout and trial additional plugins/frameworks as they emerge.

### IDE Choice: PHPStorm vs AI-Native Alternatives

Questioning whether PHPStorm is still the right default IDE given how central AI has become to our workflow.

**Current state:** PHPStorm (JetBrains) — strong PHP/Laravel tooling, refactoring, Xdebug, database integration. JetBrains AI assistant available but AI feels bolted on rather than core to the workflow.

**Alternative under consideration:** Cursor — AI-native IDE where inline edits, codebase-aware chat, and multi-file generation are first-class features. Provider-agnostic (Claude, GPT, etc.), so no lock-in to a single AI vendor. Independent pricing model with direct control over model selection.

**Considerations:**

- With BID being an Anthropic partner, Cursor's direct Claude API integration could leverage that relationship well.
- Our team already relies heavily on Claude across the entire lifecycle — an AI-native IDE would compound those gains rather than treating AI as a sidebar.
- Trade-off: PHPStorm's mature PHP-specific inspections, framework support, and debugging tooling vs. Cursor's superior AI integration.
- Cursor offers better plan flexibility and is not tied to a single AI provider's roadmap.

**Open:** Evaluate Cursor with a small group of developers to compare real-world productivity against PHPStorm.

---

## Summary

| Category | Tool / Approach | Status |
|---|---|---|
| **General Purpose** | | |
| AI Assistants | ChatGPT, Gemini, and similar | - |
| Knowledge Management | ClickUp Docs + Teams Bot LLM | - |
| **Development Lifecycle** | | |
| Concept | ConceptForge (Claude Code plugin) | WIP |
| Development | Claude + custom skills/rules | Active |
| Code Review (deep) | Claude + MCP + ClickUp context | Active |
| Code Review (lightweight) | GitLab AI diff review | Active |
| QA Handoff | AI-generated test instructions | Soft-launched, WIP |
| E2E Testing | Computer-use model + ClickUp Docs | WIP |
