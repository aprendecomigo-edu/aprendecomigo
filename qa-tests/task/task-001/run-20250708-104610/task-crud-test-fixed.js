const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function runTaskCrudTest() {
    const browser = await chromium.launch({ headless: false, slowMo: 500 }); // Visible for debugging
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
        if (details) console.log(`  Details: ${details}`);
    }

    try {
        // Step 1: Navigate to Application
        console.log('\n=== Step 1: Navigate to Application ===');
        await page.goto('http://localhost:8081');
        await page.waitForTimeout(3000);
        const screenshot1 = await takeScreenshot('01_app_loaded');

        const title = await page.title();
        if (title) {
            await addStepResult(1, 'Navigate to Application', 'PASS', 'Application loaded successfully', screenshot1);
        } else {
            await addStepResult(1, 'Navigate to Application', 'FAIL', 'Application failed to load', screenshot1);
            return results;
        }

        // Step 2: Complete Login Process
        console.log('\n=== Step 2: Login Process ===');

        // Check if we're already logged in
        await page.waitForTimeout(2000);
        let isLoggedIn = false;

        // Look for Portuguese dashboard content
        const pageText = await page.textContent('body');
        if (pageText.includes('Tarefas') || pageText.includes('Dashboard') || pageText.includes('Painel')) {
            isLoggedIn = true;
            console.log('Already logged in - dashboard content detected');
        }

        if (!isLoggedIn) {
            console.log('Need to login - looking for email input');
            const emailInput = await page.$('input[type="email"], input[placeholder*="email" i], input[placeholder*="e-mail" i]');
            if (emailInput) {
                await emailInput.fill('anapmc.carvalho@gmail.com');
                const screenshot2 = await takeScreenshot('02_email_filled');

                const submitButton = await page.$('button[type="submit"], button:has-text("Entrar"), button:has-text("Request"), button:has-text("Solicitar")');
                if (submitButton) {
                    await submitButton.click();
                    await page.waitForTimeout(3000);
                    const screenshot3 = await takeScreenshot('03_verification_code_requested');

                    const codeInput = await page.$('input[placeholder*="código" i], input[placeholder*="code" i], input[placeholder*="verification" i]');
                    if (codeInput) {
                        await codeInput.fill('123456'); // Development bypass
                        const screenshot4 = await takeScreenshot('04_verification_code_entered');

                        const verifyButton = await page.$('button[type="submit"], button:has-text("Verificar"), button:has-text("Verify")');
                        if (verifyButton) {
                            await verifyButton.click();
                            await page.waitForTimeout(4000);
                            const screenshot5 = await takeScreenshot('05_authentication_complete');
                        }
                    }
                }
            }
        }

        // Verify we're logged in and can see task content
        await page.waitForTimeout(2000);
        const finalPageText = await page.textContent('body');
        const screenshot6 = await takeScreenshot('06_final_dashboard_state');

        if (finalPageText.includes('Tarefas') || finalPageText.includes('Task')) {
            await addStepResult(2, 'Login Process', 'PASS', 'Authentication successful and task content visible', screenshot6);
        } else {
            await addStepResult(2, 'Login Process', 'FAIL', 'Authentication completed but task content not found', screenshot6);
        }

        // Step 3: Find Task Interface
        console.log('\n=== Step 3: Find Task Interface ===');

        // Look for the "Tarefas Pendentes" heading
        const taskHeading = await page.$('h1:has-text("Tarefas"), h2:has-text("Tarefas"), h3:has-text("Tarefas"), h4:has-text("Tarefas")');

        let taskInterfaceFound = false;
        if (taskHeading) {
            taskInterfaceFound = true;
            console.log('Found task heading');
        } else {
            // Look for any task-related content
            const taskElements = await page.$$('[data-testid*="task"], [class*="task"], [class*="tarefa"]');
            if (taskElements.length > 0) {
                taskInterfaceFound = true;
                console.log(`Found ${taskElements.length} task-related elements`);
            }
        }

        const screenshot7 = await takeScreenshot('07_task_interface_search');

        if (taskInterfaceFound) {
            await addStepResult(3, 'Task Interface Detection', 'PASS', 'Task interface elements found', screenshot7);
        } else {
            await addStepResult(3, 'Task Interface Detection', 'FAIL', 'Task interface not found on page', screenshot7);
            return results;
        }

        // Step 4: Find Add Task Button
        console.log('\n=== Step 4: Find Add Task Button ===');

        // Look specifically for "Add Task" button
        const addTaskButton = await page.$('button:has-text("Add Task")');
        let buttonFound = false;
        let buttonDetails = '';

        if (addTaskButton) {
            buttonFound = true;
            buttonDetails = 'Found "Add Task" button';
            console.log('Found "Add Task" button');
        } else {
            // Look for Plus icon buttons near task content
            const plusButtons = await page.$$('button svg');
            for (const button of plusButtons) {
                const parent = await button.$('xpath=..');
                if (parent) {
                    const buttonText = await parent.textContent();
                    if (buttonText && (buttonText.includes('Add') || buttonText.includes('+'))) {
                        buttonFound = true;
                        buttonDetails = `Found button with text: "${buttonText}"`;
                        break;
                    }
                }
            }

            if (!buttonFound) {
                // List all buttons for debugging
                const allButtons = await page.$$('button');
                const buttonTexts = [];
                for (const btn of allButtons) {
                    const text = await btn.textContent();
                    if (text && text.trim()) {
                        buttonTexts.push(text.trim());
                    }
                }
                buttonDetails = `Available buttons: ${buttonTexts.join(', ')}`;
            }
        }

        const screenshot8 = await takeScreenshot('08_add_task_button_search');

        if (buttonFound) {
            await addStepResult(4, 'Add Task Button Detection', 'PASS', buttonDetails, screenshot8);

            // Step 5: Click Add Task Button
            console.log('\n=== Step 5: Click Add Task Button ===');

            try {
                if (addTaskButton) {
                    await addTaskButton.click();
                } else {
                    // Click the first button that might be the add button
                    const buttons = await page.$$('button');
                    for (const btn of buttons) {
                        const text = await btn.textContent();
                        if (text && (text.includes('Add') || text.includes('+'))) {
                            await btn.click();
                            break;
                        }
                    }
                }

                await page.waitForTimeout(2000);
                const screenshot9 = await takeScreenshot('09_add_task_clicked');

                // Look for modal or form
                const modal = await page.$('[role="dialog"], .modal, [data-testid*="dialog"], [data-testid*="modal"]');
                const titleInput = await page.$('input[placeholder*="title" i], input[placeholder*="título" i]');

                if (modal || titleInput) {
                    await addStepResult(5, 'Task Creation Modal', 'PASS', 'Task creation form opened', screenshot9);

                    // Step 6: Fill Task Form
                    console.log('\n=== Step 6: Fill Task Form ===');

                    if (titleInput) {
                        await titleInput.fill('Test Task - CRUD Operations');

                        const descInput = await page.$('textarea[placeholder*="description" i], textarea[placeholder*="descrição" i]');
                        if (descInput) {
                            await descInput.fill('Testing task creation functionality');
                        }

                        const screenshot10 = await takeScreenshot('10_task_form_filled');

                        // Try to save
                        const saveButton = await page.$('button:has-text("Save"), button:has-text("Salvar"), button:has-text("Create"), button:has-text("Criar")');
                        if (saveButton) {
                            await saveButton.click();
                            await page.waitForTimeout(3000);
                            const screenshot11 = await takeScreenshot('11_task_creation_complete');

                            await addStepResult(6, 'Task Creation', 'PASS', 'Task creation form submitted successfully', screenshot11);
                        } else {
                            await addStepResult(6, 'Task Creation', 'FAIL', 'Save button not found', screenshot10);
                        }
                    } else {
                        await addStepResult(6, 'Task Creation', 'FAIL', 'Title input field not found', screenshot9);
                    }
                } else {
                    await addStepResult(5, 'Task Creation Modal', 'FAIL', 'Task creation form did not open', screenshot9);
                }
            } catch (error) {
                await addStepResult(5, 'Task Creation Modal', 'FAIL', `Error clicking button: ${error.message}`, screenshot8);
            }
        } else {
            await addStepResult(4, 'Add Task Button Detection', 'FAIL', buttonDetails, screenshot8);
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
        path.join(__dirname, 'test-results-fixed.json'),
        JSON.stringify(results, null, 2)
    );

    console.log('\n=== FINAL TEST RESULTS ===');
    console.log(`Overall Result: ${results.overallResult}`);
    console.log(`Steps: ${results.passedSteps}/${results.totalSteps} passed`);

    if (results.failedSteps > 0) {
        console.log('\nFailed Steps:');
        results.stepsResults.filter(step => step.status === 'FAIL').forEach(step => {
            console.log(`- Step ${step.step}: ${step.description} - ${step.details}`);
        });
    }

    console.log('\nTest completed successfully');
}).catch(error => {
    console.error('Test runner error:', error);
    process.exit(1);
});
