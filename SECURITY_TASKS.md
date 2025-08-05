# Security Fix Tasks

This document lists actionable tasks to address the highest priority vulnerabilities identified in the security audit.

## 4. Sensitive Data Stored Unencrypted
- [ ] Introduce field-level encryption for personal data such as `cc_number`, `cc_photo`, and address fields.
- [ ] Choose a library like `django-fernet-fields` or `django-encrypted-model-fields` and add it to `requirements.txt`.
- [ ] Update the affected models (student and teacher profiles) to use encrypted field types.
- [ ] Create and apply database migrations to migrate existing values.
- [ ] Add an environment variable for the encryption key and document it in `env.example`.

## 5. Potential XSS from Stored iframe Content
- [ ] Sanitize the `calendar_iframe` value before saving or serving it through the API.
- [ ] Use a library such as `bleach` to whitelist allowed tags and attributes.
- [ ] Add unit tests to confirm that malicious scripts are removed.

## 6. Lack of File Size Checks on Uploads
- [x] Implement a custom validator on `ChatMessage` attachments to enforce a reasonable file size limit (e.g., 5 MB).
- [x] Apply the validator in `backend/classroom/models.py` alongside the existing `FileExtensionValidator`.
- [x] Write tests to ensure oversized files are rejected with a clear error message.

