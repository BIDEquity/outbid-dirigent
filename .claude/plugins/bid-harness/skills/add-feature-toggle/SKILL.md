---
name: add-feature-toggle
description: Use when asked to 'add feature flags', 'set up feature toggles', 'we need a toggle system', or when assess flags Section 06 as failing.
---

Set up a feature toggle system for this repository.

## Before you begin

Check if `harness-docs/standards-status.md` exists in this repository.
- If it does **not** exist: run `/assess` first to establish a baseline, then return here and continue.
- If it exists: read the rows for `## 06 · Feature Toggles` to understand which toggle-related items are currently failing before scaffolding.

## Instructions

1. **Detect existing toggle library.** Scan the codebase for evidence of: PostHog, LaunchDarkly, Unleash, GrowthBook, Flagsmith, or a home-grown `features/` module.
   - If one is already present: skip to step 4 (configuration review).

2. **Default choice: PostHog.** Install the stack-appropriate PostHog SDK unless the user requests an alternative (LaunchDarkly, Unleash, GrowthBook, or Flagsmith):

   | Stack | Package |
   |-------|---------|
   | TypeScript/JS | `posthog-node` (server) or `posthog-js` (browser) |
   | Python | `posthog` |
   | Go | `github.com/posthog/posthog-go` |
   | Java | `com.posthog.java:posthog` (Maven/Gradle) |

3. **Scaffold a central feature wrapper.** Create a thin wrapper at the appropriate path — all callers import this file; no direct PostHog calls outside it:

   | Stack | Path |
   |-------|------|
   | TypeScript | `src/lib/features.ts` |
   | Python | `app/features.py` (or `src/<package>/features.py`) |
   | Go | `internal/features/features.go` |
   | Java | `src/main/java/<package>/features/Features.java` |

   The wrapper must:
   - Initialise the PostHog client once (singleton pattern)
   - Expose a typed `isEnabled(flag, userId)` function (or idiomatic equivalent)
   - Define a `FeatureFlag` enum/type listing all known flags with their category
   - Each flag entry includes: `owner`, `created_date`, `planned_removal_date`

   **TypeScript example (`src/lib/features.ts`):**

   ```typescript
   import { PostHog } from 'posthog-node';

   // Central feature flag registry — add new flags here before using them.
   // Flags active > 90 days without a planned_removal_date review are tech debt.
   export enum FeatureFlag {
     // Release (temporary) — remove once fully rolled out
     NEW_CHECKOUT_FLOW = 'new-checkout-flow',
   }

   export const FLAG_METADATA: Record<FeatureFlag, {
     category: 'release' | 'experiment' | 'ops' | 'permission';
     owner: string;
     created_date: string;
     planned_removal_date: string;
   }> = {
     [FeatureFlag.NEW_CHECKOUT_FLOW]: {
       category: 'release',
       owner: 'payments-team',
       created_date: 'YYYY-MM-DD',
       planned_removal_date: 'YYYY-MM-DD',
     },
   };

   let client: PostHog | null = null;

   function getClient(): PostHog {
     if (!client) {
       client = new PostHog(process.env.POSTHOG_API_KEY!, {
         host: process.env.POSTHOG_HOST ?? 'https://app.posthog.com',
       });
     }
     return client;
   }

   export async function isEnabled(flag: FeatureFlag, distinctId: string): Promise<boolean> {
     return (await getClient().isFeatureEnabled(flag, distinctId)) ?? false;
   }
   ```

   **Python example (`app/features.py`):**

   ```python
   import os
   from enum import Enum
   from posthog import Posthog

   # Central feature flag registry.
   # Flags active > 90 days without a planned_removal_date review are tech debt.
   class FeatureFlag(str, Enum):
       NEW_CHECKOUT_FLOW = "new-checkout-flow"  # release — owner: payments-team, expires: 2026-07-13

   _client: Posthog | None = None

   def _get_client() -> Posthog:
       global _client
       if _client is None:
           _client = Posthog(
               os.environ["POSTHOG_API_KEY"],
               host=os.getenv("POSTHOG_HOST", "https://app.posthog.com"),
           )
       return _client

   def is_enabled(flag: FeatureFlag, distinct_id: str) -> bool:
       return _get_client().feature_enabled(flag.value, distinct_id) or False
   ```

   **Go example (`internal/features/features.go`):**

   ```go
   package features

   import (
       "os"
       "sync"

       "github.com/posthog/posthog-go"
   )

   // FeatureFlag is the central registry of all feature flags.
   // Flags active > 90 days without a PlannedRemovalDate review are tech debt.
   type FeatureFlag string

   const (
       // NewCheckoutFlow is a release toggle — owner: payments-team, expires: 2026-07-13
       NewCheckoutFlow FeatureFlag = "new-checkout-flow"
   )

   var (
       once   sync.Once
       client posthog.Client
   )

   func getClient() posthog.Client {
       once.Do(func() {
           client, _ = posthog.NewWithConfig(
               os.Getenv("POSTHOG_API_KEY"),
               posthog.Config{Endpoint: getenv("POSTHOG_HOST", "https://app.posthog.com")},
           )
       })
       return client
   }

   func IsEnabled(flag FeatureFlag, distinctID string) bool {
       enabled, _ := getClient().IsFeatureEnabled(posthog.FeatureFlagPayload{
           Key:        string(flag),
           DistinctId: distinctID,
       })
       return enabled == true
   }

   func getenv(key, fallback string) string {
       if v := os.Getenv(key); v != "" {
           return v
       }
       return fallback
   }
   ```

4. **Configuration review (if toggle library already present).** Check existing toggle usage for:
   - Flags missing `owner`, `created_date`, or `planned_removal_date`
   - No central registry file — callers import the SDK directly
   Report findings and offer to scaffold the central wrapper on top of the existing library.

5. **Remind the user:**
   - Set `POSTHOG_API_KEY` in the environment / secrets manager before deploying
   - Add `POSTHOG_API_KEY` to `.env.example` with a placeholder value — never to `.env` itself
   - Never hardcode the API key in source

## Update the status file

After scaffolding the feature toggle setup, update `harness-docs/standards-status.md`:

1. Find the section heading `## 06 · Feature Toggles`.
2. For each row below, update Status to `✅ PASS`, Verified to today's date, Fixed By to `/add-feature-toggle`, and Notes to the wrapper file path created:
   - Row matching "Deploy unfinished features to production behind a toggle"
   - Row matching "Explicitly distinguish toggle types" (if the wrapper includes the four typed categories)
   - Row matching "Assign every toggle an owner, creation date, and planned removal date" (if metadata fields were added)
   - Row matching "Use a central feature toggle service or library"
3. Recalculate the MUST ✅ and MUST ❌ totals in the Summary table for the `06 · Feature Toggles` row.
