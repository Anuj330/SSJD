# SSJD Portal — Mobile App (Capacitor)

The member/admin portal (this React app) is packaged as a native Android/iOS app
with **Capacitor** — it reuses 100% of the web code. The app **opens on the login
screen** (the root route is protected, so an unauthenticated launch redirects to
`/login`), then shows the dashboard after login.

> The app bundles the **portal** only — not the public marketing website. There is
> no "home page" in the app; login is the entry point.

## Prerequisites
- **Android Studio** (bundles the Android SDK) — required to compile the APK.
- The **backend deployed at a public HTTPS URL** — a mobile app can't use
  `localhost` or the dev proxy, so it needs an absolute API URL.

## 1. Point the app at your deployed backend
The app reads `VITE_API_BASE_URL` at build time. Create `.env.production`:
```
VITE_API_BASE_URL=https://api.your-domain.com
```
(Use your deployed FastAPI backend's public URL — **https** strongly preferred;
the Android scheme is https, so an http backend would be blocked as mixed content.)

## 2. Allow the app origin on the backend (CORS)
Add the Capacitor origins to the backend's allowed CORS origins:
- Android: `https://localhost`
- iOS:     `capacitor://localhost`

## 3. Build & run
```bash
# build web + sync into the native project
npm run mobile:build

# open in Android Studio (Run ▶ to a device/emulator, or Build > Build APK)
npm run mobile:open

# …or build a debug APK from the CLI (needs ANDROID_HOME / Android SDK):
npm run mobile:apk
# output: android/app/build/outputs/apk/debug/app-debug.apk
```

## iOS (optional, needs a Mac + Xcode)
```bash
npm install @capacitor/ios
npx cap add ios
npx cap open ios
```

## Notes
- **App identity:** `appId` `com.ssjd.portal`, `appName` `SSJD` (in `capacitor.config.json`).
- **Login-on-launch:** a stored session is remembered (goes straight to dashboard).
  To force the login screen on every launch, clear the persisted auth on app start
  (Capacitor `App` `resume`/`appStateChange` listener) — ask and we'll wire it.
- After changing web code, re-run `npm run mobile:build` to push it into the app.
