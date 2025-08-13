Can you please ask the drf engineer and py-unitest engineers to review the tests in `$ARGUMENTS` app. We only want to keep good tests and make sure they follow the principle of serve as the documentation for the functionality in `$ARGUMENTS` app. Keep in mind that more tests isn't always better if the tests are bad quality.

- Each agent should do a review of the tests related to their expertise (Business logic for py-unitest and urls/views/serializers for drf test agent) and delete or modify bad tests and keep or improve the good ones. Give enough info and context to the agents.
- You should then run the tests with (make sure venv is on) `python manage.py test `$ARGUMENTS`` and check for any errors/failures.
- Coordinate with the test agents and django-dev agent to fix any errors and failures found in the step before.
- You verify ALL tests in `$ARGUMENTS` app pass without errors or failures. Otherwise, keep iterating with the help of specialised test agents.

The goal is to fix all the tests (or buggy code) with high quality. Your task is done when the refactor is complete and all tests within `$ARGUMENTS` app pass. DO NOT STOP WORKING UNTIL ALL TESTS PASS.
After all is done, commit your changes.

Plan carefully, think sequentially and keep a todo list to keep progress and track your goal. Our goal is a maintanable, clean and concise test folder.

