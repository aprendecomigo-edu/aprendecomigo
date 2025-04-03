# Google Calendar Integration - AprendeComigo

This document describes the expected format for Google Calendar events to be properly parsed by the AprendeComigo system.

## Authentication

The system uses Google OAuth2 authentication through django-allauth. Administrators must:
1. Connect their Google account through the social login feature
2. Use their email when running the sync command

## Event Format

Google Calendar events must follow this format to be correctly imported into the system:

### Title
The title should contain the student's full name. If the student was absent, append " - FALTOU" at the end of the name.

Example:
- `João Silva` (student attended)
- `Maria Santos - FALTOU` (student was absent)

### Location
The location field should contain the teacher's name, optionally prefixed with "Prof.".

Example:
- `Prof. Carlos Mendes`
- `Ana Pereira`

### Description
The description field should contain the class type code which determines the hourly rate for the class. This is a code defined in the system that corresponds to a specific class type and pricing.

Example:
- `MATH101`
- `CHEMISTRY_ADV`
- `PRIVATE_ENGLISH`

### Date and Time
Standard Google Calendar date and time fields are used to determine the class schedule.

## Example Event
```
Title: Tom Steadman
Date: Tuesday, April 8
Time: 09:00 — 10:00
Location: Prof. Carla Almeida
Description: Explicação_Uni
```

## Calendar ID
The system is configured to use the following specific calendar by default:
```
python manage.py sync_calendar --admin-email admin@example.com --days 10
```

You can specify the number of days to fetch events for, or use a date range:

```
python manage.py sync_calendar --admin-email admin@example.com --start-date 2023-06-01 --end-date 2023-06-30
```

This will create or update class sessions in the database, and create placeholder user accounts for any students or teachers who don't already exist in the system.
