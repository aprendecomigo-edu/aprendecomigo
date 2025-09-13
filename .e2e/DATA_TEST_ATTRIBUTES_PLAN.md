# Data-Test Attributes Implementation Plan

## Overview
To make E2E tests language-agnostic and resilient to UI changes, we need to add `data-test` attributes to key elements across the platform. This follows best practices for test automation and ensures tests work in both English and Portuguese.

## Principles

1. **Test User Intent, Not Implementation**: Focus on what users accomplish, not how the UI looks
2. **Language Independence**: Tests should work regardless of UI language
3. **Stability**: Tests shouldn't break due to text changes, styling updates, or minor UI modifications
4. **Semantic Naming**: Use descriptive, action-oriented attribute names

## When NOT to Add data-test Attributes

Don't add data-test to:
- Static text that never changes (e.g., copyright footers)
- Decorative elements (icons, dividers)
- Internal implementation details users don't interact with
- Every single <div> or <span> wrapper
- Elements already uniquely identifiable by semantic HTML

## School Admin Registration Flow - Priority Elements

### Registration Form (`/signup/`)

```html
<!-- Tab Selection -->
<button data-test="individual-tutor-tab" role="tab">
    Individual Tutor
</button>
<button data-test="school-admin-tab" role="tab">
    School Admin
</button>

<!-- Personal Information Section -->
<input data-test="admin-full-name"
       name="full_name"
       placeholder="Enter your full name">

<input data-test="admin-email"
       name="email"
       type="email"
       placeholder="Enter your email address">

<input data-test="admin-phone"
       name="phone"
       placeholder="+1 (555) 123-4567">

<!-- School Information Section -->
<input data-test="school-name"
       name="school_name"
       placeholder="Your school name">

<!-- Action Buttons -->
<button data-test="submit-registration" type="submit">
    Create Account
</button>

<!-- Success Message -->
<div data-test="registration-success-message">
    <h3>Welcome to Aprende Comigo!</h3>
    <p>Account created successfully! Welcome to Aprende Comigo.</p>
    <p data-test="redirect-message">Redirecting to your dashboard...</p>
</div>
```

### Dashboard (`/dashboard/`)

```html
<!-- School Header -->
<h1 data-test="school-name-header">Escola de Teste</h1>
<div data-test="user-role-badge">school_owner</div>

<!-- User Welcome -->
<h1 data-test="user-welcome">Hello, Maria!</h1>

<!-- Setup Status -->
<div data-test="activation-status">
    <p data-test="activation-instructions">
        You need to add teachers and students to fully activate your account
    </p>
    <p data-test="pending-tasks-instructions">
        Complete the pending tasks below to get started.
    </p>
</div>

<!-- Stats Cards -->
<div data-test="stats-grid">
    <div data-test="teacher-count-card">
        <p data-test="teacher-count-label">Total Teachers</p>
        <p data-test="teacher-count-value">0</p>
    </div>

    <div data-test="student-count-card">
        <p data-test="student-count-label">Total Students</p>
        <p data-test="student-count-value">0</p>
    </div>

    <div data-test="sessions-count-card">
        <p data-test="sessions-count-label">Active Sessions</p>
        <p data-test="sessions-count-value">0</p>
    </div>

    <div data-test="revenue-card">
        <p data-test="revenue-label">Monthly Revenue</p>
        <p data-test="revenue-value">€0</p>
    </div>
</div>

<!-- TODO Section -->
<div data-test="personal-tasks-section">
    <h2 data-test="personal-tasks-title">Tarefas Pessoais</h2>
    <p data-test="tasks-summary">2 pendentes, 0 concluídas</p>

    <div data-test="pending-tasks-list">
        <div data-test="task-item" data-task-type="phone-verification">
            <p data-test="task-title">Verify your phone number</p>
            <span data-test="task-priority">Alta</span>
            <span data-test="task-deadline">2025-09-14</span>
        </div>

        <div data-test="task-item" data-task-type="email-verification">
            <p data-test="task-title">Verify your email address</p>
            <span data-test="task-priority">Alta</span>
            <span data-test="task-deadline">2025-09-14</span>
        </div>
    </div>
</div>
```

## Naming Convention Rules

### 1. User Actions (Buttons, Links)
Pattern: `{verb}-{object}`
- `submit-registration`
- `cancel-booking`
- `open-settings`

### 2. Form Inputs
Pattern: `input-{field-name}`
- `input-email`
- `input-school-name`

### 3. Display Values
Pattern: `value-{metric-name}`
- `value-teacher-count`
- `value-monthly-revenue`

### 4. Containers/Sections
Pattern: `section-{content}`
- `section-pending-tasks`
- `section-user-stats`

### 5. Lists and Items
Pattern: `list-{content}` and `item-{type}`
- `list-students` containing `item-student`
- `list-tasks` containing `item-task`

### 6. States and Feedback
Pattern: `{state}-{context}`
- `success-registration`
- `error-validation`
- `loading-students`

## Benefits

1. **Language Independence**: Tests work in English, Portuguese, or any future language
2. **UI Resilience**: Tests survive CSS class changes, text updates, layout modifications
3. **Semantic Clarity**: Developers understand what tests are targeting
4. **Maintainability**: Easy to update tests when features change
5. **Performance**: More efficient selectors than text-based searches

## Implementation Examples

### Before (Language-Dependent)
```python
# ❌ Breaks in Portuguese
page.get_by_placeholder("Enter your full name")
page.get_by_text("Total Teachers")
page.get_by_role("tab", name="School Admin")
```

### After (Language-Agnostic)
```python
# ✅ Works in any language
page.locator('[data-test="admin-full-name"]')
page.locator('[data-test="teacher-count-value"]')
page.locator('[data-test="school-admin-tab"]')
```

## How Tests Will Use These Attributes

class SchoolAdminActions:
    """Helper class showing how clean tests become"""

    def register_school(self, page, school_data):
        page.locator('[data-test="select-school-admin"]').click()
        page.locator('[data-test="input-school-name"]').fill(school_data['name'])
        page.locator('[data-test="input-admin-email"]').fill(school_data['email'])
        page.locator('[data-test="submit-registration"]').click()

    def verify_registration_success(self, page):
        success = page.locator('[data-test="success-registration"]')
        return success.is_visible()

    def get_teacher_count(self, page):
        metric = page.locator('[data-test="metric-teachers"]')
        return int(metric.get_attribute('data-value'))

## Validation Strategy

1. **Test Coverage**: Ensure all critical user paths have `data-test` attributes
2. **Naming Consistency**: Use linting rules to enforce naming conventions
3. **Documentation**: Keep this plan updated as new features are added
4. **Cross-Language Testing**: Run E2E tests in both English and Portuguese

## Next Steps

1. Add `data-test` attributes to registration form elements
2. Add `data-test` attributes to dashboard key elements
3. Update E2E tests to use new selectors
4. Establish code review guidelines for new `data-test` attributes
5. Create automated checks to ensure critical elements have test attributes
