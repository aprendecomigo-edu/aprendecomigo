import { test, expect } from '@playwright/test';

import { loginAs, logout, waitForPageLoad } from '../../utils/test-helpers';

test.describe('Scheduler Role-Based Permissions', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await waitForPageLoad(page);
  });

  test('Teacher cannot schedule classes', async ({ page }) => {
    // Login as teacher
    await loginAs(page, 'teacher@test.com', 'password123');

    // Navigate to calendar
    await page.click('[data-testid="calendar-nav"]');
    await waitForPageLoad(page);

    // Verify Book Class button is NOT visible
    await expect(page.locator('text="Book Class"')).not.toBeVisible();

    // Verify existing classes are displayed
    await expect(page.locator('[data-testid="calendar-view"]')).toBeVisible();

    // Try to access booking page directly
    await page.goto('/calendar/book');

    // Should be redirected or show access denied
    await expect(page.locator('text="Access Denied"')).toBeVisible({
      timeout: 10000,
    });

    await logout(page);
  });

  test('Student can schedule classes for themselves', async ({ page }) => {
    // Login as student
    await loginAs(page, 'student@test.com', 'password123');

    // Navigate to calendar
    await page.click('[data-testid="calendar-nav"]');
    await waitForPageLoad(page);

    // Verify Book Class button IS visible
    await expect(page.locator('text="Book Class"')).toBeVisible();

    // Click Book Class button
    await page.click('text="Book Class"');
    await waitForPageLoad(page);

    // Should be on booking page
    await expect(page.locator('text="Book a Class"')).toBeVisible();

    // Select a teacher
    await page.click('[data-testid="teacher-select"]');
    await page.click('[data-testid="teacher-option-1"]');

    // Select a date
    await page.click('[data-testid="date-select"]');
    await page.click('[data-testid="date-option-1"]');

    // Wait for available time slots to load
    await expect(page.locator('[data-testid="time-slots"]')).toBeVisible({
      timeout: 10000,
    });

    // Select first available time slot
    await page.click('[data-testid="time-slot-0"]');

    // Fill in class details
    await page.click('[data-testid="duration-select"]');
    await page.click('text="60 minutes"');

    await page.fill('[data-testid="description-input"]', 'Test class booking');

    // Verify student field is readonly (can only book for themselves)
    await expect(page.locator('[data-testid="student-select"]')).toBeDisabled();

    // Submit booking
    await page.click('[data-testid="submit-booking"]');

    // Wait for success message
    await expect(page.locator('text="Class booked successfully"')).toBeVisible({
      timeout: 10000,
    });

    // Should redirect to calendar
    await expect(page.locator('[data-testid="calendar-view"]')).toBeVisible();

    // Verify new class appears in calendar
    await expect(page.locator('text="Test class booking"')).toBeVisible();

    await logout(page);
  });

  test('Admin can schedule classes for any student', async ({ page }) => {
    // Login as admin
    await loginAs(page, 'admin@test.com', 'password123');

    // Navigate to calendar
    await page.click('[data-testid="calendar-nav"]');
    await waitForPageLoad(page);

    // Verify Book Class button IS visible
    await expect(page.locator('text="Book Class"')).toBeVisible();

    // Click Book Class button
    await page.click('text="Book Class"');
    await waitForPageLoad(page);

    // Should be on booking page
    await expect(page.locator('text="Book a Class"')).toBeVisible();

    // Verify admin can select any student
    await expect(page.locator('[data-testid="student-select"]')).toBeEnabled();

    // Select a student
    await page.click('[data-testid="student-select"]');
    await page.click('[data-testid="student-option-1"]');

    // Select a teacher
    await page.click('[data-testid="teacher-select"]');
    await page.click('[data-testid="teacher-option-1"]');

    // Select a date
    await page.click('[data-testid="date-select"]');
    await page.click('[data-testid="date-option-1"]');

    // Wait for available time slots to load
    await expect(page.locator('[data-testid="time-slots"]')).toBeVisible({
      timeout: 10000,
    });

    // Select first available time slot
    await page.click('[data-testid="time-slot-0"]');

    // Fill in class details
    await page.click('[data-testid="duration-select"]');
    await page.click('text="60 minutes"');

    await page.fill('[data-testid="description-input"]', 'Admin scheduled class');

    // Submit booking
    await page.click('[data-testid="submit-booking"]');

    // Wait for success message
    await expect(page.locator('text="Class booked successfully"')).toBeVisible({
      timeout: 10000,
    });

    // Should redirect to calendar
    await expect(page.locator('[data-testid="calendar-view"]')).toBeVisible();

    // Verify new class appears in calendar
    await expect(page.locator('text="Admin scheduled class"')).toBeVisible();

    await logout(page);
  });

  test('Calendar view modes work correctly', async ({ page }) => {
    // Login as student
    await loginAs(page, 'student@test.com', 'password123');

    // Navigate to calendar
    await page.click('[data-testid="calendar-nav"]');
    await waitForPageLoad(page);

    // Verify default view is list
    await expect(page.locator('[data-testid="list-view"]')).toBeVisible();

    // Switch to week view
    await page.click('text="Week"');
    await expect(page.locator('[data-testid="week-view"]')).toBeVisible();

    // Switch back to list view
    await page.click('text="List"');
    await expect(page.locator('[data-testid="list-view"]')).toBeVisible();

    // Test navigation controls
    await page.click('[data-testid="prev-button"]');
    await page.click('[data-testid="today-button"]');
    await page.click('[data-testid="next-button"]');

    await logout(page);
  });

  test('Class detail view shows correct actions based on role', async ({ page }) => {
    // Login as teacher
    await loginAs(page, 'teacher@test.com', 'password123');

    // Navigate to calendar
    await page.click('[data-testid="calendar-nav"]');
    await waitForPageLoad(page);

    // Click on first class
    await page.click('[data-testid="class-card-0"]');
    await waitForPageLoad(page);

    // Verify class details are displayed
    await expect(page.locator('[data-testid="class-details"]')).toBeVisible();

    // Teacher should see confirm, complete, and cancel actions if they own the class
    await expect(page.locator('[data-testid="confirm-button"]')).toBeVisible();
    await expect(page.locator('[data-testid="complete-button"]')).toBeVisible();
    await expect(page.locator('[data-testid="cancel-button"]')).toBeVisible();

    await logout(page);

    // Login as student
    await loginAs(page, 'student@test.com', 'password123');

    // Navigate to calendar
    await page.click('[data-testid="calendar-nav"]');
    await waitForPageLoad(page);

    // Click on first class
    await page.click('[data-testid="class-card-0"]');
    await waitForPageLoad(page);

    // Student should NOT see management actions
    await expect(page.locator('[data-testid="confirm-button"]')).not.toBeVisible();
    await expect(page.locator('[data-testid="complete-button"]')).not.toBeVisible();
    await expect(page.locator('[data-testid="cancel-button"]')).not.toBeVisible();

    await logout(page);
  });

  test('Class management actions work correctly', async ({ page }) => {
    // Login as teacher
    await loginAs(page, 'teacher@test.com', 'password123');

    // Navigate to calendar
    await page.click('[data-testid="calendar-nav"]');
    await waitForPageLoad(page);

    // Click on a scheduled class
    await page.click('[data-testid="class-card-0"]');
    await waitForPageLoad(page);

    // Confirm the class
    await page.click('[data-testid="confirm-button"]');
    await expect(page.locator('text="Class confirmed successfully"')).toBeVisible({
      timeout: 10000,
    });

    // Verify status changed to confirmed
    await expect(page.locator('text="Confirmed"')).toBeVisible();

    // Complete the class
    await page.click('[data-testid="complete-button"]');
    await expect(page.locator('text="Class marked as completed"')).toBeVisible({
      timeout: 10000,
    });

    // Verify status changed to completed
    await expect(page.locator('text="Completed"')).toBeVisible();

    await logout(page);
  });

  test('Error handling works correctly', async ({ page }) => {
    // Login as student
    await loginAs(page, 'student@test.com', 'password123');

    // Navigate to calendar
    await page.click('[data-testid="calendar-nav"]');
    await waitForPageLoad(page);

    // Click Book Class button
    await page.click('text="Book Class"');
    await waitForPageLoad(page);

    // Try to submit without filling required fields
    await page.click('[data-testid="submit-booking"]');

    // Should show validation errors
    await expect(page.locator('text="Please select a teacher"')).toBeVisible();
    await expect(page.locator('text="Please select a date"')).toBeVisible();
    await expect(page.locator('text="Please select a time slot"')).toBeVisible();

    await logout(page);
  });

  test('Responsive design works on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Login as student
    await loginAs(page, 'student@test.com', 'password123');

    // Navigate to calendar
    await page.click('[data-testid="calendar-nav"]');
    await waitForPageLoad(page);

    // Verify mobile layout
    await expect(page.locator('[data-testid="mobile-calendar"]')).toBeVisible();

    // Test mobile navigation
    await page.click('[data-testid="mobile-menu-button"]');
    await expect(page.locator('[data-testid="mobile-nav-menu"]')).toBeVisible();

    await logout(page);
  });
});
