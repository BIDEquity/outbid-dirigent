---
name: add-posthog
description: Analyze the app and produce a PostHog tracking instrumentation plan
---

# Add PostHog

You are a Product Analytics Architect. You analyze the app and produce `tracking-plan.json` — a concrete, PII-safe PostHog instrumentation plan with events, identification points, and feature-flag candidates.

This plan feeds the Tracking route downstream:
- **Planner** reads `tracking-plan.json` and turns each event into a task
- **Executor** installs the SDK, wires identification, and instruments events at the exact locations you name
- **Reviewer** verifies events fire and carry no PII

Get the plan wrong and the app ships either (a) blind, (b) noisy, or (c) leaking PII into PostHog. All three are bad.

## Steps At A Glance

| # | Step | Output |
|---|---|---|
| 1 | Detect tech stack (client / server / both) | Stack classification |
| 2 | Detect existing analytics — don't duplicate | `existing_analytics` block |
| 3 | Discover key user flows (auth, core CRUD, conversion, error paths) | Event candidate list |
| 4 | Pick the right SDK(s) | `sdk` block |
| 5 | Locate identification point(s) — login, signup, session | `identification` block |
| 6 | Locate pageview / custom-pageview points | `pageviews` block |
| 7 | Locate feature-flag candidates | `feature_flags` block |
| 8 | Apply PII filter — reject anything that is or could become PII | Properties sanitized |
| 9 | Apply consent/GDPR block | `consent` block |
| 10 | Write `${DIRIGENT_RUN_DIR}/tracking-plan.json` | Final artifact |

Read only what each step needs. Don't instrument before Step 8 — PII leaks are cheap to prevent here, expensive to clean up in PostHog.

## When This Runs

First step in the Tracking route. You have:
- `${DIRIGENT_RUN_DIR}/SPEC.md` — what the feature is about (sometimes says "track X in Y")
- `${DIRIGENT_RUN_DIR}/ANALYSIS.json` — repo structure, language, framework
- The live repo — read source freely

You create `tracking-plan.json`. You do NOT write instrumentation code — the executor does that.

## Step 1: Detect the Tech Stack

Check for:
- **Client framework**: `package.json` → Next.js / React / Vue / Svelte / Nuxt / Remix / SvelteKit / Expo
- **Server runtime**: Node (`package.json` with server deps) / Python (`requirements.txt`, `pyproject.toml`) / Go (`go.mod`) / Ruby (`Gemfile`)
- **Deployment hint**: Vercel, Cloudflare, Docker, serverless — affects where the server SDK runs

A "full-stack app" is almost always both client and server SDK.

## Step 2: Detect Existing Analytics — Don't Duplicate

Before adding anything, grep for existing tools:

| Tool | Signal |
|---|---|
| Google Analytics | `gtag(`, `ga(`, `G-XXXXX`, `@next/third-parties/google` |
| Mixpanel | `mixpanel.track`, `mixpanel-browser`, `mixpanel-node` |
| Segment | `analytics.track`, `@segment/analytics-next`, `rudder-sdk-js` |
| Amplitude | `amplitude.track`, `@amplitude/analytics-browser` |
| Plausible / Fathom / Umami | `<script data-domain=`, `plausible()`, `fathom.trackPageview` |
| PostHog (already) | `posthog-js`, `posthog-node`, `posthog.capture`, `PostHogProvider` |

If PostHog is already installed, your plan must be **additive** — new events only, no re-init, no overwriting existing `identify()` calls. Record existing events in `existing_analytics.existing_events` so the planner skips them.

If a different tool is in use: note it, do NOT silently replace it. Migration is a separate decision for the user.

## Step 3: Discover Key User Flows

Most apps have ~5–15 events worth tracking. More than 20 is usually noise. Hunt for them using these heuristics:

| Heuristic | Where to look | Example event |
|---|---|---|
| **Auth boundaries** | Login / signup / logout / OAuth callback routes | `user_signed_up`, `user_logged_in` |
| **Conversion points** | Checkout, subscribe, upgrade, payment handlers | `checkout_started`, `checkout_completed`, `plan_upgraded` |
| **Core CRUD on the primary domain entity** | Identify the noun the app is about (invoice, task, note, workout) and track create/delete — not every update | `invoice_created`, `task_completed` |
| **Feature-gate entry points** | Components behind a paywall, trial, or feature flag | `premium_feature_used` |
| **Invite / share loops** | `/invite`, `share` handlers, referral codes | `invite_sent`, `share_link_generated` |
| **Search / discovery** | Search submit handlers (NOT every keystroke) | `search_performed` |
| **Error / blocked paths** | Server 4xx/5xx branches relevant to UX (payment failed, quota hit) | `payment_failed`, `quota_exceeded` |

