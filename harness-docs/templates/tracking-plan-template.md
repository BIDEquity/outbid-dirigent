# Tracking Plan: [Feature/Product Name]

**Owner:** [name]
**Last Updated:** YYYY-MM-DD

## Overview

[What user interactions does this tracking plan cover? What decisions
will this data inform?]

## Events

| Event Name | Trigger | Properties | Owner | Status |
|------------|---------|------------|-------|--------|
| `feature_viewed` | User opens feature page | `user_id`, `source`, `variant` | [name] | Implemented |
| `action_completed` | User completes action | `user_id`, `duration_ms`, `result` | [name] | Proposed |

## Event Schema Details

### `feature_viewed`

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `user_id` | string | yes | Unique user identifier |
| `source` | string | yes | Where the user came from |
| `variant` | string | no | A/B test variant if applicable |

## Validation

- [ ] Event schemas are validated in CI
- [ ] Breaking changes to schemas trigger a review
- [ ] All events fire correctly in staging before production deploy

## Dashboards

| Dashboard | Audience | URL |
|-----------|----------|-----|
| [Name] | Product team | [link] |
