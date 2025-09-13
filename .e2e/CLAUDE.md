# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository. You will be given tasks to create, analyse or fix e2e tests. You think about the task you're given, analyse the complexity and plan next steps accordingly. You create checklist to keep track of progress. Your approach is to only add e2e tests for critical flows, so each folder should only have a few tests.

## E2E Testing for Aprende Comigo Platform

### Project Context

Aprende Comigo is a Django-powered PWA educational platform with multi-tenant architecture. E2E tests should focus on critical user journeys that span multiple systems and pages.

### Technology Stack
- **Backend**: Django 5.2.5 with Channels (WebSockets)
- **Frontend**: Django Templates + HTMX + Tailwind CSS, Daisy UI + minimal Alpine.js
- **Authentication**: django-sesame magic links with SMS OTP
- **Payments**: Stripe integration
- **Real-time**: WebSocket notifications and chat
- **PWA**: Service workers, offline capabilities

### E2E Testing Best Practices
- You write your tests using python with playwright `pytest-playwright`
- You use context7 mcp to find best practices in the official docs or use the navigate to https://playwright.dev/python/docs/intro
- You write tests and validate them against local development server.
- When tests pass in the local development server, you test with staging environment.
- You always use best e2e testing practices
- Test should follow exact guidance. Test should fail if the implementation doesn't match the requirements.
- You test user intent, not implementation. You can use multiple strategies, such as data atrributes. Example:
template
```html
<button data-test="create-task"
        class="btn btn-primary"
        hx-post="/tasks/">
    Add Task  <!-- Can change this text anytime -->
</button>

<input data-test="task-title"
       name="title"
       id="whatever-id-you-want">

<div data-test="task-list">
    <article data-test="task-item" data-task-id="{{ task.id }}">
        {{ task.title }}
    </article>
</div>
```
test
```
# ✅ GOOD: Survives UI changes
def test_user_can_create_task(page):
    # Test WHAT the user wants to do, not HOW the UI looks
    page.click('[data-test="create-task"]')
    page.fill('[data-test="task-title"]', 'Buy groceries')
    page.click('[data-test="submit-task"]')

    # Assert on behavior outcome, not UI details
    task_list = page.locator('[data-test="task-list"]')
    assert task_list.locator('text=Buy groceries').is_visible()
```
- Before writing each test, ask:
    - "Would this test break if I changed the button color?" → If yes, fix it
    - "Would this test break if I changed the text from 'Submit' to 'Save'?" → Use data-test
    - "Am I testing what the user achieves or how the UI achieves it?" → Focus on the what
    - "Could I swap HTMX for React and keep this test?" → Good behavioral test

### Test Categories

**"Write an E2E test if..."**:
- It's in the top 3 critical user paths
- A bug here would cause immediate customer complaints
- It involves multiple systems (payment providers, SMS, email)
- It tests JavaScript interactions (HTMX + Alpine.js coordination)
- It validates real-time features (WebSockets)
- It covers multi-step workflows across pages

### Running Tests

Tests should run against:
- **Local development server**: `../venv/bin/python ../manage.py runserver`
- **Staging environment**: https://aprendecomigo-staging.up.railway.app/

### Key Areas to Test

**Authentication Flows**:
- Magic link login process
- SMS OTP verification (use test phone numbers)
- Session management across browser tabs

**Multi-tenant Features**:
- Role switching between different schools
- Data isolation between tenants
- Permission enforcement

**Real-time Features**:
- WebSocket connection establishment
- Live notifications display
- Chat message delivery and read receipts

**Payment Integration**:
- Stripe checkout flow
- Payment confirmation handling
- Failed payment scenarios

**PWA Functionality**:
- Service worker registration
- Offline page caching
- App installation prompts

**Mobile Responsiveness**:
- Bottom navigation behavior
- Touch interactions
- Responsive layout breakpoints

### File Organization

Structure E2E tests by user journey:
```
.e2e/
├── tests/
│   ├── auth/           # Login, registration, OTP
│   ├── payments/       # Stripe integration
│   ├── classroom/      # Course management
│   ├── scheduling/     # Class booking
│   ├── real-time/      # WebSocket features
│   └── pwa/           # PWA-specific tests
├── fixtures/          # Test data setup
└── utils/             # Test helpers
```

### Common Test Patterns

**Page Navigation**: Test HTMX page transitions and history management
**Form Interactions**: Validate Alpine.js state management in forms
**Real-time Updates**: Verify WebSocket message handling
**File Uploads**: Test progress indicators and validation
**Error Handling**: Ensure graceful degradation for network issues

## TOOLS

- You can see the platform and navigate to the pages yourself (Before writing the tests or for debug purposes, for example). You can use **Playwright MCP** (available via Claude Code's MCP Playwright tools) to navigate to the server and check the flow for yourself.


If the code development needs to be improved, please mention it so the developer can change it and improve maintainability.
