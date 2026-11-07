#!/bin/bash
# Builds a signed, installable APK without Gradle or Android Studio.
# Needs (Ubuntu/Debian): sudo apt install openjdk-17-jdk-headless aapt apksigner zipalign dalvik-exchange android-sdk-platform-23 libandroid-23-java
set -e
cd "$(dirname "$0")"
AJ=/usr/lib/android-sdk/platforms/android-23/android.jar
python3 mkassets.py ../web/index.html          # web app -> assets/index.html (bundled fonts + native bridge)
rm -rf build gen; mkdir -p build/classes gen
aapt package -f -m -J gen -M AndroidManifest.xml -S res -A assets -I $AJ -F build/app.unsigned.apk --min-sdk-version 21 --target-sdk-version 33 --version-code 1 --version-name 1.0
javac -nowarn --release 8 -classpath $AJ -d build/classes gen/pk/aasmaan/weather/R.java src/pk/aasmaan/weather/MainActivity.java
dalvik-exchange --dex --output=build/classes.dex build/classes
cd build && aapt add app.unsigned.apk classes.dex >/dev/null
zipalign -f -p 4 app.unsigned.apk app.aligned.apk
# Debug-style key for side-loading. For Google Play use your own release key.
[ -f ../debug.jks ] || keytool -genkeypair -keystore ../debug.jks -alias aasmaan -keyalg RSA -keysize 2048 -validity 10000 -storepass android -keypass android -dname "CN=Aasmaan Debug"
apksigner sign --ks ../debug.jks --ks-pass pass:android --key-pass pass:android --ks-key-alias aasmaan --out aasmaan.apk app.aligned.apk
echo "Built: android/build/aasmaan.apk"
