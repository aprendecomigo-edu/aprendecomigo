# Authentication Session Persistence Investigation
*Investigation Date: August 2, 2025*
*Status: CRITICAL ISSUES IDENTIFIED - IMMEDIATE FIX REQUIRED*

## Executive Summary

**PROBLEM**: Users are experiencing "Acesso Negado" (Access Denied) when navigating to protected routes or refreshing pages, despite having valid authentication tokens. Sessions are not persisting across page navigation/refreshes.

**ROOT CAUSE**: Race conditions in authentication initialization and inconsistent loading state handling across components.

**BUSINESS IMPACT**: 
- Users forced to re-authenticate on every page navigation
- Poor user experience affecting retention
- Potential revenue impact from user abandonment

## Technical Root Cause Analysis

### 1. Race Condition in Auth Initialization
**File**: `/frontend-ui/api/authContext.tsx`
**Issue**: AuthContext initializes with `isLoggedIn: false` and takes time to validate tokens asynchronously. Components make decisions based on initial false state before validation completes.

**Code Path**:
```
Page Load → AuthContext useEffect → checkAuthStatus() → isAuthenticated() → API call
During this time: isLoggedIn = false, isLoading = true
Problem: Components act on isLoggedIn = false before process completes
```

### 2. Premature Redirects in AuthGuard
**File**: `/frontend-ui/components/auth/auth-guard.tsx`
**Issue**: Lines 40-44 immediately redirect to signin when `!isLoggedIn` without waiting for auth initialization.

```typescript
// PROBLEMATIC CODE:
if (!isLoggedIn && !hasRedirectedRef.current) {
  hasRedirectedRef.current = true;
  await logout(); // ❌ CLEARS VALID TOKENS!
  router.replace('/auth/signin');
  return;
}
```

### 3. Inconsistent Loading State Handling
**Files**: 
- `/frontend-ui/app/index.tsx` ✅ (Handles loading correctly)
- `/frontend-ui/app/(school-admin)/_layout.tsx` ❌ (Ignores loading state)
- `/frontend-ui/components/common/AuthGuard.tsx` ❌ (Shows "Access Denied" immediately)

### 4. Multiple AuthGuard Components
**Issue**: Two different AuthGuard implementations causing confusion:
- `/components/auth/auth-guard.tsx` (Main - used in MainLayout)
- `/components/common/AuthGuard.tsx` (Legacy - different behavior)

### 5. Profile vs Auth State Separation
**Issue**: AuthContext separates token validation from profile loading, causing timing mismatches where `isLoggedIn: true` but `userProfile: null`.

## Specific Code Issues Found

### Issue 1: SchoolAdminLayout Premature Redirect
**File**: `/frontend-ui/app/(school-admin)/_layout.tsx:54-56`
```typescript
// ❌ PROBLEMATIC: Doesn't wait for loading to complete
if (!isLoggedIn) {
  return <Redirect href="/auth/signin" />;
}
```

### Issue 2: AuthGuard Clears Valid Tokens
**File**: `/frontend-ui/components/auth/auth-guard.tsx:42`
```typescript
// ❌ PROBLEMATIC: Calls logout() which clears valid tokens
await logout(); // This removes tokens from storage!
```

### Issue 3: Legacy AuthGuard Shows Immediate Denial
**File**: `/frontend-ui/components/common/AuthGuard.tsx:44`
```typescript
// ❌ PROBLEMATIC: Doesn't consider loading state
if (!isLoggedIn || !userProfile) {
  // Shows "Acesso Negado" immediately
}
```

## Recommended Solutions

### IMMEDIATE FIXES (Priority 1 - Deploy Today)

#### Fix 1: Update AuthGuard Loading Logic
**File**: `/frontend-ui/components/auth/auth-guard.tsx`
```typescript
// ✅ FIXED: Wait for loading to complete before redirecting
if (isLoading) {
  return fallback || (/* loading spinner */);
}

// Only redirect after auth check completes
if (!isLoggedIn && !hasRedirectedRef.current) {
  hasRedirectedRef.current = true;
  // ❌ REMOVE: await logout(); // Don't clear valid tokens!
  router.replace('/auth/signin');
  return;
}
```

