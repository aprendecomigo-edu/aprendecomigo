# Session Booking Hour Deduction QA Test Suite

This test suite provides comprehensive quality assurance testing for the Session Booking Hour Deduction feature implemented in **GitHub Issue #32: "Implement Session Booking Hour Deduction"**.

## Feature Overview

The Session Booking Hour Deduction feature integrates the tutoring hour purchase system with session booking functionality. When students book tutoring sessions, hours are automatically deducted from their account balance. The system supports session cancellations with refunds and handles various session types with comprehensive audit logging.

### Key Features Tested
- Automatic hour deduction when booking sessions
- Balance validation before booking confirmation  
- Session cancellation with automatic hour refunds
- Support for individual and group sessions
- Package expiration handling during booking
- Real-time balance updates
- Comprehensive audit logging and security controls

## Test Case Structure

### SESSION-001: Individual Session Booking with Hour Deduction
**Purpose**: Verify that individual tutoring session bookings correctly deduct hours from student account balance with proper financial integration.

**Key Validation Points**:
- Exact 1.0 hour deducted for individual session
- Balance calculation: remaining = purchased - consumed
- Monetary calculation: balance amount reduced proportionally
- Consumption record links to session
- Transaction atomicity (all or nothing)

**Expected Results**: Session booking succeeds and hours are accurately deducted from student balance

### SESSION-002: Group Session Booking with Multiple Students  
**Purpose**: Verify that group tutoring session bookings correctly handle hour deduction for multiple students with proper cost distribution.

**Key Validation Points**:
- Each participant charged full session duration
- No group discounts or shared cost distribution
- All participants must have sufficient balance before booking
- Atomic transaction: all succeed or all fail
- Group session references maintained consistently

**Expected Results**: Group session booking succeeds and hours are accurately deducted from all participating students' balances

### SESSION-003: Balance Validation and Insufficient Funds Handling
**Purpose**: Verify that session booking properly validates student balances and gracefully handles insufficient funds scenarios.

**Key Validation Points**:
- Pre-booking balance checks prevent insufficient fund bookings
- Clear, user-friendly error messages for all failure scenarios
- No sessions or hour consumptions created on validation failure
- Proper handling of edge cases (exact balance, negative balance)
- Transaction atomicity maintained

**Expected Results**: System correctly prevents bookings when insufficient balance and provides clear error messaging

### SESSION-004: Session Cancellation and Hour Refund Process
**Purpose**: Verify that session cancellations correctly refund hours to student account balance with proper audit trails.

**Key Validation Points**:
- Early cancellation (24+ hours): Full refund
- Late cancellation (<24 hours): Partial refund with fee
- Same-day cancellation: No refund
- Teacher cancellation: Full refund to student
- Admin cancellation: Policy override capability

**Expected Results**: Session cancellation succeeds and hours are accurately refunded with complete audit trail

### SESSION-005: Package Expiration and Renewal Integration
**Purpose**: Verify that session booking properly handles hour package expiration scenarios and integrates with package renewal functionality.

**Key Validation Points**:
- Expired packages cannot be used for new bookings
- Active packages with sufficient hours allow booking
- Packages expiring soon provide warnings but allow booking
- Multiple packages handled with correct priority (expiring first)
- Auto-renewal integration with booking process

**Expected Results**: System prevents bookings with expired packages and provides seamless renewal integration

### SESSION-006: Security and Audit Trail Validation
**Purpose**: Verify that session booking hour deduction maintains comprehensive security controls and complete audit trails.

**Key Validation Points**:
- Authentication required for all financial operations
- Authorization properly enforced (students access own data only)
- Cross-school data isolation maintained
- Complete session booking and hour deduction audit trail
- SQL injection and XSS prevention active

**Expected Results**: All session booking operations secure with complete audit trails and proper authorization controls

## Test Data Requirements

### User Accounts
- **Students**: Various balance scenarios (sufficient, low, zero, negative, expired packages)
- **Teachers**: Available for session booking across different time slots
- **Admins**: School-level administrative access for testing admin functions
- **Cross-School Users**: For testing school isolation and security

### Balance Scenarios
- **Sufficient Balance**: 10.00+ hours for successful booking tests
- **Low Balance**: 0.5 hours for insufficient funds testing
- **Zero Balance**: 0.0 hours for validation testing
- **Negative Balance**: -2.0 hours for edge case testing
- **Expired Packages**: Packages with various expiration dates