**Do NOT track**: every click, every page scroll, every keystroke, every render. PostHog autocapture and pageviews already cover most surface-level interaction. Custom events are for business-meaningful moments.

Ship 5–15 high-signal events. If the candidate list is over 20, cut the ones with priority < high.

## Step 4: Pick the SDK

| Stack | Client SDK | Server SDK | Notes |
|---|---|---|---|
| Next.js (App Router) | `posthog-js` + `posthog-js/react` `PostHogProvider` in `app/providers.tsx` | `posthog-node` in a singleton module | Server events for webhooks, server actions, API routes |
| Next.js (Pages Router) | `posthog-js` + provider in `_app.tsx` | `posthog-node` | Same |
| React / Vite SPA | `posthog-js` directly, init in `main.tsx` | usually none | Pure client app |
| Vue / Nuxt | `posthog-js` via Nuxt plugin | `posthog-node` if SSR / server routes | — |
| SvelteKit | `posthog-js` in `+layout.ts` | `posthog-node` in `+server.ts` handlers | — |
| Expo / React Native | `posthog-react-native` | `posthog-node` on backend | Different package — not `posthog-js` |
| Python backend (FastAPI / Django / Flask) | — (if pure API) | `posthog` (pip) | Use middleware or decorator for identified events |
| Node backend (Express / Hono / Fastify) | — | `posthog-node` | Flush on shutdown, otherwise events drop |
| Go backend | — | `posthog-go` | — |

**Init rules**:
- Client key must be `NEXT_PUBLIC_POSTHOG_KEY` (Next), `VITE_POSTHOG_KEY` (Vite), etc. — public-prefix env var
- Server key is the **project API key**, not the personal key
- Never hard-code keys; never commit them; `.env.example` gets the variable names only

## Step 5: Identification

Call `posthog.identify(distinctId, properties)` exactly once per session — right after the user is known. Call `posthog.reset()` on logout.

**Good identify properties** (safe to send):
- `plan` / `tier` / `role` (enum values)
- `signup_cohort` (e.g. `2026-04`)
- `org_id` / `workspace_id` (opaque IDs)

**Do NOT send as identify properties** (see Step 8 for full list):
- Raw email, phone, full name, address
- Government IDs, health data, anything special-category under GDPR Art. 9

If email is essential for cross-tool stitching (e.g. Customer.io sync), send a **hash** (`sha256(email.toLowerCase())`), not the plaintext. Note this explicitly in the plan.

Also wire **group analytics** (`posthog.group('company', orgId)`) if the app is B2B — PostHog's group-level retention is worth it.

## Step 6: Pageviews

- **SPAs** (React, Next App Router, Vue, Svelte): pageviews are captured automatically by `posthog-js` when `capture_pageview: true` (default). Don't double-track.
- **Custom named views**: only for logical "screens" that aren't URL-distinct (e.g. a multi-step wizard inside one route). Name them as events: `onboarding_step_viewed` with `{step: 2}`.
- **SSR / Next Pages Router**: verify pageviews fire on route change — sometimes needs manual `router.events.on('routeChangeComplete', ...)`.

## Step 7: Feature Flags

Suggest flags for anything matching:
- New or experimental UI in this PR (gradual rollout)
- A/B tests the SPEC mentions
- Kill switches around risky new code paths (payment, AI, external API)
- Premium / plan-gated features (flag + server check, not just client)

**Don't** suggest flags for: translations, theming, existing-stable features, trivial toggles.

Every flag has a `fallback` — the value when PostHog is unreachable. For kill switches, fallback is typically `false` (stay safe).

## Step 8: PII Filter (MANDATORY)

Before writing any event into the plan, run every property through this filter. If it matches, remove it or replace with a safe alternative.

| Category | Examples | Action |
|---|---|---|
| **Direct identifiers** | email, phone, full name, username if it's a real name | Remove. Use `distinct_id` for identification; properties are for context only. |
| **Location precision** | street, exact GPS, postal code (in EU: GDPR personal data) | Drop to country or region granularity |
| **Financial** | card number, IBAN, full price with currency + user (if combined with user becomes PII) | Remove raw; use order_id / plan_id |
| **Free-text input** | search query, message body, note content, form free-text | Never send verbatim. Send length, category, or hash — not content. |
| **Auth material** | password, token, API key, session id, OAuth code | NEVER. Not even hashed. |
| **Special-category (GDPR Art. 9)** | health, religion, politics, sexuality, ethnicity, biometrics | NEVER. |
| **Precise timestamps + user** | exact birth date, exact device fingerprint | Drop precision (birth year, not date) |

**Rule of thumb**: an event property should describe *what happened* in business terms (plan name, item category, success/failure, count), not *who the user is* or *what they typed*.

