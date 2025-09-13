# Branch Protection Setup

To ensure that pushes and merges to `main` and `staging` branches only succeed when all tests pass, you need to configure branch protection rules in GitHub.

## Required GitHub Repository Settings

### 1. Navigate to Branch Protection Rules
1. Go to your repository on GitHub
2. Click **Settings** → **Branches**
3. Click **Add rule** for each protected branch

### 2. Configure Protection for `main` Branch

**Branch name pattern:** `main`

**Required settings:**
- ✅ **Require a pull request before merging**
  - ✅ **Require approvals:** 1
  - ✅ **Dismiss stale PR approvals when new commits are pushed**
- ✅ **Require status checks to pass before merging**
  - ✅ **Require branches to be up to date before merging**
  - **Required status checks:** `Pre-Deploy Tests`
- ✅ **Require conversation resolution before merging**
- ✅ **Restrict pushes that create files**
- ✅ **Do not allow bypassing the above settings**

### 3. Configure Protection for `staging` Branch

**Branch name pattern:** `staging`

**Required settings:**
- ✅ **Require status checks to pass before merging**
  - ✅ **Require branches to be up to date before merging**
  - **Required status checks:** `Pre-Deploy Tests`
- ✅ **Restrict pushes that create files**
- ✅ **Do not allow bypassing the above settings**

## How It Works

1. **Direct Pushes**: Blocked to both `main` and `staging` unless tests pass
2. **Pull Requests**: Must have passing tests before merge is allowed
3. **Status Checks**: The workflow `Pre-Deploy Tests` job must complete successfully
4. **Up-to-date Requirement**: Branches must be current with target branch

## Workflow Details

The `deploy.yml` workflow will:
- Run on pushes to `main` and `staging` branches (triggering Railway deployments)
- Run on pull requests targeting `main` and `staging`
- Execute Django tests, linting, and formatting checks
- Block merge/deployment if any step fails

## Emergency Override

Repository administrators can temporarily disable protection rules if needed, but this should be documented and re-enabled immediately after emergency fixes.
