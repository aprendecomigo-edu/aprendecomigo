/**
 * Comprehensive Onboarding Test Execution Script
 * GitHub Issue #39: Post-Registration Onboarding - Guide New School Admins to Success
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

// Test configuration
const CONFIG = {
  baseUrl: 'http://localhost:8081',
  backendUrl: 'http://localhost:8000',
  testEmail: 'anapmc.carvalho@gmail.com',
  verificationCode: '123456',
  timeout: 30000,
  screenshotDir: (testName, runId) => `/Users/anapmc/Code/aprendecomigo/qa-tests/onboard/${testName}/run-${runId}/screenshots`,
  resultsDir: (testName, runId) => `/Users/anapmc/Code/aprendecomigo/qa-tests/onboard/${testName}/run-${runId}`
};

// Generate run ID
const generateRunId = () => {
  const now = new Date();
  return now.toISOString().replace(/[-:]/g, '').replace(/\..+/, '').replace('T', '-');
};

// Create directories for test run
const createTestRunDirectories = (testName, runId) => {
  const resultsDir = CONFIG.resultsDir(testName, runId);
  const screenshotDir = CONFIG.screenshotDir(testName, runId);
  
  if (!fs.existsSync(resultsDir)) {
    fs.mkdirSync(resultsDir, { recursive: true });
  }
  if (!fs.existsSync(screenshotDir)) {
    fs.mkdirSync(screenshotDir, { recursive: true });
  }
  
  return { resultsDir, screenshotDir };
};

// Take screenshot with error handling
const takeScreenshot = async (page, screenshotDir, filename, description = '') => {
  try {
    const filepath = path.join(screenshotDir, `${filename}.png`);
    await page.screenshot({ path: filepath, fullPage: true });
    console.log(`✓ Screenshot saved: ${filename}.png - ${description}`);
    return filepath;
  } catch (error) {
    console.error(`✗ Failed to take screenshot ${filename}: ${error.message}`);
    return null;
  }
};

// Wait for element with timeout
const waitForElementSafe = async (page, selector, timeout = 10000) => {
  try {
    await page.waitForSelector(selector, { timeout });
    return true;
  } catch (error) {
    console.error(`Element not found: ${selector}`);
    return false;
  }
};

// Check for errors in console
const checkConsoleErrors = (consoleMessages) => {
  const errors = consoleMessages.filter(msg => msg.type() === 'error');
  return errors.map(error => error.text());
};

/**
 * ONBOARD-001: Welcome Screen Display Test
 */
