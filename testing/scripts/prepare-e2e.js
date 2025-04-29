#!/usr/bin/env node

/**
 * Prepare E2E Test Environment
 *
 * This script prepares the environment for running E2E tests:
 * 1. Ensures all necessary dependencies are installed
 * 2. Copies the test files to the frontend-ui directory
 * 3. Sets up the test data and configuration
 */

const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

console.log("Preparing E2E test environment...");

// Define paths
const REPO_ROOT = path.resolve(__dirname, "../..");
const TESTING_DIR = path.join(REPO_ROOT, "testing");
const FRONTEND_DIR = path.join(REPO_ROOT, "frontend-ui");
const INTEGRATION_DIR = path.join(TESTING_DIR, "integration");

// Check that all directories exist
if (!fs.existsSync(FRONTEND_DIR)) {
  console.error("Error: frontend-ui directory not found");
  process.exit(1);
}

if (!fs.existsSync(path.join(INTEGRATION_DIR, "e2e"))) {
  console.error("Error: integration/e2e directory not found");
  process.exit(1);
}

// Install dependencies
console.log("Installing dependencies...");
try {
  execSync("npm install", { cwd: TESTING_DIR, stdio: "inherit" });
  execSync(
    "cd ../frontend-ui && npm install --save-dev detox jest-circus axios-mock-adapter",
    { cwd: TESTING_DIR, stdio: "inherit" },
  );
} catch (error) {
  console.error("Error installing dependencies:", error.message);
  process.exit(1);
}

// Ensure Detox is properly set up
console.log("Setting up Detox configuration...");
try {
  // Check if .detoxrc.js exists in frontend-ui
  if (!fs.existsSync(path.join(FRONTEND_DIR, ".detoxrc.js"))) {
    console.log("Creating Detox configuration...");

    // Create detox config by executing the detox init command
    execSync("npx detox init -r jest", {
      cwd: FRONTEND_DIR,
      stdio: "inherit",
    });

    // Now update the config for Expo
    console.log("Updating Detox config for Expo...");
    const detoxConfig = `
/** @type {Detox.DetoxConfig} */
module.exports = {
  testRunner: {
    args: {
      '$0': 'jest',
      config: 'e2e/jest.config.js'
    },
    jest: {
      setupTimeout: 120000
    }
  },
  apps: {
    'ios.debug': {
      type: 'ios.app',
      build: 'npx expo prebuild --platform ios && xcodebuild -workspace ios/AprendeConmigo.xcworkspace -scheme AprendeConmigo -configuration Debug -sdk iphonesimulator -derivedDataPath ios/build',
      binaryPath: 'ios/build/Build/Products/Debug-iphonesimulator/AprendeConmigo.app'
    },
    'ios.release': {
      type: 'ios.app',
      build: 'npx expo prebuild --platform ios && xcodebuild -workspace ios/AprendeConmigo.xcworkspace -scheme AprendeConmigo -configuration Release -sdk iphonesimulator -derivedDataPath ios/build',
      binaryPath: 'ios/build/Build/Products/Release-iphonesimulator/AprendeConmigo.app'
    },
    'android.debug': {
      type: 'android.apk',
      build: 'npx expo prebuild --platform android && cd android && ./gradlew assembleDebug assembleAndroidTest -DtestBuildType=debug',
      binaryPath: 'android/app/build/outputs/apk/debug/app-debug.apk'
    },
    'android.release': {
      type: 'android.apk',
      build: 'npx expo prebuild --platform android && cd android && ./gradlew assembleRelease assembleAndroidTest -DtestBuildType=release',
      binaryPath: 'android/app/build/outputs/apk/release/app-release.apk'
    }
  },
  devices: {
    simulator: {
      type: 'ios.simulator',
      device: {
        type: 'iPhone 14'
      }
    },
    attached: {
      type: 'android.attached',
      device: {
        adbName: '.*'
      }
    },
    emulator: {
      type: 'android.emulator',
      device: {
        avdName: 'Pixel_3a_API_30'
      }
    }
  },
  configurations: {
    'ios.sim.debug': {
      device: 'simulator',
      app: 'ios.debug'
    },
    'ios.sim.release': {
      device: 'simulator',
      app: 'ios.release'
    },
    'android.att.debug': {
      device: 'attached',
      app: 'android.debug'
    },
    'android.att.release': {
      device: 'attached',
      app: 'android.release'
    },
    'android.emu.debug': {
      device: 'emulator',
      app: 'android.debug'
    },
    'android.emu.release': {
      device: 'emulator',
      app: 'android.release'
    }
  }
};
    `;

    fs.writeFileSync(path.join(FRONTEND_DIR, ".detoxrc.js"), detoxConfig);
  }

  // Ensure e2e directory exists
  if (!fs.existsSync(path.join(FRONTEND_DIR, "e2e"))) {
    fs.mkdirSync(path.join(FRONTEND_DIR, "e2e"));
  }

  // Create Jest config
  const jestConfig = `
/** @type {import('@jest/types').Config.InitialOptions} */
module.exports = {
  rootDir: '..',
  testMatch: ['<rootDir>/e2e/**/*.e2e.js'],
  testTimeout: 120000,
  maxWorkers: 1,
  globalSetup: 'detox/runners/jest/globalSetup',
  globalTeardown: 'detox/runners/jest/globalTeardown',
  reporters: ['detox/runners/jest/reporter'],
  testEnvironment: 'detox/runners/jest/testEnvironment',
  verbose: true,
};
  `;

  fs.writeFileSync(
    path.join(FRONTEND_DIR, "e2e", "jest.config.js"),
    jestConfig,
  );

  // Create basic test
  const basicTest = `
describe('Test Detox Setup', () => {
  beforeAll(async () => {
    await device.launchApp();
  });

  beforeEach(async () => {
    await device.reloadReactNative();
  });

  it('should verify Detox is working', async () => {
    // This is just a simple test to verify Detox is working
    // We expect the app to launch successfully
    // In a real test, we would have more specific checks
    await expect(element(by.id('app-root'))).toExist();
  });
});
  `;

  fs.writeFileSync(path.join(FRONTEND_DIR, "e2e", "basic.e2e.js"), basicTest);
} catch (error) {
  console.error("Error setting up Detox:", error.message);
  process.exit(1);
}

