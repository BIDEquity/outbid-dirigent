# Expo (React Native)

**Role:** Mobile app — iOS + Android from one codebase
**Tier:** 1 (default for mobile apps)
**When:** SPEC mentions mobile, app, iOS, Android, scanning, camera, NFC, or wallet

## Docs

Before using unfamiliar Expo APIs, query context7:
1. `mcp__context7__resolve-library-id` with `libraryName="expo"` → get libraryId
2. `mcp__context7__query-docs` with `libraryId=<result>` and `topic="<your question>"` → get current docs

## Check Installation

```bash
node --version   # >= 18
npm --version
npx expo --version
```

## Scaffold

```bash
npx create-expo-app@latest . --template blank-typescript
npm install
```

For apps with navigation (most apps):
```bash
npx create-expo-app@latest . --template tabs
npm install
```

The scaffold uses `expo-router` (file-based routing) by default.

## Run

```bash
npx expo start --port 8081
```

Port: **8081** (Metro bundler)

For web preview (no device needed):
```bash
npx expo start --web --port 8081
```

For device testing: scan the QR code with Expo Go app.

## Common Modules

Install as needed based on SPEC:

```bash
# Camera / barcode scanning
npx expo install expo-camera

# NFC
npx expo install react-native-nfc-manager

# File system
npx expo install expo-file-system

# Secure storage (tokens, keys)
npx expo install expo-secure-store

# Haptics
npx expo install expo-haptics

# Location
npx expo install expo-location
```

Always use `npx expo install` (not `npm install`) for native modules — it picks the SDK-compatible version.

## Test

```bash
npm install -D jest @testing-library/react-native
```

Add to `package.json`:
```json
{
  "scripts": {
    "test": "jest"
  },
  "jest": {
    "preset": "jest-expo"
  }
}
```

```typescript
// __tests__/App.test.tsx
import { render, screen } from '@testing-library/react-native'
import App from '../app/index'

test('renders without crashing', () => {
  render(<App />)
  expect(screen.toJSON()).toBeTruthy()
})
```

```bash
npm test
```

### E2E Testing (Maestro)

```bash
# Check maestro is installed
maestro --version
```

```yaml
# maestro/flow.yaml
appId: com.yourapp
---
- launchApp
- assertVisible: "Welcome"
- tapOn: "Get Started"
- assertVisible: "Home"
```

```bash
maestro test maestro/flow.yaml
```

## Build

```bash
# Local dev build (requires Xcode / Android Studio)
npx expo run:ios
npx expo run:android

# Cloud build (requires EAS account — use local builds for prototypes)
eas build --platform ios --local
```

## Start Script Pattern

```bash
#!/bin/bash
set -e
cd "$(dirname "$0")"
npm install
echo "Expo Dev Server: http://localhost:8081"
echo "Scan QR code with Expo Go, or press 'w' for web preview"
exec npx expo start --port 8081
```

## Pairing

- **+ PocketBase** → mobile app + lightweight backend with auth
- **+ Supabase Local** → mobile app + production backend (use @supabase/supabase-js)
- **+ FastAPI** → mobile app + custom Python backend
- **+ Anthropic SDK** → AI-powered mobile features (call API from app or via backend)
