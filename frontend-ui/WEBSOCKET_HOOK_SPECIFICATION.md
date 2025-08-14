# WebSocket Hook Test Failures Analysis & Specification

This document analyzes the 14 failing WebSocket hook tests and specifies the expected behavior that needs to be implemented to make them pass.

## Current Test Status
- ✅ 11 tests passing
- ❌ 14 tests failing
- Total: 25 tests

## Failing Tests Analysis

### 1. Connection Management

#### ❌ `should cleanup connection on unmount`
**Expected Behavior:**
- When component unmounts, WebSocket should be in `CLOSING` state
- Connection should be properly closed to prevent memory leaks

**Current Issue:**
- Test expects `ws.readyState === WebSocket.CLOSING` after unmount
- Hook's disconnect() method calls `ws.close()` but test checks state immediately
- MockWebSocket sets readyState to CLOSING synchronously, then CLOSED after timeout

**Fix Required:**
- Ensure cleanup sets WebSocket to CLOSING state immediately
- Verify timing of state changes in disconnect method

### 2. Message Handling

#### ❌ `should receive and parse JSON messages`
**Expected Behavior:**
- When `ws.simulateMessage()` sends JSON string, hook should parse it and call `onMessage` callback
- Parsed object should be passed to the callback, not the JSON string

**Current Issue:**
- `onMessage` callback not being called when mock WebSocket simulates message
- Hook's `onmessage` handler may not be properly connected to mock events

**Fix Required:**
- Ensure hook's WebSocket `onmessage` handler is triggered by mock's `simulateMessage()`
- Verify JSON parsing and callback invocation

#### ❌ `should handle malformed JSON messages gracefully`
**Expected Behavior:**
- Malformed JSON should not crash the application
- Should log error to console with format: `'Error parsing WebSocket message:', Error`
- `onMessage` callback should NOT be called for malformed JSON

**Current Issue:**
- Console.error not being called with expected format
- May be error handling issue in JSON parsing

**Fix Required:**
- Implement proper try-catch around JSON.parse
- Call console.error with exact expected format
- Ensure onMessage is not called for parsing errors

#### ❌ `should send messages successfully when connected`
**Expected Behavior:**
- When `sendMessage()` is called, message should be added to mock's message queue
- Mock's `getMessageQueue()` should contain the sent message as JSON string

**Current Issue:**
- Messages not appearing in mock WebSocket's message queue
- May be issue with how mock WebSocket's `send()` method works

**Fix Required:**
- Ensure hook calls mock WebSocket's `send()` method
- Verify mock's `getMessageQueue()` contains sent messages
- Check message serialization format

### 3. Reconnection Logic

#### ❌ `should implement exponential backoff reconnection`
**Expected Behavior:**
- Reconnection delays should follow exponential backoff: 1s, 2s, 4s, 8s, etc.
- Should track timing between reconnection attempts
- Verify backoff timing with tolerance for test execution delays

**Current Issue:**
- `WebSocketTestUtils.verifyBackoffTiming` function doesn't exist
- Missing utility to validate exponential backoff timing

**Fix Required:**
- Implement `verifyBackoffTiming` utility function
- Function should accept: (attempts: number[], baseDelay: number, tolerance: number) => boolean
- Verify each attempt follows exponential pattern within tolerance

#### ❌ `should stop reconnecting after max attempts`
**Expected Behavior:**
- After max reconnection attempts (5), should stop creating new WebSocket instances
- Total WebSocket instances should not exceed initial + max attempts

**Current Issue:**
- May be continuing to reconnect beyond max attempts
- Instance counting may be incorrect

**Fix Required:**
- Ensure reconnection stops after maxReconnectAttempts
- Verify WebSocket instance tracking in mock

#### ❌ `should not reconnect on normal closure (code 1000)`
**Expected Behavior:**
- When WebSocket closes with code 1000 (normal closure), no reconnection should occur
- Should remain disconnected permanently

**Current Issue:**
- May be attempting to reconnect even for normal closures
- Should check close event code before reconnecting

**Fix Required:**
- Verify hook checks `event.code !== 1000` before reconnecting
- Ensure no new WebSocket instances created after normal closure

### 4. Error Handling

#### ❌ `should call onError callback on WebSocket errors`
**Expected Behavior:**
- When `ws.simulateError()` is called, hook's `onError` callback should be invoked
- Error event object should be passed to callback

**Current Issue:**
- `onError` callback not being called
- Hook's WebSocket `onerror` handler may not be properly connected

**Fix Required:**
- Ensure hook's WebSocket `onerror` handler calls the provided `onError` callback
- Verify mock's `simulateError()` triggers the handler

#### ❌ `should handle network interruption and recovery`
**Expected Behavior:**
- Network failure should trigger `onClose` and `onError` callbacks once each
- Successful reconnection should trigger `onOpen` callback again (total 2 times)
- Should track callback invocation counts correctly

**Current Issue:**
- Callback invocation counts don't match expectations
- May be timing issues with simulated network failure/recovery