// Add testID to root component
console.log("Ensuring testID on root component...");
try {
  const providerPath = path.join(
    FRONTEND_DIR,
    "components/ui/gluestack-ui-provider/index.tsx",
  );
  const providerWebPath = path.join(
    FRONTEND_DIR,
    "components/ui/gluestack-ui-provider/index.web.tsx",
  );

  if (fs.existsSync(providerPath)) {
    let content = fs.readFileSync(providerPath, "utf8");

    // Only add testID if it doesn't already exist
    if (!content.includes('testID="app-root"')) {
      content = content.replace(
        /<View\s+style=/g,
        '<View\n      testID="app-root"\n      style=',
      );
      fs.writeFileSync(providerPath, content);
    }
  }

  if (fs.existsSync(providerWebPath)) {
    let content = fs.readFileSync(providerWebPath, "utf8");

    // Only add testID if it doesn't already exist
    if (!content.includes('testID="app-root"')) {
      content = content.replace(
        /<View\s+style=/g,
        '<View\n      testID="app-root"\n      style=',
      );
      fs.writeFileSync(providerWebPath, content);
    }
  }
} catch (error) {
  console.error("Error updating root component:", error.message);
  // Non-fatal error, continue
}

// Update package.json scripts
console.log("Updating package.json scripts...");
try {
  const pkgPath = path.join(FRONTEND_DIR, "package.json");
  const pkg = JSON.parse(fs.readFileSync(pkgPath, "utf8"));

  // Add Detox scripts if they don't exist
  if (!pkg.scripts["e2e:build"]) {
    pkg.scripts["e2e:build"] = "detox build";
    pkg.scripts["e2e:test"] = "detox test";
    pkg.scripts["e2e:build:ios"] = "detox build -c ios.sim.debug";
    pkg.scripts["e2e:test:ios"] = "detox test -c ios.sim.debug";
    pkg.scripts["e2e:build:android"] = "detox build -c android.emu.debug";
    pkg.scripts["e2e:test:android"] = "detox test -c android.emu.debug";

    fs.writeFileSync(pkgPath, JSON.stringify(pkg, null, 2));
  }
} catch (error) {
  console.error("Error updating package.json:", error.message);
  // Non-fatal error, continue
}

console.log("E2E test environment prepared successfully!");
console.log("");
console.log("Next steps:");
console.log(
  "1. To run basic test:          cd frontend-ui && npx detox test -c ios.sim.debug e2e/basic.e2e.js",
);
console.log(
  "2. To run all auth tests:      cd testing && npm run test:auth:ios",
);
console.log("");
console.log(
  "Note: Running the tests requires a simulator/emulator configured in your environment.",
);
console.log(
  "You may need to adjust the device configurations in .detoxrc.js to match your available devices.",
);