### Session Types
- **Individual Sessions**: 1.0, 1.5, 2.0 hour durations
- **Group Sessions**: Multiple students, various durations
- **Different Time Slots**: Past, present, future for cancellation testing

## Running the Tests

### Prerequisites
1. **Environment Setup**: 
   - Project root: `/Users/anapmc/Code/aprendecomigo/`
   - Virtual environment activated: `source .venv/bin/activate`
   - Development servers running: `make dev`

2. **Test Data**: 
   - Create test users via Django admin
   - Set up various balance and package scenarios
   - Configure teacher availability

### Execution Steps
1. Navigate to specific test directory: `cd qa-tests/session/session-00X/`
2. Follow detailed step-by-step instructions in `test-case.txt`
3. Execute tests using Playwright browser automation
4. Capture screenshots at designated verification points
5. Document results in timestamped run directory

### Expected Artifacts
- **Screenshots**: Visual verification of each test step
- **Server Logs**: Backend API calls and responses
- **Results Documentation**: Comprehensive pass/fail analysis
- **CSV Updates**: Test run tracking and status

## Pass/Fail Criteria

### Overall PASS Requirements
- **ALL individual test cases must PASS**
- **Session booking functionality works correctly**
- **Hour deduction accurate for all scenarios**
- **Balance validation prevents inappropriate bookings**
- **Cancellation and refund processes functional**
- **Security controls and audit trails complete**

### Overall FAIL Conditions
- **ANY individual test case FAILS**
- **Session booking fails or hours not deducted**
- **Balance validation bypassed**
- **Cancellation/refund processes broken**
- **Security vulnerabilities identified**
- **Audit trail incomplete or inconsistent**

## Integration Points

### Classroom-Finances App Integration
- **Session Creation**: Scheduler app creates sessions
- **Hour Deduction**: Finances app processes hour consumption
- **Balance Updates**: Real-time balance calculation updates
- **Audit Logging**: Cross-app audit trail maintenance

### Security Integration
- **Authentication**: JWT token validation across all endpoints
- **Authorization**: Role-based access control enforcement
- **Data Isolation**: School-level data separation
- **Audit Trail**: Comprehensive logging for compliance

## Business Logic Validation

### Financial Calculations
- **Hour Deduction**: Exact session duration deducted
- **Balance Updates**: remaining_hours = purchased_hours - consumed_hours
- **Monetary Calculations**: Balance amount proportionally reduced
- **Refund Calculations**: Based on cancellation timing and policies

### Session Management
- **Individual Sessions**: One student, full duration charge
- **Group Sessions**: Multiple students, each pays full duration
- **Cancellation Policies**: Time-based refund percentages
- **Package Management**: Expiration handling and renewal integration

## Performance Requirements

### Response Time Standards
- **Session Booking**: < 2000ms for individual sessions
- **Group Booking**: < 3000ms for multiple students
- **Balance Validation**: < 1000ms for balance checks
- **Cancellation Processing**: < 3000ms for refunds

### Concurrency Requirements
- **Race Condition Prevention**: Proper locking for financial operations
- **Concurrent Booking**: No double-booking of time slots
- **Balance Updates**: Atomic transaction processing
- **Audit Trail**: Consistent logging under load

## Monitoring and Alerting

### Key Metrics
- **Session Booking Success Rate**: Target > 95%
- **Hour Deduction Accuracy**: Target 100%
- **Balance Validation Effectiveness**: Target 100%
- **Security Event Detection**: Real-time monitoring

### Alert Conditions
- **Failed Financial Transactions**: Immediate investigation
- **Balance Calculation Errors**: Critical alert
- **Security Breach Attempts**: High-priority alert
- **Performance Degradation**: Warning threshold monitoring

## Compliance and Audit

### Regulatory Requirements
- **Financial Transaction Logging**: Complete audit trail
- **Data Privacy**: Student financial data protection
- **Cross-Border Data**: School isolation compliance
- **Retention Policies**: Audit log retention standards

### Audit Trail Requirements
- **Session Booking Events**: User, timestamp, details
- **Hour Deduction Records**: Amount, session reference, timestamp
- **Balance Updates**: Before/after states, calculation details
- **Security Events**: Authentication, authorization, access attempts

This comprehensive test suite ensures the Session Booking Hour Deduction feature meets all functional, security, performance, and compliance requirements while providing a robust foundation for ongoing quality assurance.