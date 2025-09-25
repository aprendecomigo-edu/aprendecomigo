# Visual Test Plan: Multiple Guardians Feature (Issue #304)

## Test Environment Setup
- **User Type**: School Admin
- **Test Data**: Create test student with existing primary guardian
- **Browser**: Chrome/Chromium via Playwright
- **Starting Point**: Logged in as admin user

## Test Scenarios

### 1. Navigate to Guardian Management Page
**Steps:**
1. Start from admin dashboard
2. Navigate to People Management
3. Select a student
4. Click on "Manage Guardians" button

**Expected:**
- Guardian management page loads
- Shows existing primary guardian with "PRIMARY" badge
- Shows guardian permissions clearly
- "Add Guardian" button is visible

### 2. Add New Guardian (Non-Primary)
**Steps:**
1. Click "Add Guardian" button
2. Enter new guardian details:
   - Email: newguardian@test.com
   - Name: Secondary Guardian
   - Relationship: Father
   - Keep "Primary Guardian" unchecked
3. Select permissions:
   - Can book classes: Yes
   - Can view records: Yes
   - Can edit profile: No
   - Can manage finances: No (auto-disabled for non-primary)
4. Submit form

**Expected:**
- Modal form appears smoothly
- Financial permission is disabled for non-primary
- Success message appears
- New guardian appears in list
- Guardian list updates without page refresh (HTMX)

### 3. Set Guardian as Primary
**Steps:**
1. Find the non-primary guardian
2. Click "Set as Primary" button
3. Confirm the action in dialog

**Expected:**
- Confirmation dialog appears
- After confirmation:
  - Previous primary loses "PRIMARY" badge
  - New guardian gets "PRIMARY" badge
  - Financial permissions automatically granted
  - Success message appears
  - List updates via HTMX

### 4. Edit Guardian Permissions
**Steps:**
1. Click "Edit Permissions" on a non-primary guardian
2. Modify permissions:
   - Can book classes: No
   - Can view records: Yes
   - Can edit profile: Yes
3. Save changes

**Expected:**
- Edit form loads in modal
- Current permissions pre-populated
- Financial permission remains disabled for non-primary
- Success message after save
- Permission badges update in real-time

### 5. Attempt to Remove Last Guardian
**Steps:**
1. Navigate to student with only one guardian
2. Attempt to click "Remove" button (should be disabled)

**Expected:**
- Remove button is disabled or hidden
- Tooltip/message indicates cannot remove last guardian

### 6. Remove Non-Primary Guardian
**Steps:**
1. Navigate to student with multiple guardians
2. Click "Remove" on non-primary guardian
3. Confirm removal

**Expected:**
- Confirmation dialog appears
- After confirmation:
  - Guardian removed from list
  - Success message appears
  - List updates via HTMX

### 7. Visual States Testing
**Test:**
- Primary guardian visual distinction (blue border/badge)
- Permission badges (green for granted, gray for denied)
- Disabled states for buttons
- Loading states during HTMX operations
- Error message display
- Success message display
- Modal overlays
- Responsive design on mobile viewport

### 8. Form Validation
**Steps:**
1. Try to add guardian with invalid email
2. Try to add duplicate guardian
3. Try to submit with missing required fields

**Expected:**
- Inline validation messages
- Form doesn't submit
- Clear error indicators
- Error messages are helpful

### 9. Permission Enforcement
**Steps:**
1. Login as primary guardian
2. Verify can access guardian management
3. Login as non-primary guardian
4. Verify appropriate access restrictions

**Expected:**
- Primary guardian can manage other guardians
- Non-primary guardian has restricted access
- Clear permission denied messages when appropriate

### 10. Cross-School Testing
**Steps:**
1. Create guardian relationship in School A
2. Navigate to School B
3. Verify guardian doesn't appear
4. Add same guardian to School B

**Expected:**
- Guardian relationships are school-scoped
- Same guardian can have different roles in different schools
- Only one primary guardian globally

## Key Elements to Verify

### Visual Components
- PRIMARY badge styling (background color, text color, positioning)
- Permission badges (colors, icons if any)
- Button states (enabled, disabled, hover, active)
- Modal appearance and animations
- Form field styling and validation states
- Success/error message styling

### Functional Components
- HTMX updates without page refresh
- Modal forms work correctly
- Confirmation dialogs appear when needed
- Form validation works client-side
- Permission rules are enforced

### Responsive Design
- Test on desktop (1920x1080)
- Test on tablet (768x1024)
- Test on mobile (375x667)
- Verify touch interactions on mobile

## Success Criteria
- All CRUD operations work correctly
- Visual feedback is clear and immediate
- Business rules are enforced (one primary guardian)
- HTMX updates work smoothly
- No JavaScript errors in console
- Forms are accessible and usable
- Mobile experience is functional
