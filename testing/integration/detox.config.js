/** @type {Detox.DetoxConfig} */
module.exports = {
  testRunner: {
    args: {
      $0: "jest",
      config: "testing/integration/jest.config.js",
    },
    jest: {
      setupTimeout: 120000,
    },
  },
  apps: {
    "ios.debug": {
      type: "ios.app",
      binaryPath:
        "frontend-ui/ios/build/Build/Products/Debug-iphonesimulator/AprendeConmigo.app",
      build:
        "cd frontend-ui && xcodebuild -workspace ios/AprendeConmigo.xcworkspace -scheme AprendeConmigo -configuration Debug -sdk iphonesimulator -derivedDataPath ios/build",
    },
    "ios.release": {
      type: "ios.app",
      binaryPath:
        "frontend-ui/ios/build/Build/Products/Release-iphonesimulator/AprendeConmigo.app",
      build:
        "cd frontend-ui && xcodebuild -workspace ios/AprendeConmigo.xcworkspace -scheme AprendeConmigo -configuration Release -sdk iphonesimulator -derivedDataPath ios/build",
    },
    "android.debug": {
      type: "android.apk",
      binaryPath:
        "frontend-ui/android/app/build/outputs/apk/debug/app-debug.apk",
      build:
        "cd frontend-ui && ./gradlew assembleDebug assembleAndroidTest -DtestBuildType=debug",
    },
    "android.release": {
      type: "android.apk",
      binaryPath:
        "frontend-ui/android/app/build/outputs/apk/release/app-release.apk",
      build:
        "cd frontend-ui && ./gradlew assembleRelease assembleAndroidTest -DtestBuildType=release",
    },
  },
  devices: {
    simulator: {
      type: "ios.simulator",
      device: {
        type: "iPhone 15",
      },
    },
    emulator: {
      type: "android.emulator",
      device: {
        avdName: "Pixel_4_API_30",
      },
    },
  },
  configurations: {
    "ios.sim.debug": {
      device: "simulator",
      app: "ios.debug",
    },
    "ios.sim.release": {
      device: "simulator",
      app: "ios.release",
    },
    "android.emu.debug": {
      device: "emulator",
      app: "android.debug",
    },
    "android.emu.release": {
      device: "emulator",
      app: "android.release",
    },
  },
};
