---
name: refactor-plan
description: Use when asked to 'plan a refactor', 'how should I refactor this', or when a specific file is mentioned as too complex to modify safely. Requires a file path argument.
---

Produce a safe, step-by-step refactoring plan for the specified path.

## Usage

`/refactor-plan src/payments/processor.ts`

A path argument is required. If none is given, ask the user which file or directory to analyse.

## Instructions

1. **Read the target file(s)** in full before proposing anything.

2. **Check for existing tests** that cover the target. Note this explicitly — if no tests exist, Step 0 of the plan must be writing characterization tests first.

3. **Identify refactoring opportunities:**
   - Functions doing more than one thing
   - Deep nesting that obscures control flow
   - Duplicated logic that could be extracted
   - Unclear naming (names that require reading the implementation to understand)
   - Missing or wrong abstractions

4. **Output the plan to the conversation** — do not write any files or modify any source code. The engineer decides whether to save the plan.

   Plan format:

   ```markdown
   # Refactoring Plan: [filename]

   Analysed: [date]

   ## Assessment

   [2–3 sentences: what is wrong and why it matters for maintainability or reliability]

   ## Pre-conditions

   - [ ] Tests exist covering [list the key behaviours to lock in] — or complete Step 0 first
   - [ ] No open PRs currently touching this file

   ## Steps

   ### Step 0: Write characterization tests (skip if tests already exist)

   **Why:** You need a safety net before moving anything. These tests do not need to be elegant — they just need to lock in the current behaviour so a regression is immediately visible.

   **What to test:** [list specific functions and observable behaviours]

   **Risk:** Low

   **Commit:** `test: add characterization tests for [filename]`

   ---

   ### Step 1: [Smallest, safest change first]

   **What:** [e.g., "Extract the email validation logic into a standalone `validateEmail(input: string): boolean` function"]

   **Why:** [what problem this solves — one sentence]

   **How:**
   1. [Concrete instruction — e.g., "Create `src/utils/validate-email.ts` exporting `validateEmail`"]
   2. [e.g., "Move lines 42–58 from `processor.ts` into the new function"]
   3. [e.g., "Replace the original block with a call to `validateEmail(input)`"]

   **Risk:** Low — pure extraction, no behaviour change

   **Commit:** `refactor: extract validateEmail into utils`

   ---

   [Repeat for each subsequent step, smallest/safest first. Each step is independently committable.]

   ## Out of scope

   [Changes that were considered but excluded — and why. E.g., "Splitting the file into separate modules — that is a larger architectural change that should follow once coverage is established."]
   ```

5. After outputting the plan, remind the engineer:
   > This is a plan only. Start a new session to execute the steps, or ask me to begin Step 0 now.
