# Data-Test Attributes Conventions

## Overview
This document defines the standards for `data-test` attributes across our Django + HTMX + Alpine.js application. These attributes enable resilient, language-agnostic E2E testing.

## Core Principles

1. **Test User Intent, Not Implementation** - Focus on what users accomplish
2. **Language Independence** - Tests work regardless of UI language
3. **Stability Over Specificity** - Survive UI changes without breaking
4. **Meaningful Names** - Self-documenting attribute values

## Naming Convention Rules

### 1. User Actions (Buttons, Links, Clickable Elements)
**Pattern:** `{verb}-{object}`

```html
<!-- Examples -->
<button data-test="submit-registration">Create Account</button>
<button data-test="cancel-subscription">Cancel</button>
<a data-test="view-profile">View Profile</a>
<button data-test="delete-task">🗑️</button>
```

### 2. Selections/Choices (Tabs, Radio, Dropdowns)
**Pattern:** `select-{choice}`

```html
<!-- Examples -->
<button data-test="select-school-admin" role="tab">School Admin</button>
<input data-test="select-monthly-plan" type="radio" value="monthly">
<option data-test="select-portuguese">Português</option>
```

### 3. Form Inputs
**Pattern:** `input-{field-name}`

```html
<!-- Examples -->
<input data-test="input-email" name="email" type="email">
<input data-test="input-school-name" name="school_name">
<textarea data-test="input-description"></textarea>
<select data-test="input-country">...</select>
```

### 4. Display Values/Metrics
**Pattern:** `metric-{name}` with `data-value` attribute

```html
<!-- Examples -->
<div data-test="metric-teacher-count" data-value="5">
    <span>Total Teachers</span>
    <span>5</span>
</div>

<div data-test="metric-monthly-revenue" data-value="1500.00" data-currency="EUR">
    <p>Monthly Revenue</p>
    <p>€1,500.00</p>
</div>
```

### 5. Content Sections
**Pattern:** `section-{content}`

```html
<!-- Examples -->
<div data-test="section-pending-tasks">...</div>
<section data-test="section-user-stats">...</section>
<div data-test="section-notifications">...</div>
```

### 6. Lists and Items
**Pattern:** `list-{content}` and `item-{singular}`

```html
<!-- Examples -->
<ul data-test="list-students">
    <li data-test="item-student" data-student-id="123">
        João Silva
    </li>
    <li data-test="item-student" data-student-id="124">
        Maria Costa
    </li>
</ul>

<div data-test="list-tasks">
    <div data-test="item-task" data-task-id="1" data-task-status="pending">
        Verify email
    </div>
</div>
```

### 7. States and Feedback
**Pattern:** `{state}-{context}`

```html
<!-- Examples -->
<div data-test="success-registration">Welcome!</div>
<div data-test="error-validation">Please fix the errors below</div>
<div data-test="loading-students">Loading...</div>
<div data-test="empty-tasks">No tasks pending</div>
```

### 8. Modals/Overlays
**Pattern:** `modal-{purpose}`

```html
<!-- Examples -->
<div data-test="modal-add-teacher" data-modal-state="open">...</div>
<div data-test="modal-confirm-delete" data-modal-state="closed">...</div>
```

## HTMX-Specific Patterns

### HTMX Actions
```html
<!-- Actions that trigger HTMX requests -->
<button data-test="load-more-students"
        hx-get="/students?page=2"
        hx-target="#student-list">
    Load More
</button>

<button data-test="refresh-metrics"
        hx-get="/api/metrics"
        hx-trigger="click, every 30s">
    Refresh
</button>
```

### HTMX Targets
```html
<!-- Containers that receive HTMX responses -->
<div data-test="container-students"
     id="student-list"
     data-loaded="true">
    <!-- HTMX will swap content here -->
</div>
```

### HTMX States
```html
<!-- Track HTMX loading states -->
<div data-test="section-tasks"
     data-loading-state="idle">
    <!-- Use Alpine.js to update: -->
    <!-- :data-loading-state="loading ? 'loading' : 'idle'" -->
</div>
```

## Alpine.js Patterns

### Interactive Components
```html
<!-- Dropdowns, accordions, toggles -->
<div data-test="dropdown-filter"
     data-dropdown-state="closed"
     x-data="{ open: false }"
     :data-dropdown-state="open ? 'open' : 'closed'">
    <button data-test="toggle-filter">Filter</button>
    <div data-test="filter-options">...</div>
</div>
```

