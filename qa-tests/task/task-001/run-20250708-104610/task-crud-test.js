const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function runTaskCrudTest() {
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
        viewport: { width: 1280, height: 720 }
    });
    const page = await context.newPage();

    const runDir = __dirname;
    const screenshotsDir = path.join(runDir, 'screenshots');

    const results = {
        runId: path.basename(runDir),
        timestamp: new Date().toISOString(),
        environment: 'macOS development',
        browser: 'Playwright Chrome',
        overallResult: 'PASS',
        stepsResults: [],
        totalSteps: 0,
        passedSteps: 0,
        failedSteps: 0
    };

    async function takeScreenshot(stepName) {
        const filename = `${stepName.replace(/[^a-zA-Z0-9]/g, '_')}.png`;
        await page.screenshot({
            path: path.join(screenshotsDir, filename),
            fullPage: true
        });
        return filename;
    }

    async function addStepResult(stepNumber, description, status, details = '', screenshot = null) {
        results.totalSteps++;
        if (status === 'PASS') {
            results.passedSteps++;
        } else {
            results.failedSteps++;
            results.overallResult = 'FAIL';
        }

        results.stepsResults.push({
            step: stepNumber,
            description,
            status,
            details,
            screenshot
        });

        console.log(`Step ${stepNumber}: ${status} - ${description}`);
    }

    try {
        // Step 1: Navigate to Application
        console.log('Step 1: Navigate to Application');
        await page.goto('http://localhost:8081');
        await page.waitForTimeout(2000);
        const screenshot1 = await takeScreenshot('01_app_loaded');

        // Check if page loaded
        const title = await page.title();
        if (title) {
            await addStepResult(1, 'Navigate to Application', 'PASS', 'Application loaded successfully', screenshot1);
        } else {
            await addStepResult(1, 'Navigate to Application', 'FAIL', 'Application failed to load', screenshot1);
            return results;
        }

        // Step 2: Complete Login Process
        console.log('Step 2: Login Process');

        // Wait for login interface to appear
        await page.waitForTimeout(2000);

        // Check if we're already logged in by looking for dashboard elements
        const dashboardElements = await page.$$('[data-testid*="dashboard"], [class*="dashboard"], h1, h2, h3');
        let isLoggedIn = false;

        for (const element of dashboardElements) {
            const text = await element.textContent();
            if (text && (text.includes('Dashboard') || text.includes('Painel') || text.includes('Bem-vindo'))) {
                isLoggedIn = true;
                break;
            }
        }

        if (!isLoggedIn) {
            // Look for email input field
            const emailInput = await page.$('input[type="email"], input[placeholder*="email" i], input[placeholder*="e-mail" i]');
            if (emailInput) {
                await emailInput.fill('anapmc.carvalho@gmail.com');
                const screenshot2 = await takeScreenshot('02_email_filled');

                // Look for submit button
                const submitButton = await page.$('button[type="submit"], button:has-text("Entrar"), button:has-text("Request"), button:has-text("Solicitar")');
                if (submitButton) {
                    await submitButton.click();
                    await page.waitForTimeout(2000);
                    const screenshot3 = await takeScreenshot('03_verification_code_requested');

                    // Look for verification code input
                    const codeInput = await page.$('input[placeholder*="código" i], input[placeholder*="code" i], input[placeholder*="verification" i]');
                    if (codeInput) {
                        // Use development bypass - any 6-digit code
                        await codeInput.fill('123456');
                        const screenshot4 = await takeScreenshot('04_verification_code_entered');

                        // Submit verification code
                        const verifyButton = await page.$('button[type="submit"], button:has-text("Verificar"), button:has-text("Verify")');
                        if (verifyButton) {
                            await verifyButton.click();
                            await page.waitForTimeout(3000);
                            const screenshot5 = await takeScreenshot('05_authentication_complete');
                        }
                    }
                }
            }
        }

        // Check if we're now authenticated
        await page.waitForTimeout(2000);
        const finalScreenshot = await takeScreenshot('06_final_dashboard_state');

        // Look for dashboard content or task-related content
        const pageContent = await page.content();
        const hasTaskContent = pageContent.includes('Tarefa') || pageContent.includes('Task') ||
                              pageContent.includes('Pendente') || pageContent.includes('Pending');

        if (hasTaskContent) {
            await addStepResult(2, 'Login Process', 'PASS', 'Authentication successful and task content visible', finalScreenshot);
        } else {
            await addStepResult(2, 'Login Process', 'FAIL', 'Authentication completed but task content not found', finalScreenshot);
        }

        // Step 3: Look for Task Interface
        console.log('Step 3: Look for Task Interface');

        // Search for task-related elements
        const taskElements = await page.$$('[data-testid*="task"], [class*="task"], [class*="tarefa"]');
        const taskButtons = await page.$$('button:has-text("Add"), button:has-text("Nova"), button:has-text("Create"), button:has-text("+")');

        let taskInterfaceFound = false;

        // Check for table elements that might contain tasks
        const tables = await page.$$('table, [role="table"], [class*="table"]');
        if (tables.length > 0) {
            for (const table of tables) {
                const tableText = await table.textContent();
                if (tableText && (tableText.includes('Tarefa') || tableText.includes('Task') ||
                                 tableText.includes('Pendente') || tableText.includes('Due'))) {
                    taskInterfaceFound = true;
                    break;
                }
            }
        }

        // Also check for any task-related headings
        const headings = await page.$$('h1, h2, h3, h4, h5, h6');
        for (const heading of headings) {
            const text = await heading.textContent();
            if (text && (text.includes('Tarefa') || text.includes('Task') || text.includes('Pendente'))) {
                taskInterfaceFound = true;
                break;
            }
        }

        const screenshot7 = await takeScreenshot('07_task_interface_search');

        if (taskInterfaceFound) {
            await addStepResult(3, 'Task Interface Detection', 'PASS', 'Task interface elements found', screenshot7);

            // Step 4: Test Task Creation
            console.log('Step 4: Attempt Task Creation');

            // Look for add/create buttons
            let createButtonFound = false;

            for (const button of taskButtons) {
                const buttonText = await button.textContent();
                if (buttonText && (buttonText.includes('+') || buttonText.toLowerCase().includes('add') ||
                                  buttonText.toLowerCase().includes('nova') || buttonText.toLowerCase().includes('create'))) {
                    try {
                        await button.click();
                        await page.waitForTimeout(1000);
                        createButtonFound = true;
                        break;
                    } catch (e) {
                        // Try next button
                        continue;
                    }
                }
            }

            const screenshot8 = await takeScreenshot('08_task_creation_attempt');

            if (createButtonFound) {
                await addStepResult(4, 'Task Creation Interface', 'PASS', 'Task creation button clicked successfully', screenshot8);

                // Look for form fields
                const titleInput = await page.$('input[placeholder*="título" i], input[placeholder*="title" i], input[name*="title"]');
                const descInput = await page.$('textarea[placeholder*="descrição" i], textarea[placeholder*="description" i], input[placeholder*="descrição" i]');

                if (titleInput) {
                    await titleInput.fill('Test Task - CRUD Operations');
                    if (descInput) {
                        await descInput.fill('Testing task creation functionality');
                    }

                    const screenshot9 = await takeScreenshot('09_task_form_filled');

                    // Try to save
                    const saveButton = await page.$('button[type="submit"], button:has-text("Salvar"), button:has-text("Save"), button:has-text("Criar")');
                    if (saveButton) {
                        await saveButton.click();
                        await page.waitForTimeout(2000);
                        const screenshot10 = await takeScreenshot('10_task_save_attempt');

                        await addStepResult(5, 'Task Creation', 'PASS', 'Task creation form submitted', screenshot10);
                    } else {
                        await addStepResult(5, 'Task Creation', 'FAIL', 'Save button not found', screenshot9);
                    }
                } else {
                    await addStepResult(4, 'Task Creation Interface', 'FAIL', 'Task form fields not found', screenshot8);
                }
            } else {
                await addStepResult(4, 'Task Creation Interface', 'FAIL', 'Task creation button not found or not clickable', screenshot8);
            }
        } else {
            await addStepResult(3, 'Task Interface Detection', 'FAIL', 'Task interface not found on page', screenshot7);
        }

    } catch (error) {
        console.error('Test execution error:', error);
        await addStepResult(0, 'Test Execution', 'FAIL', `Test failed with error: ${error.message}`, null);
    } finally {
        await browser.close();
    }

    return results;
}

// Run the test
runTaskCrudTest().then(results => {
    // Write results to JSON file
    fs.writeFileSync(
        path.join(__dirname, 'test-results.json'),
        JSON.stringify(results, null, 2)
    );

    console.log('\n=== TEST RESULTS ===');
    console.log(`Overall Result: ${results.overallResult}`);
    console.log(`Steps: ${results.passedSteps}/${results.totalSteps} passed`);
    console.log('Run completed successfully');
}).catch(error => {
    console.error('Test runner error:', error);
    process.exit(1);
});
