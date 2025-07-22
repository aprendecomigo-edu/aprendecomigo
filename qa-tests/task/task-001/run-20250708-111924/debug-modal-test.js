const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function debugModalTest() {
    const browser = await chromium.launch({
        headless: false,
        slowMo: 1000  // Slower for debugging
    });
    const context = await browser.newContext({
        viewport: { width: 1280, height: 720 }
    });
    const page = await context.newPage();

    const runDir = __dirname;
    const screenshotsDir = path.join(runDir, 'screenshots');

    console.log('🔍 DEBUG: Modal Opening Investigation');

    try {
        // Go to application
        console.log('\n1. Loading application...');
        await page.goto('http://localhost:8081');
        await page.waitForTimeout(4000);

        // Quick auth (user should be logged in from previous test)
        const isLoggedIn = (await page.textContent('body')).includes('Tarefas');
        if (!isLoggedIn) {
            console.log('   Need to authenticate...');
            const emailInput = await page.$('input[type="email"]');
            if (emailInput) {
                await emailInput.fill('anapmc.carvalho@gmail.com');
                const submitBtn = await page.$('button[type="submit"]');
                await submitBtn.click();
                await page.waitForTimeout(3000);
                const codeInput = await page.$('input[placeholder*="code"]');
                await codeInput.fill('123456');
                const verifyBtn = await page.$('button[type="submit"]');
                await verifyBtn.click();
                await page.waitForTimeout(4000);
            }
        }

        // Remove overlays
        console.log('\n2. Removing overlays...');
        await page.evaluate(() => {
            const overlays = document.querySelectorAll('[class*="backdrop"], [class*="bg-background-dark"]');
            overlays.forEach(el => el.remove());
        });

        const skipBtn = await page.$('button:has-text("Pular")');
        if (skipBtn) {
            await skipBtn.click();
            await page.waitForTimeout(2000);
        }

        // Take screenshot before clicking
        await page.screenshot({ path: path.join(screenshotsDir, 'debug_01_before_click.png'), fullPage: true });

        // Debug: Find all buttons on page
        console.log('\n3. Analyzing page buttons...');
        const allButtons = await page.$$('button');
        console.log(`   Found ${allButtons.length} buttons on page`);

        for (let i = 0; i < allButtons.length; i++) {
            const button = allButtons[i];
            const text = await button.textContent();
            const className = await button.getAttribute('class');
            const isVisible = await button.isVisible();

            if (text && (text.includes('Add') || text.includes('Task'))) {
                console.log(`   Button ${i}: "${text}" - Visible: ${isVisible}`);
                console.log(`   Classes: ${className}`);
            }
        }

        // Find the specific Add Task button
        console.log('\n4. Locating Add Task button...');
        const addTaskButton = await page.$('button:has-text("Add Task")');

        if (addTaskButton) {
            const isVisible = await addTaskButton.isVisible();
            const isEnabled = await addTaskButton.isEnabled();
            const boundingBox = await addTaskButton.boundingBox();

            console.log(`   Add Task button found!`);
            console.log(`   Visible: ${isVisible}, Enabled: ${isEnabled}`);
            console.log(`   Position: ${JSON.stringify(boundingBox)}`);

            // Check if button is covered by other elements
            const clickablePoint = await page.evaluate((button) => {
                const rect = button.getBoundingClientRect();
                const centerX = rect.left + rect.width / 2;
                const centerY = rect.top + rect.height / 2;
                const elementAtPoint = document.elementFromPoint(centerX, centerY);

                return {
                    center: { x: centerX, y: centerY },
                    elementAtPoint: elementAtPoint ? elementAtPoint.tagName + '.' + elementAtPoint.className : 'none',
                    isButton: elementAtPoint === button
                };
            }, addTaskButton);

            console.log(`   Clickable point: ${JSON.stringify(clickablePoint)}`);

            // Try clicking the button
            console.log('\n5. Attempting to click Add Task button...');

            try {
                await addTaskButton.click();
                console.log('   ✓ Button clicked successfully');
            } catch (error) {
                console.log(`   ❌ Click failed: ${error.message}`);

                // Try force click
                console.log('   Trying force click...');
                await page.evaluate(() => {
                    const btn = document.querySelector('button:has-text("Add Task")') ||
                               Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Add Task'));
                    if (btn) {
                        btn.click();
                        console.log('Force clicked via JS');
                    }
                });
            }

            // Wait and check for modal
            await page.waitForTimeout(3000);
            await page.screenshot({ path: path.join(screenshotsDir, 'debug_02_after_click.png'), fullPage: true });

            console.log('\n6. Checking for modal...');

            // Look for modal elements
            const modal = await page.$('[role="dialog"]');
            const alertDialog = await page.$('[class*="AlertDialog"]');
            const modalContent = await page.$('[class*="modal"], [class*="Modal"]');

            console.log(`   Modal with role="dialog": ${modal ? 'FOUND' : 'NOT FOUND'}`);
            console.log(`   AlertDialog: ${alertDialog ? 'FOUND' : 'NOT FOUND'}`);
            console.log(`   Modal content: ${modalContent ? 'FOUND' : 'NOT FOUND'}`);

            // Check for any new elements after click
            const bodyTextAfter = await page.textContent('body');
            const hasNewContent = bodyTextAfter.includes('Enter task title') ||
                                 bodyTextAfter.includes('Create New Task') ||
                                 bodyTextAfter.includes('Title') ||
                                 bodyTextAfter.includes('Save');

            console.log(`   New form content detected: ${hasNewContent}`);

            // Look for input fields that might have appeared
            const titleInputs = await page.$$('input[placeholder*="title"], input[placeholder*="Title"]');
            console.log(`   Title input fields found: ${titleInputs.length}`);

            if (titleInputs.length > 0) {
                console.log('\n7. Modal opened! Testing form interaction...');
                const titleInput = titleInputs[0];

                await titleInput.fill('DEBUG TEST TASK');
                console.log('   ✓ Title filled');

                await page.waitForTimeout(1000);
                await page.screenshot({ path: path.join(screenshotsDir, 'debug_03_form_filled.png'), fullPage: true });

                // Look for save button
                const saveButton = await page.$('button:has-text("Save")');
                if (saveButton) {
                    await saveButton.click();
                    await page.waitForTimeout(3000);

                    const finalBodyText = await page.textContent('body');
                    const taskCreated = finalBodyText.includes('DEBUG TEST TASK');

                    console.log(`   Task created successfully: ${taskCreated}`);

                    await page.screenshot({ path: path.join(screenshotsDir, 'debug_04_task_created.png'), fullPage: true });

                    return { success: true, taskCreated };
                } else {
                    console.log('   ❌ Save button not found');
                }
            } else {
                console.log('\n7. Modal did not open properly');

                // Debug: Check what elements are currently visible
                const visibleElements = await page.evaluate(() => {
                    const elements = Array.from(document.querySelectorAll('*')).filter(el => {
                        const style = window.getComputedStyle(el);
                        return style.display !== 'none' && style.visibility !== 'hidden' && el.offsetWidth > 0 && el.offsetHeight > 0;
                    });

                    return elements.slice(-20).map(el => ({
                        tag: el.tagName,
                        className: el.className,
                        text: el.textContent ? el.textContent.substring(0, 50) : ''
                    }));
                });

                console.log('   Recent visible elements:');
                visibleElements.forEach((el, i) => {
                    console.log(`     ${i}: ${el.tag}.${el.className} - "${el.text}"`);
                });
            }

        } else {
            console.log('   ❌ Add Task button not found');
        }

    } catch (error) {
        console.error('Debug test error:', error);
        await page.screenshot({ path: path.join(screenshotsDir, 'debug_error.png'), fullPage: true });
    } finally {
        await browser.close();
    }
}

// Run debug test
debugModalTest().then(result => {
    console.log('\n' + '='.repeat(50));
    console.log('🔍 DEBUG TEST COMPLETED');
    console.log('='.repeat(50));
    if (result && result.success) {
        console.log('✅ Modal opening and task creation SUCCESSFUL!');
        console.log(`📝 Task created: ${result.taskCreated}`);
    } else {
        console.log('❌ Modal opening issues detected');
        console.log('📸 Check debug screenshots for visual analysis');
    }
}).catch(error => {
    console.error('Debug test failed:', error);
});
