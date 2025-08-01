# Purchase API QA Tests

This directory contains comprehensive QA test cases for the Purchase Initiation API implemented in GitHub Issue #30: "Create Purchase Initiation API".

## Feature Overview

The Purchase Initiation API allows students to start the process of purchasing tutoring hours through various pricing plans. The API integrates with Stripe for payment processing and creates preliminary transaction records.

### API Details
- **Endpoint**: `POST /finances/api/purchase/initiate/`
- **Authentication**: Supports both authenticated users and guest purchases
- **Payment Plans**: Handles package and subscription plan types
- **Payment Integration**: Creates Stripe payment intents
- **Response**: Returns client secrets for frontend payment completion

## Test Categories

### PURCHASE-001: Authenticated User Purchase Flow
- Tests normal purchase flow for logged-in users
- Verifies API request/response structure
- Tests payment intent creation
- Validates database transaction creation

### PURCHASE-002: Guest User Purchase and Registration
- Tests guest user purchase functionality
- Verifies automatic user creation for guest purchases
- Tests email validation and user matching logic
- Validates guest-to-registered user flow

### PURCHASE-003: Validation and Error Handling
- Tests input validation across all fields
- Verifies error message format and clarity
- Tests edge cases and boundary conditions
- Validates security against malicious inputs

### PURCHASE-004: Stripe Integration and Payment Processing
- Tests Stripe payment intent creation
- Verifies payment metadata handling
- Tests payment amount calculations
- Validates currency and pricing plan integration

### PURCHASE-005: Security and Input Sanitization
- Tests protection against injection attacks
- Verifies input sanitization
- Tests rate limiting and abuse prevention
- Validates authentication and authorization

### PURCHASE-006: Performance and Load Testing
- Tests API response times under normal load
- Verifies behavior under stress conditions
- Tests concurrent request handling
- Validates database performance impact

## Running Tests

Each test case includes detailed step-by-step instructions for:
1. Environment setup and prerequisites
2. Test data preparation
3. API request execution
4. Response validation
5. Database state verification
6. Screenshot documentation

## Test Environment

- **Backend**: Django REST Framework on http://localhost:8000
- **Database**: PostgreSQL for production, SQLite for testing
- **Stripe**: Test mode with mock payment intents
- **Authentication**: JWT tokens for authenticated tests
- **Frontend Integration**: Verify API responses are frontend-compatible

## Success Criteria

All tests must achieve PASS status for the Purchase Initiation API to be considered production-ready. Any FAIL result indicates issues that must be resolved before deployment.