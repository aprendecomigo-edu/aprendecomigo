You task is to work with the product-strategist agent to generate detailed and appropriate user stories from a product perspective, and then save these stories as GitHub issues. Your primary focus is on creating well-documented and detailed user stories that will serve as a foundation for the development team's technical implementation planning. You will be working based on a report.

<report_info>
$ARGUMENTS
</report_info>

These are the flow markdown files you will analyze to identify user stories and features.

Process overview:
1. Ask the product-strategist to analyze report, to identify well-defined, standalone user stories and features.
2. Create detailed user stories from a product perspective
3. Save each user story as a GitHub issue using the 'gh' command

Follow these detailed instructions for each step:

1. Ask the product-strategist agent to follow these steps:
   - Review each report carefully
   - Identify potential user stories and features within the report
   - Make note of any important details or requirements
   - Consider prioritization and additional details
   - Ensure alignment on the scope and importance of each user story

2. Then rom the information the product-strategist created, create user stories:
   - Write each user story with enough detail from the product perspective
   - Include the following components in each user story:
     a. Title: A concise description of the feature or functionality
     b. User persona: Who will benefit from this feature?
     c. Goal: What does the user want to accomplish?
     d. Context: In what situation or environment will this be used?
     e. Acceptance criteria: What conditions must be met for this to be considered complete?
     f. Additional notes: Any other relevant information, constraints, or considerations

3. Saving user stories as GitHub issues:
   - Use the 'gh' command to create a new issue for each user story
   - Format the command as follows:
     <gh_command>gh issue create --title "User Story: [Title]" --body "[Full user story content]" --label "user-story"</gh_command>
   - Ensure that the user story content is properly formatted and easy to read

Guidelines for user story content:
- Focus on the product perspective, not technical implementation
- Provide enough detail for developers to understand the requirements
- Use clear, concise language
- Avoid technical jargon unless necessary for understanding
- Include any relevant business rules or constraints

Reminders and best practices:
- Do not discuss development plans or technical implementation details
- Add appropriate tags such as "user-story" to each GitHub issue
- Ensure each user story is well-defined and standalone
- Consider the needs of both frontend and backend developers
- If a user story is too large, consider breaking it down into smaller, manageable stories
- You can use your sequential-thinking mcp.