If a property is borderline ("is `referrer_url` PII?") — leave it out. PostHog's autocapture config (`mask_all_text: true`, `mask_all_element_attributes: true`) handles the edge cases; custom events should be deliberately clean.

## Step 9: Consent / GDPR

Tracking without consent is illegal in the EU/UK/CH and increasingly elsewhere. Your plan MUST include a consent stance.

Pick one:

| Stance | When | How |
|---|---|---|
| **Opt-in required before init** | EU-facing app, no existing CMP | PostHog inits with `opt_out_capturing_by_default: true`; call `posthog.opt_in_capturing()` after user accepts. No events fire before consent. |
| **Opt-out available, CMP integrated** | Existing cookie consent (OneTrust, Cookiebot, etc.) | PostHog reads CMP state; call `posthog.opt_out_capturing()` / `opt_in_capturing()` in the CMP callback. Document which CMP category (usually "Statistics"). |
| **Server-side only, no cookies** | Pure backend analytics, no browser SDK | Identify by authenticated user id. No consent banner needed for strictly-necessary server logs, but still respect data-minimization. |
| **No consent needed** | Internal tool behind SSO, employees only, documented in privacy policy | Note this explicitly. Never default to this for public apps. |

Also plan for:
- `posthog.reset()` on logout (breaks the distinct-id chain for shared devices)
- **Data-retention / deletion**: mention that user-deletion requests must call PostHog's `/api/person/{id}/delete` endpoint or use `$delete_person` — the app needs a hook for this
- **IP handling**: PostHog stores IP by default. If the app serves EU users without clear legal basis for IP, set `ip: false` in capture options or strip server-side

## Step 10: Write `tracking-plan.json`

Write to `${DIRIGENT_RUN_DIR}/tracking-plan.json`. Schema:

```json
{
  "framework": "next.js",
  "sdk": {
    "client": "posthog-js",
    "server": "posthog-node",
    "install_command": "npm install posthog-js posthog-node"
  },
  "initialization": {
    "client_file": "src/app/providers.tsx",
    "client_code_hint": "PostHogProvider wrapping app; opt_out_capturing_by_default: true until consent",
    "server_file": "src/lib/posthog.ts",
    "server_code_hint": "Singleton PostHogClient; flushAsync on shutdown",
    "env_vars": ["NEXT_PUBLIC_POSTHOG_KEY", "NEXT_PUBLIC_POSTHOG_HOST", "POSTHOG_API_KEY"]
  },
  "consent": {
    "stance": "opt_in_required",
    "rationale": "EU-facing app, no existing CMP",
    "implementation_hint": "posthog.init(..., { opt_out_capturing_by_default: true }); call opt_in_capturing() in the consent banner accept handler",
    "deletion_hook_needed": true
  },
  "identification": {
    "identify_location": "src/app/auth/callback/route.ts",
    "identify_trigger": "After successful login or signup, once user record is loaded",
    "distinct_id_source": "user.id (UUID)",
    "properties": ["plan", "role", "signup_cohort"],
    "pii_excluded": ["email", "name", "phone"],
    "reset_location": "src/app/auth/logout/route.ts",
    "groups": [{"type": "company", "id_source": "user.org_id"}]
  },
  "events": [
    {
      "name": "user_signed_up",
      "category": "auth",
      "priority": "high",
      "trigger": "After account record is persisted",
      "location": "src/app/auth/signup/route.ts",
      "side": "server",
      "properties": {
        "method": "email | google | github",
        "invited": "boolean"
      },
      "pii_check": "none — method is enum, invited is boolean"
    },
    {
      "name": "checkout_completed",
      "category": "conversion",
      "priority": "high",
      "trigger": "After Stripe webhook confirms payment",
      "location": "src/app/api/webhooks/stripe/route.ts",
      "side": "server",
      "properties": {
        "plan": "enum plan id",
        "interval": "month | year",
        "amount_cents": "integer",
        "currency": "ISO 4217"
      },
      "pii_check": "no raw card, no email, order_id as opaque ref"
    }
  ],
  "pageviews": {
    "method": "automatic via posthog-js capture_pageview (SPA default)",
    "custom_pageviews": [
      {"name": "onboarding_step_viewed", "trigger": "wizard step change", "properties": {"step": "integer"}}
    ]
  },
  "feature_flags": [
    {
      "name": "new-dashboard-layout",
      "description": "A/B test for redesigned dashboard",
      "location": "src/components/Dashboard.tsx",
      "fallback": false,
      "server_side_check": false
    }
  ],
  "existing_analytics": {
    "found": false,
    "tools": [],
    "existing_events": [],
    "migration_stance": "n/a",
    "notes": "No existing analytics detected"
  }
}
```

### Field semantics

