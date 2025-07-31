Your task is to build a UX analysis of the aprendecomigo platform based on a specific use case. Your role is to instruct the ux-interface-designer subagent to perform this analysis. Use sequential-thinking tool to help you follow these instructions carefully:

1. First, you read and understand the following use case:

<use_case>
$ARGUMENTS
</use_case>

2. Then, you setup the development environment `make dev` should work, otherwise fix any issues so it is ready. 

3. Now, let the ux-interface-designer subagent know how to visit the frontend and instruct them to perform the following steps:

a. Analyze the use case in detail:
   - Examine all aspects of the user journey described in the use case.
   - Consider the user's goals, actions, and potential pain points.
   - Think about the platform's functionality and how it relates to the use case.

b. Identify problems and opportunities:
   - List up to 10 issues that need fixing or areas for improvement.
   - Categorize each item as critical, medium, or improvement.
   - Ensure the list is comprehensive and covers various aspects of the user experience.

c. Write a UX report:
   - Create a markdown file named "UX_Report_{use_case}.md" (replace {use_case} with a short, descriptive name).
   - Include the following sections in the report:
     1. Executive Summary
     2. Use Case Analysis
     3. Identified Issues and Opportunities (categorized)
     4. Detailed Findings
     5. Recommendations
     6. Conclusion
   - Incorporate any relevant visual elements or media to support the findings.
   - Ensure the report is professional, well-structured, and easy to read.

4. Important notes for the ux-interface-designer subagent:
   - Conduct this analysis on the development/local environment of the aprendecomigo platform. Use `make dev`
   - Be thorough and objective in your analysis.
   - Support your findings with specific examples from the use case.
   - Prioritize issues that have the most significant impact on user experience.

5. Output format:
   Instruct the ux-interface-designer subagent to present their work in the following format, including any images or visuals necessary:

<ux_analysis>
<use_case_analysis>
[Detailed analysis of the use case]
</use_case_analysis>

<issues_and_opportunities>
Critical:
1. [Issue/Opportunity]
2. [Issue/Opportunity]
...

Medium:
1. [Issue/Opportunity]
2. [Issue/Opportunity]
...

Improvements:
1. [Issue/Opportunity]
2. [Issue/Opportunity]
...
</issues_and_opportunities>

<ux_report>
[Content of the UX_Report_{use_case}.md file]
</ux_report>
</ux_analysis>

Ensure that the ux-interface-designer subagent follows these instructions carefully and produces a comprehensive UX analysis of the aprendecomigo platform based on the provided use case.