#### Fix 2: Update SchoolAdminLayout
**File**: `/frontend-ui/app/(school-admin)/_layout.tsx`
```typescript
// ✅ FIXED: Properly handle loading state
if (isLoading || checkingAccess) {
  return (
    <Center className="flex-1">
      <Text>Verificando autenticação...</Text>
    </Center>
  );
}

// Only redirect after loading completes
if (!isLoggedIn) {
  return <Redirect href="/auth/signin" />;
}
```

#### Fix 3: Remove Legacy AuthGuard
**Action**: Delete `/frontend-ui/components/common/AuthGuard.tsx` and update all imports to use the main AuthGuard.

### SECONDARY FIXES (Priority 2 - Deploy This Week)

#### Fix 4: Improve Token Validation
**File**: `/frontend-ui/api/authApi.tsx`
```typescript
// ✅ Add retry logic for network failures
export const isAuthenticated = async (): Promise<boolean> => {
  const token = await getToken();
  if (!token) return false;

  try {
    await apiClient.get('/accounts/users/dashboard_info/');
    return true;
  } catch (error: any) {
    // Don't logout for temporary network issues
    if (error.code === 'ERR_NETWORK') {
      return true; // Assume token is still valid
    }
    
    if (error.response?.status === 401) {
      await removeToken();
      return false;
    }
    
    return true; // For other errors, assume token is valid
  }
};
```

#### Fix 5: Add Auth Recovery Mechanism
**File**: `/frontend-ui/api/authContext.tsx`
```typescript
// ✅ Add recovery for failed initializations
const initializeAuth = async () => {
  try {
    await checkAuthStatus();
  } catch (error) {
    // Retry once after short delay
    setTimeout(() => checkAuthStatus(), 1000);
  }
};
```

## Testing Requirements

### Test Cases to Verify Fixes:
1. **Direct URL Access**: Navigate directly to `/dashboard` - should not show "Acesso Negado"
2. **Page Refresh**: Refresh on protected routes - should maintain session
3. **Network Interruption**: Test with poor connectivity - should not logout prematurely
4. **Multiple Tabs**: Open multiple tabs - auth state should be consistent

### QA Checklist:
- [ ] Login flow works normally
- [ ] Direct navigation to protected routes works
- [ ] Page refresh maintains session
- [ ] No "Acesso Negado" false positives
- [ ] Actual unauthorized access still blocked
- [ ] Loading states show appropriately

## Deployment Strategy

### Phase 1 (Immediate - Today):
1. Deploy Fix 1 & 2 (AuthGuard and Layout loading logic)
2. Test with staging environment
3. Deploy to production during low-traffic hours

### Phase 2 (This Week):
1. Deploy Fix 3 (Remove legacy AuthGuard)
2. Deploy Fix 4 & 5 (Token validation improvements)
3. Monitor error rates and user reports

## Success Metrics

### Expected Improvements:
- 📊 **User Session Duration**: Increase from current broken state to normal levels
- 📊 **Bounce Rate**: Reduce false authentication failures
- 📊 **Support Tickets**: Eliminate "forced to login repeatedly" complaints
- 📊 **User Satisfaction**: Restore seamless navigation experience

### Monitoring Points:
- Authentication error rates
- Failed login attempts due to premature logouts
- Page refresh success rates on protected routes

---

## Notes for Development Team

This is a **critical issue affecting all users**. The fixes are straightforward but must be implemented carefully to avoid breaking existing login flows.

**Communication to users**: Once fixed, consider sending a brief notification that navigation issues have been resolved.

**Future Prevention**: Implement automated tests for authentication persistence across page refreshes and direct navigation scenarios.