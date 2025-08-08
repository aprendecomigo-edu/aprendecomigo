Issue gh $ARGUMENTS addresses fixing issues in frontend test setup, configuration and coverage. Keep in mind that more tests isn't always better if the tests are bad quality, so always follow good practices.

- Get the issue gh $ARGUMENTS. Read the issue body, comments or related sub-issues.
- The react-native-test-engineer should work on the issue, implement the tests or fix setup.
- You should then run the tests and check for any errors/failures and run the quality checks below.

## Quality Checks
Before considering tests complete, you verify:
1. Tests fail when the implementation is broken
2. Tests pass when implementation is correct
3. Tests survive refactoring that preserves behavior
4. Failure messages clearly indicate what went wrong
5. No test takes longer than 100ms
6. Coverage includes happy path, edge cases, and error conditions

- If anything fails, you verify if the test needs fixing or if it's a buggy code. Fix. 

Your task is done when the new tests pass and errors are fixed. Plan carefully and think sequentially. Our goal is a maintanable, clean and concise test folder. When you're done, commit your changes and leave a comment on the gh issue.