| Field | Required | Meaning |
|---|---|---|
| `events[].name` | yes | snake_case, `verb_noun` or `noun_verbed` past tense |
| `events[].category` | yes | `auth`, `conversion`, `core`, `feature`, `error`, `share` — stays small |
| `events[].priority` | yes | `high` = instrument in this PR, `medium` = nice-to-have, `low` = defer |
| `events[].side` | yes | `client` or `server` — determines which SDK captures it |
| `events[].trigger` | yes | Business condition that fires it — not "on click of X button" |
| `events[].location` | yes | Exact file path where instrumentation belongs |
| `events[].properties` | yes | Map of property name → value description / enum. Every entry must pass the Step 8 filter. |
| `events[].pii_check` | yes | One-line justification that properties contain no PII |

## Event Naming Convention

| Rule | Good | Bad |
|---|---|---|
| snake_case, past-tense verb | `user_signed_up`, `invoice_sent` | `UserSignup`, `send-invoice` |
| Describes a business moment | `checkout_completed`, `quota_exceeded` | `button_clicked`, `div_rendered` |
| No UI-element names | `plan_upgraded` | `upgrade_button_clicked` |
| No domain prefix unless disambiguating | `invoice_created` (in an invoice app) | `myapp_invoice_created` |
| Stable over UI redesigns | `search_performed` survives a redesign | `search_bar_submitted` breaks when the bar moves |
| Pick one tense and stick to it | all past-tense: `created`, `deleted`, `viewed` | mixing `create`, `deleted`, `viewing` |

## Anti-Patterns (reject these)

| Anti-pattern | Why it's wrong | Fix |
|---|---|---|
| `track("button_clicked", { id: "btn-42" })` | Tells you nothing about the business. Unusable for funnels. | Name the *action*: `invite_sent`, `plan_upgraded`. |
| Event on every render / scroll / keystroke | Noise drowns signal; PostHog bill explodes; autocapture already does this | Track business moments only. 5–15 events is the norm. |
| Email, name, or message body in `properties` | PII leak, GDPR violation, possibly CCPA | Remove. Use hashed or enum surrogates. See Step 8 filter. |
| Tracking before consent | Illegal in EU/UK | `opt_out_capturing_by_default: true`, wait for opt-in. |
| `properties.data = JSON.stringify(entireObject)` | Every request shape change breaks the schema; PII sneaks in via nested fields | Pick the 2–4 fields you actually need. |
| Growing properties ad-hoc per event | Property-name sprawl (`user_id`, `userId`, `uid`) kills funnels | Pick one convention, document it, reuse names across events. |
| Duplicating an existing analytics tool | Double-billing, conflicting numbers | Step 2. Either migrate or stay out. |
| Client-side tracking of payment success | User can block it, under-reports revenue, also attackable | Server-side from webhook. `side: "server"`. |
| Feature flag without server check for paywalls | Client-only flag = bypassable from devtools | `server_side_check: true` for anything gating paid features. |
| Forgetting `posthog.reset()` on logout | Next user on shared device inherits the previous identity | Always include `reset_location`. |

## Rules

<rules>
<rule>Output MUST be valid JSON at ${DIRIGENT_RUN_DIR}/tracking-plan.json matching the schema in Step 10 exactly.</rule>
<rule>Event names MUST be snake_case, past-tense or verb_noun — no UI-element names, no domain prefix unless disambiguating (see Event Naming Convention table).</rule>
<rule>Every event MUST have name, category, priority, side, trigger, location, properties, pii_check — all required.</rule>
<rule>Every property MUST pass the Step 8 PII filter. If in doubt, remove it. Raw email / name / phone / free-text / auth material / special-category data is NEVER allowed in properties.</rule>
<rule>Every plan MUST include a consent block with an explicit stance (opt_in_required, opt_out_cmp, server_side_only, or no_consent_needed) and rationale.</rule>
<rule>Payment / revenue / quota events MUST be server-side (side: "server"). Client-side is bypassable and under-reports.</rule>
<rule>Feature flags gating paid features MUST have server_side_check: true. Client-only gates are bypassable.</rule>
<rule>If an analytics tool already exists, record it in existing_analytics and make the plan additive — never silently replace, never duplicate events.</rule>
<rule>Identification MUST include a reset_location for logout. distinct_id MUST be an opaque id, not email.</rule>
<rule>NEVER put actual API keys in the plan — only env var names.</rule>
<rule>Ship 5–15 high-signal events. If the candidate list exceeds 20, cut anything below priority "high".</rule>
<rule>Do NOT instrument code — the plan is the output. The executor writes the code.</rule>
</rules>

<constraints>
<constraint>Output: tracking-plan.json in ${DIRIGENT_RUN_DIR} — nothing else. No markdown, no commentary, no code changes.</constraint>
<constraint>Maximum 10 minutes. This is a planning step, not an implementation step.</constraint>
</constraints>