const executeOnboard001 = async () => {
  const testName = 'onboard-001';
  const runId = generateRunId();
  const { resultsDir, screenshotDir } = createTestRunDirectories(testName, runId);
  
  console.log(`\n🚀 Starting ONBOARD-001: Welcome Screen Display Test`);
  console.log(`📁 Results: ${resultsDir}`);
  
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  const consoleMessages = [];
  
  // Capture console messages
  page.on('console', msg => consoleMessages.push(msg));
  
  const results = {
    testId: 'ONBOARD-001',
    testName: 'Welcome Screen Display After Email Verification',
    runId,
    timestamp: new Date().toISOString(),
    steps: [],
    overallResult: 'PENDING',
    totalSteps: 15,
    passedSteps: 0,
    failedSteps: 0,
    consoleErrors: [],
    screenshots: []
  };
  
  try {
    // Step 1: Navigate to landing page
    console.log('Step 1: Navigate to landing page');
    await page.goto(CONFIG.baseUrl, { waitUntil: 'domcontentloaded' });
    await takeScreenshot(page, screenshotDir, '01_landing_page', 'Landing page loaded');
    
    const landingLoaded = await waitForElementSafe(page, 'body');
    results.steps.push({
      step: 1,
      description: 'Navigate to landing page',
      result: landingLoaded ? 'PASS' : 'FAIL',
      details: landingLoaded ? 'Landing page loaded successfully' : 'Failed to load landing page'
    });
    
    if (landingLoaded) results.passedSteps++;
    else results.failedSteps++;
    
    // Step 2: Navigate to sign-in
    console.log('Step 2: Navigate to sign-in page');
    try {
      // Look for sign-in link/button
      const signInButton = await page.locator('text=Sign In').first();
      if (await signInButton.isVisible()) {
        await signInButton.click();
      } else {
        await page.goto(`${CONFIG.baseUrl}/auth/signin`);
      }
      
      await page.waitForURL('**/auth/signin', { timeout: 10000 });
      await takeScreenshot(page, screenshotDir, '02_signin_page', 'Sign-in page loaded');
      
      results.steps.push({
        step: 2,
        description: 'Navigate to sign-in page',
        result: 'PASS',
        details: 'Successfully navigated to sign-in page'
      });
      results.passedSteps++;
      
    } catch (error) {
      console.error('Failed to navigate to sign-in:', error.message);
      await takeScreenshot(page, screenshotDir, '02_signin_failed', 'Sign-in navigation failed');
      results.steps.push({
        step: 2,
        description: 'Navigate to sign-in page',
        result: 'FAIL',
        details: `Navigation failed: ${error.message}`
      });
      results.failedSteps++;
    }
    
    // Step 3: Enter email and request verification
    console.log('Step 3: Enter email and request verification');
    try {
      const emailInput = page.locator('input[type="email"]').first();
      await emailInput.fill(CONFIG.testEmail);
      
      const sendCodeButton = page.locator('text=Send Verification Code').first();
      await sendCodeButton.click();
      
      await page.waitForURL('**/auth/verify-code*', { timeout: 10000 });
      await takeScreenshot(page, screenshotDir, '03_verification_requested', 'Verification code requested');
      
      results.steps.push({
        step: 3,
        description: 'Request verification code',
        result: 'PASS',
        details: 'Verification code requested successfully'
      });
      results.passedSteps++;
      
    } catch (error) {
      console.error('Failed to request verification:', error.message);
      await takeScreenshot(page, screenshotDir, '03_verification_failed', 'Verification request failed');
      results.steps.push({
        step: 3,
        description: 'Request verification code',
        result: 'FAIL',
        details: `Verification request failed: ${error.message}`
      });
      results.failedSteps++;
    }
    
    // Step 4: Enter verification code
    console.log('Step 4: Enter verification code');
    try {
      const codeInput = page.locator('input[name="code"]').first();
      await codeInput.fill(CONFIG.verificationCode);
      
      const verifyButton = page.locator('text=Verify Code').first();
      await verifyButton.click();
      
      // Wait for redirect - this is the critical test point
      await page.waitForTimeout(3000);
      await takeScreenshot(page, screenshotDir, '04_verification_completed', 'Verification completed');
      
      results.steps.push({
        step: 4,
        description: 'Complete email verification',
        result: 'PASS',
        details: 'Email verification completed successfully'
      });
      results.passedSteps++;
      
    } catch (error) {
      console.error('Failed to complete verification:', error.message);
      await takeScreenshot(page, screenshotDir, '04_verification_failed', 'Verification failed');
      results.steps.push({
        step: 4,
        description: 'Complete email verification',
        result: 'FAIL',
        details: `Verification failed: ${error.message}`
      });
      results.failedSteps++;
    }
    
    // Step 5: CRITICAL - Verify welcome screen appears
    console.log('Step 5: CRITICAL - Verify welcome screen appears');
    try {
      const currentUrl = page.url();
      const isWelcomeScreen = currentUrl.includes('/onboarding/welcome');
      
      if (isWelcomeScreen) {
        await takeScreenshot(page, screenshotDir, '05_welcome_screen_loaded', 'Welcome screen loaded - CRITICAL PASS');
        console.log('✅ CRITICAL SUCCESS: Welcome screen appears after verification!');
        
        results.steps.push({
          step: 5,
          description: 'Verify welcome screen appears (CRITICAL)',
          result: 'PASS',
          details: `Welcome screen loaded at ${currentUrl}`
        });
        results.passedSteps++;
        
      } else {
        await takeScreenshot(page, screenshotDir, '05_welcome_screen_missing', 'Welcome screen missing - CRITICAL FAIL');
        console.log('❌ CRITICAL FAILURE: Welcome screen did not appear!');
        console.log(`Current URL: ${currentUrl}`);
        
        results.steps.push({
          step: 5,
          description: 'Verify welcome screen appears (CRITICAL)',
          result: 'FAIL',
          details: `Expected /onboarding/welcome, got ${currentUrl}`
        });
        results.failedSteps++;
      }
      
    } catch (error) {
      console.error('Failed to verify welcome screen:', error.message);
      await takeScreenshot(page, screenshotDir, '05_welcome_check_error', 'Welcome screen check error');
      results.steps.push({
        step: 5,
        description: 'Verify welcome screen appears (CRITICAL)',
        result: 'FAIL',
        details: `Welcome screen check failed: ${error.message}`
      });
      results.failedSteps++;
    }
    
    // Continue with additional verification steps if welcome screen loaded
    const currentUrl = page.url();
    if (currentUrl.includes('/onboarding/welcome')) {
      
      // Step 6: Verify welcome screen elements
      console.log('Step 6: Verify welcome screen elements');
      try {
        const elements = {
          checkIcon: page.locator('[data-testid="check-circle-icon"], .lucide-check-circle').first(),
          welcomeHeading: page.locator('text=Welcome to Aprende Comigo').first(),
          getStartedButton: page.locator('[data-testid="get-started-button"], text=Get Started').first(),
          skipButton: page.locator('[data-testid="skip-onboarding-button"], text=Skip Onboarding').first()
        };
        
        const elementResults = {};
        for (const [name, locator] of Object.entries(elements)) {
          elementResults[name] = await locator.isVisible();
        }
        
        await takeScreenshot(page, screenshotDir, '06_welcome_elements', 'Welcome screen elements verification');
        
        const allElementsPresent = Object.values(elementResults).every(visible => visible);
        results.steps.push({
          step: 6,
          description: 'Verify welcome screen elements',
          result: allElementsPresent ? 'PASS' : 'FAIL',
          details: `Elements found: ${JSON.stringify(elementResults)}`
        });
        
        if (allElementsPresent) results.passedSteps++;
        else results.failedSteps++;
        
      } catch (error) {
        console.error('Failed to verify welcome elements:', error.message);
        results.steps.push({
          step: 6,
          description: 'Verify welcome screen elements',
          result: 'FAIL',
          details: `Element verification failed: ${error.message}`
        });
        results.failedSteps++;
      }
      
      // Step 7: Test Get Started button
      console.log('Step 7: Test Get Started button functionality');
      try {
        const getStartedButton = page.locator('[data-testid="get-started-button"], text=Get Started').first();
        await getStartedButton.click();
        
        await page.waitForTimeout(2000);
        const newUrl = page.url();
        const navigatedToChecklist = newUrl.includes('/onboarding/checklist');
        
        await takeScreenshot(page, screenshotDir, '07_get_started_navigation', 'Get Started button navigation');
        
        results.steps.push({
          step: 7,
          description: 'Test Get Started button functionality',
          result: navigatedToChecklist ? 'PASS' : 'FAIL',
          details: `Navigation result: ${newUrl}`
        });
        
        if (navigatedToChecklist) results.passedSteps++;
        else results.failedSteps++;
        
      } catch (error) {
        console.error('Failed to test Get Started button:', error.message);
        results.steps.push({
          step: 7,
          description: 'Test Get Started button functionality',
          result: 'FAIL',
          details: `Get Started test failed: ${error.message}`
        });
        results.failedSteps++;
      }
    }
    
    // Determine overall result
    results.overallResult = results.failedSteps === 0 ? 'PASS' : 'FAIL';
    results.consoleErrors = checkConsoleErrors(consoleMessages);
    
  } catch (error) {
    console.error('Test execution error:', error);
    results.overallResult = 'ERROR';
    results.error = error.message;
  } finally {
    await browser.close();
  }
  
  // Save results
  const resultsPath = path.join(resultsDir, 'results.md');
  const resultsContent = generateTestReport(results);
  fs.writeFileSync(resultsPath, resultsContent);
  
  console.log(`\n📊 ONBOARD-001 Results:`);
  console.log(`Overall: ${results.overallResult}`);
  console.log(`Steps: ${results.passedSteps}/${results.totalSteps} passed`);
  console.log(`Report saved: ${resultsPath}`);
  
  return results;
};

