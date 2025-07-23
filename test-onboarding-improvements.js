const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

// Test configuration
const BASE_URL = 'http://localhost:8081';
const API_URL = 'http://127.0.0.1:8000';
const SCREENSHOTS_DIR = './test-screenshots';
const TEST_USER = {
  name: 'Maria Santos',
  email: `test-${Date.now()}@example.com`,
  phone: '+351 912 345 678'
};

// Create screenshots directory
if (!fs.existsSync(SCREENSHOTS_DIR)) {
  fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
}

async function runTests() {
  console.log('🚀 Starting comprehensive onboarding improvement tests...\n');
  
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 }
  });
  const page = await context.newPage();
  
  const results = {
    passed: 0,
    failed: 0,
    tests: []
  };

  // Test 1: Landing Page Loads Correctly
  await test('Landing Page Loads and Displays User Type Selection', async () => {
    await page.goto(BASE_URL);
    
    // Wait for redirect to landing page
    await page.waitForURL('**/landing');
    
    // Check page title and main elements
    await expect(page.locator('text=Aprende Comigo')).toBeVisible();
    await expect(page.locator('text=Individual Tutor')).toBeVisible();
    await expect(page.locator('text=School or Institution')).toBeVisible();
    
    // Check CTA buttons
    await expect(page.locator('text=Start Your Tutoring Practice')).toBeVisible();
    await expect(page.locator('text=Register Your Institution')).toBeVisible();
    
    await page.screenshot({ path: `${SCREENSHOTS_DIR}/01-landing-page.png` });
    console.log('✅ Landing page displays correctly with both user type options');
  });

  // Test 2: Tutor Signup Flow
  await test('Individual Tutor Signup Flow', async () => {
    // Click on tutor signup button
    await page.locator('text=Start Your Tutoring Practice').click();
    
    // Should navigate to signup with tutor type
    await page.waitForURL('**/auth/signup?type=tutor');
    
    // Check tutor-specific messaging
    await expect(page.locator('text=Set Up Your Tutoring Practice')).toBeVisible();
    await expect(page.locator('text=Individual Tutor')).toBeVisible();
    
    await page.screenshot({ path: `${SCREENSHOTS_DIR}/02-tutor-signup-page.png` });
    
    // Fill out personal information
    await page.fill('input[placeholder="Enter your full name"]', TEST_USER.name);
    await page.fill('input[placeholder="Enter your email address"]', TEST_USER.email);
    await page.fill('input[placeholder="Enter your phone number"]', TEST_USER.phone);
    
    // Verify auto-generated school name
    const schoolNameField = page.locator('input[placeholder*="auto-generated"]');
    await expect(schoolNameField).toHaveValue(`${TEST_USER.name}'s Tutoring Practice`);
    
    await page.screenshot({ path: `${SCREENSHOTS_DIR}/03-tutor-form-filled.png` });
    console.log('✅ Tutor signup form displays correctly with auto-generated school name');
    
    // Note: Not submitting to avoid creating test data
  });

  // Test 3: School Signup Flow
  await test('School/Institution Signup Flow', async () => {
    await page.goto(`${BASE_URL}/landing`);
    
    // Click on school signup button
    await page.locator('text=Register Your Institution').click();
    
    // Should navigate to signup with school type
    await page.waitForURL('**/auth/signup?type=school');
    
    // Check school-specific messaging
    await expect(page.locator('text=Register Your School')).toBeVisible();
    await expect(page.locator('text=School/Institution')).toBeVisible();
    
    await page.screenshot({ path: `${SCREENSHOTS_DIR}/04-school-signup-page.png` });
    
    // Fill out personal information
    await page.fill('input[placeholder="Enter your full name"]', 'Admin User');
    await page.fill('input[placeholder="Enter your email address"]', 'admin@school.com');
    await page.fill('input[placeholder="Enter your phone number"]', '+351 987 654 321');
    
    // School name should be editable and required
    const schoolNameInput = page.locator('input[placeholder="Enter your school name"]');
    await expect(schoolNameInput).toBeEditable();
    await schoolNameInput.fill('Example Language School');
    
    // Additional school fields should be visible
    await expect(page.locator('input[placeholder="Enter your school address"]')).toBeVisible();
    await expect(page.locator('input[placeholder="https://example.com"]')).toBeVisible();
    
    await page.screenshot({ path: `${SCREENSHOTS_DIR}/05-school-form-filled.png` });
    console.log('✅ School signup form displays correctly with editable school fields');
  });

  // Test 4: Navigation and Responsive Design
  await test('Navigation and Responsive Design', async () => {
    await page.goto(`${BASE_URL}/landing`);
    
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.screenshot({ path: `${SCREENSHOTS_DIR}/06-mobile-landing.png` });
    
    // Ensure elements are still accessible
    await expect(page.locator('text=Individual Tutor')).toBeVisible();
    await expect(page.locator('text=School or Institution')).toBeVisible();
    
    // Test tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.screenshot({ path: `${SCREENSHOTS_DIR}/07-tablet-landing.png` });
    
    // Reset to desktop
    await page.setViewportSize({ width: 1280, height: 720 });
    
    console.log('✅ Responsive design works correctly across different screen sizes');
  });

  // Test 5: Real-time School Name Generation
  await test('Real-time School Name Generation for Tutors', async () => {
    await page.goto(`${BASE_URL}/auth/signup?type=tutor`);
    
    const nameInput = page.locator('input[placeholder="Enter your full name"]');
    const schoolNameInput = page.locator('input[placeholder*="auto-generated"]');
    
    // Test real-time updates
    await nameInput.fill('João Silva');
    await expect(schoolNameInput).toHaveValue("João Silva's Tutoring Practice");
    
    await nameInput.fill('Ana Costa');
    await expect(schoolNameInput).toHaveValue("Ana Costa's Tutoring Practice");
    
    // Verify field is read-only for tutors
    await expect(schoolNameInput).not.toBeEditable();
    
    await page.screenshot({ path: `${SCREENSHOTS_DIR}/08-realtime-name-generation.png` });
    console.log('✅ Real-time school name generation works correctly');
  });

  // Test 6: Sign In Navigation
  await test('Sign In Navigation from Landing Page', async () => {
    await page.goto(`${BASE_URL}/landing`);
    
    // Test sign in button
    await page.locator('text=Sign In').click();
    await page.waitForURL('**/auth/signin');
    
    // Verify we're on signin page
    await expect(page.locator('text=Welcome back')).toBeVisible();
    
    await page.screenshot({ path: `${SCREENSHOTS_DIR}/09-signin-navigation.png` });
    console.log('✅ Sign in navigation works correctly');
  });

  // Helper function for tests
  async function test(name, testFn) {
    try {
      console.log(`🧪 Running: ${name}`);
      await testFn();
      results.passed++;
      results.tests.push({ name, status: 'PASSED' });
    } catch (error) {
      console.error(`❌ Failed: ${name}`);
      console.error(error.message);
      results.failed++;
      results.tests.push({ name, status: 'FAILED', error: error.message });
      
      // Take screenshot on failure
      await page.screenshot({ 
        path: `${SCREENSHOTS_DIR}/FAILED-${name.replace(/\s+/g, '-').toLowerCase()}.png` 
      });
    }
  }

  // Helper function to simulate expect
  async function expect(locator) {
    return {
      toBeVisible: async () => {
        await locator.waitFor({ state: 'visible', timeout: 5000 });
      },
      toHaveValue: async (value) => {
        const actualValue = await locator.inputValue();
        if (actualValue !== value) {
          throw new Error(`Expected "${value}" but got "${actualValue}"`);
        }
      },
      toBeEditable: async () => {
        const isEditable = await locator.isEditable();
        if (!isEditable) {
          throw new Error('Element is not editable');
        }
      }
    };
  }

  await browser.close();
  
  // Generate test report
  const report = {
    timestamp: new Date().toISOString(),
    summary: {
      total: results.passed + results.failed,
      passed: results.passed,
      failed: results.failed,
      success_rate: `${Math.round((results.passed / (results.passed + results.failed)) * 100)}%`
    },
    tests: results.tests,
    screenshots: fs.readdirSync(SCREENSHOTS_DIR).map(file => path.join(SCREENSHOTS_DIR, file))
  };
  
  // Save report
  fs.writeFileSync('./test-report.json', JSON.stringify(report, null, 2));
  
  console.log('\n📊 Test Results Summary:');
  console.log(`Total Tests: ${report.summary.total}`);
  console.log(`Passed: ${report.summary.passed}`);
  console.log(`Failed: ${report.summary.failed}`);
  console.log(`Success Rate: ${report.summary.success_rate}`);
  console.log(`\nScreenshots saved to: ${SCREENSHOTS_DIR}`);
  console.log(`Test report saved to: test-report.json`);
  
  return report;
}

// Run tests if this file is executed directly
if (require.main === module) {
  runTests().catch(console.error);
}

module.exports = { runTests };