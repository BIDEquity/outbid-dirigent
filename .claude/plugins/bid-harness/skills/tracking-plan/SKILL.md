---
name: tracking-plan
description: Use when asked to 'create a tracking plan', 'document our analytics events', 'we need a tracking plan', or when assess flags Section 07 product tracking rows as failing.
---

Create or update the product analytics tracking plan.

## Before you begin

Check if `harness-docs/standards-status.md` exists in this repository.
- If it does **not** exist: run `/assess` first to establish a baseline, then return here and continue.
- If it exists: read the rows for `## 07 · Observability, Monitoring & Tracking` to understand which product tracking items are currently failing.

## Instructions

1. **Check if `harness-docs/tracking-plan.md` already exists.** If it does, read it and offer to update it rather than replacing it.

2. **Ask the user for:**
   - Product area (e.g. "Checkout", "Onboarding", "Settings")
   - 3–5 key user interactions to instrument first (e.g. "user signs up", "order placed", "password reset requested")
   - Event name convention they prefer: `noun_verb` (e.g. `order_placed`) or `Verb Noun` (e.g. `Order Placed`)

3. **Scaffold `harness-docs/tracking-plan.md`** from `harness-docs/templates/tracking-plan-template.md` (if it exists) or using this structure. Populate the events described. Each event requires: event name, trigger, properties table, owner.

   ```markdown
   # Tracking Plan

   _Last updated: YYYY-MM-DD. Owner: [team name]._

   ## Event naming convention

   [Describe the agreed convention, e.g.: snake_case noun_verb: `order_placed`, `user_signed_up`]

   ## Events

   ### `order_placed`

   **Trigger:** User clicks "Confirm Order" on the checkout summary page.

   **Properties:**

   | Property | Type | Example | Notes |
   |----------|------|---------|-------|
   | `order_id` | string | `ord_abc123` | Server-generated |
   | `total_amount_cents` | integer | `4999` | In smallest currency unit |
   | `item_count` | integer | `3` | |
   | `user_id` | string | `usr_xyz789` | Authenticated user |

   **Owner:** payments-team

   ---

   ### `user_signed_up`

   **Trigger:** New user account is created successfully (server-side, after email verification if applicable).

   **Properties:**

   | Property | Type | Example | Notes |
   |----------|------|---------|-------|
   | `user_id` | string | `usr_xyz789` | |
   | `signup_method` | string | `email` | `email`, `google`, `github` |
   | `referral_source` | string | `organic` | UTM source if available |

   **Owner:** growth-team

   ---
   ```

4. **After saving the file**, remind the user:
   - Per engineering-standards.md § 07, events must be schema-validated in CI before shipping
   - If CI is not yet configured: run `/add-ci` first, then add a tracking plan validation step

## Update the status file

After creating or updating the tracking plan, update `harness-docs/standards-status.md`:

1. Find the section heading `## 07 · Observability, Monitoring & Tracking`.
2. For each row below, update Status to `✅ PASS`, Verified to today's date, Fixed By to `/tracking-plan`, Notes to the file path and number of events documented:
   - Row matching "Maintain a tracking plan"
   - Row matching "every significant user interaction must have a named event, defined properties, and a documented owner"
3. Recalculate the MUST ✅ and MUST ❌ totals in the Summary table for the `07 · Observability, Monitoring & Tracking` row.