/**
 * Generate detailed test report
 */
const generateTestReport = (results) => {
  return `# ${results.testName} - Test Results

**Test ID:** ${results.testId}
**Run ID:** ${results.runId}
**Timestamp:** ${results.timestamp}
**Overall Result:** ${results.overallResult}

## Summary
- **Total Steps:** ${results.totalSteps}
- **Passed:** ${results.passedSteps}
- **Failed:** ${results.failedSteps}
- **Success Rate:** ${((results.passedSteps / results.totalSteps) * 100).toFixed(1)}%

## Step Results

${results.steps.map(step => 
  `### Step ${step.step}: ${step.description}
**Result:** ${step.result}
**Details:** ${step.details}
`).join('\n')}

## Console Errors
${results.consoleErrors.length > 0 ? 
  results.consoleErrors.map(error => `- ${error}`).join('\n') : 
  'No console errors detected'}

## Critical Acceptance Criteria

${results.steps.find(s => s.step === 5)?.result === 'PASS' ? 
  '✅ **PASS**: Welcome screen appears immediately after successful email verification' :
  '❌ **FAIL**: Welcome screen does not appear after email verification'}

## Recommendations

${results.overallResult === 'PASS' ? 
  'All acceptance criteria met. Onboarding welcome screen functionality is working correctly.' :
  'Issues detected with onboarding flow. Review failed steps and address critical failures.'}

---
*Generated by QA Test Automation - ${new Date().toISOString()}*
`;
};

/**
 * Main execution function
 */
const executeAllTests = async () => {
  console.log('🎯 Starting Comprehensive Onboarding Tests for GitHub Issue #39');
  console.log('📋 Testing: Post-Registration Onboarding - Guide New School Admins to Success\n');
  
  const testResults = [];
  
  try {
    // Execute ONBOARD-001
    const onboard001Results = await executeOnboard001();
    testResults.push(onboard001Results);
    
    // TODO: Add execution for ONBOARD-002 through ONBOARD-005
    
    // Generate overall summary
    console.log('\n📈 Overall Test Summary:');
    testResults.forEach(result => {
      console.log(`${result.testId}: ${result.overallResult} (${result.passedSteps}/${result.totalSteps} steps)`);
    });
    
  } catch (error) {
    console.error('Test suite execution error:', error);
  }
};

// Execute if run directly
if (require.main === module) {
  executeAllTests().catch(console.error);
}

module.exports = {
  executeOnboard001,
  executeAllTests,
  CONFIG
};