### Alpine.js Forms
```html
<!-- Forms with Alpine.js validation -->
<form data-test="form-add-student"
      data-form-state="idle"
      x-data="{ submitting: false, errors: {} }"
      :data-form-state="submitting ? 'submitting' : 'idle'">
    <input data-test="input-student-name"
           :class="{ 'error': errors.name }">
</form>
```

## When NOT to Add data-test

### Don't Add to:
- Static text (copyright, legal text)
- Decorative elements (icons without actions, dividers)
- Wrapper divs that only provide layout
- Elements already unique by semantic HTML (`<main>`, `<header>`)
- Third-party components you don't control
- CSS-only animations or transitions

### Examples of What NOT to Test:
```html
<!-- Don't add data-test to these -->
<div class="container">  <!-- Just a layout wrapper -->
<span class="icon-decorative">🎨</span>  <!-- Decorative only -->
<p>© 2024 Company Name</p>  <!-- Static footer text -->
<div class="css-spinner"></div>  <!-- CSS-only element -->
```

## Anti-Patterns to Avoid

### Testing Implementation Details
```html
<!-- Bad: Tied to CSS -->
<button data-test="blue-primary-button-large">

<!-- Good: Describes intent -->
<button data-test="submit-registration">
```

### Over-Specific Naming
```html
<!-- Bad: Too specific -->
<div data-test="dashboard-left-sidebar-teacher-stats-card-title">

<!-- Good: Concise and clear -->
<div data-test="metric-teachers">
```

### Duplicating DOM Structure
```html
<!-- Bad: Mirrors HTML structure -->
<div data-test="div-wrapper">
    <span data-test="span-label">
    <p data-test="p-value">

<!-- Good: Semantic naming -->
<div data-test="metric-revenue" data-value="1000">
```

### Language-Dependent Attributes
```html
<!-- Bad: Will break in Portuguese -->
<button data-test="create-account-button">

<!-- Good: Language agnostic -->
<button data-test="submit-registration">
```

## Additional Data Attributes

Use supplementary `data-*` attributes for state and metadata:

```html
<!-- Task with multiple data attributes -->
<div data-test="item-task"
     data-task-id="123"
     data-task-status="pending"
     data-task-priority="high">
    Complete profile
</div>

<!-- Student with metadata -->
<div data-test="item-student"
     data-student-id="456"
     data-student-status="active"
     data-student-grade="10">
    Ana Silva
</div>
```

## Testing Benefits

### What This Enables:
```python
# Clean, resilient test code
def test_school_registration(page):
    # Works in any language
    page.locator('[data-test="select-school-admin"]').click()
    page.locator('[data-test="input-school-name"]').fill("Test School")
    page.locator('[data-test="submit-registration"]').click()

    # Clear assertions
    assert page.locator('[data-test="success-registration"]').is_visible()

    # Easy to get values
    teacher_count = page.locator('[data-test="metric-teacher-count"]')
    assert teacher_count.get_attribute('data-value') == "0"
```

## Best Practices

1. **Add During Development** - Don't wait until testing phase
2. **Review in PRs** - Ensure new features have appropriate data-test attributes
3. **Keep Names Stable** - Changing data-test values breaks tests
4. **Document Special Cases** - If you deviate from patterns, document why
5. **Use TypeScript/Types** - Consider creating types for valid data-test values

## Maintenance Guidelines

### When to Add data-test:
- New user-facing features
- Interactive elements
- Important display values
- Form inputs and buttons
- HTMX targets and triggers

### When to Update data-test:
- Feature significantly changes purpose
- Better naming pattern emerges
- Consolidating duplicate functionality

### When to Remove data-test:
- Feature is being deleted
- Element becomes non-interactive
- Replacing with better testing strategy

## CSS Helper (Development Only)

Add this CSS in development to highlight testable elements:

```css
/* Development only - shows elements with data-test */
[data-test] {
    outline: 1px dashed rgba(255, 0, 255, 0.3);
}

[data-test]:hover::after {
    content: attr(data-test);
    position: absolute;
    background: #ff00ff;
    color: white;
    padding: 2px 5px;
    font-size: 10px;
    z-index: 10000;
}
```

## Questions?

For questions about naming conventions or patterns, consult this document first. If your use case isn't covered, follow the closest pattern and document the exception.