**Fix Required:**
- Ensure proper callback sequencing during network failure
- Verify reconnection triggers `onOpen` callback again

### 5. Manual Connection Control

#### ❌ `should allow manual connection`
**Expected Behavior:**
- When `shouldConnect` is false, calling `connect()` manually should establish connection
- Should transition from disconnected to connected state

**Current Issue:**
- Manual `connect()` method may not be working properly
- State may not update correctly

**Fix Required:**
- Ensure manual `connect()` method works independently of `shouldConnect` prop
- Verify state updates after manual connection

#### ❌ `should allow manual disconnection`
**Expected Behavior:**
- Calling `disconnect()` on connected WebSocket should close connection
- Should transition from connected to disconnected state

**Current Issue:**
- Manual `disconnect()` method may not update state immediately
- State tracking issue

**Fix Required:**
- Ensure manual `disconnect()` method updates state synchronously
- Verify connection cleanup

### 6. Enhanced WebSocket Interface

#### ❌ `should support sending both string and object messages`
**Expected Behavior:**
- String messages should be sent as-is
- Object messages should be JSON.stringify'd
- Both should appear in mock's message queue

**Current Issue:**
- Message serialization may not be working correctly
- Mock queue format mismatch

**Fix Required:**
- Implement proper message type detection and serialization
- Ensure both string and object messages work correctly

### 7. Performance Tests

#### ❌ `should complete connection within 100ms`
**Expected Behavior:**
- WebSocket connection should be established quickly
- End-to-end connection time should be under 100ms

**Current Issue:**
- Connection timing may be too slow
- May be related to fake timers or async operations

**Fix Required:**
- Optimize connection timing
- Verify fake timer usage in tests

#### ❌ `should handle rapid message sending without blocking`
**Expected Behavior:**
- Sending 100 messages rapidly should complete quickly (< 100ms)
- All 100 messages should appear in mock's queue
- Should not block the main thread

**Current Issue:**
- Message sending performance is slow
- Shows "WebSocket not connected" warnings, indicating connection issues

**Fix Required:**
- Ensure connection is established before rapid message test
- Optimize message sending performance

## Missing Test Utilities

### `WebSocketTestUtils.verifyBackoffTiming`
**Required Implementation:**
```typescript
verifyBackoffTiming: (attempts: number[], baseDelay: number, tolerance: number): boolean => {
  for (let i = 0; i < attempts.length; i++) {
    const expectedDelay = Math.pow(2, i) * baseDelay;
    const actualDelay = attempts[i];
    const withinTolerance = Math.abs(actualDelay - expectedDelay) <= tolerance;
    if (!withinTolerance) return false;
  }
  return true;
}
```

### Mock WebSocket Integration Issues
**Current Issue:**
- MockWebSocket's `getMessageQueue()` returns `Array<{ data: any; timestamp: number }>`
- Tests expect string array of message contents
- Need adapter method or fix queue format

**Fix Required:**
```typescript
// In tests, extract just the data:
const sentMessages = ws.getMessageQueue().map(msg => msg.data);
```

## Implementation Priorities

### High Priority (Blocking Basic Functionality)
1. Fix message handling (receive/send messages)
2. Fix connection cleanup on unmount
3. Fix manual connect/disconnect methods
4. Add missing `verifyBackoffTiming` utility

### Medium Priority (Reconnection Logic)
5. Fix exponential backoff reconnection
6. Fix max reconnection attempts limit  
7. Fix normal closure (no reconnection)

### Low Priority (Error Handling & Performance)
8. Fix error callback invocation
9. Fix network interruption handling
10. Fix enhanced interface message types
11. Fix performance tests

## Test Infrastructure Requirements

### MockWebSocket Enhancements Needed
- Ensure proper event handler triggering
- Fix message queue format consistency
- Improve timing control for tests

### WebSocketTestUtils Missing Functions
- `verifyBackoffTiming` implementation
- Better integration with fake timers
- Message queue format adapters

## Expected Hook Interface

The tests expect the useWebSocket hook to provide:

```typescript
interface UseWebSocketResult {
  isConnected: boolean;
  error: string | null;
  sendMessage: (message: any) => void;  // Should accept any type, not just WebSocketMessage
  connect: () => void;
  disconnect: () => void;
}

interface UseWebSocketEnhancedResult {
  isConnected: boolean;
  lastMessage: string | null;
  sendMessage: (message: any) => void;
  connect: () => void;
  disconnect: () => void;
}
```

## Success Criteria

All tests should pass when:
1. Connection lifecycle works properly (establish, maintain, cleanup)
2. Message handling works bidirectionally with proper error handling
3. Reconnection logic implements exponential backoff with limits
4. Error callbacks are triggered appropriately
5. Manual controls work independently
6. Performance requirements are met
7. All test utilities are implemented

The hooks should provide robust, production-ready WebSocket functionality that handles real-world scenarios like network interruptions, authentication, and performance requirements.