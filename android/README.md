# Android wrapper

This module packages the existing web console inside a WebView so you can ship
it as a native Android application. The assets folder bundles the same
`frontend/index.html` that powers the static site, allowing the app to run
offline and connect to any reachable FastAPI backend URL.

## Requirements

* Android Studio Iguana or later, or Gradle 8.7+ with the Android Gradle Plugin
  8.5.
* Android SDK Platform 34 and a build-tools installation that matches (build
  tools 34.0.0 works well).

## Building a debug APK

1. Install the Android SDK and set `ANDROID_HOME`/`ANDROID_SDK_ROOT`, or open the
   `android` folder in Android Studio which will guide you through the
   installation.
2. If you are using the command line, create a `local.properties` file at the
   root of the `android/` directory that points at your SDK, for example:

   ```properties
   sdk.dir=/home/you/Android/Sdk
   ```

3. Generate the Gradle wrapper files if they are not already present:

   ```bash
   gradle wrapper --gradle-version 8.7
   ```

   Android Studio automatically offers to do this the first time you open the
   project. The included `gradlew` helper will fall back to a system Gradle
   installation if the wrapper JAR is absent.

4. From the `android/` directory run:

   ```bash
   ./gradlew assembleDebug
   ```

   Android Studio also exposes this through **Build → Build Bundle(s) / APK(s) →
   Build APK(s)**.

The resulting APK appears under `android/app/build/outputs/apk/debug/`. Install
it with `adb install app-debug.apk` or send it to your testers of choice.

## Syncing frontend updates

The Gradle build copies `frontend/index.html` into the app's assets before every
build. Update the web client as usual and re-run `./gradlew assembleDebug` (or
any other variant); the latest HTML will be bundled automatically. If the file
is missing, Gradle aborts with a clear error so you can restore or regenerate
the frontend before retrying.
