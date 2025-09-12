# Internationalization Guide for Aprende Comigo

## Overview
This guide covers the complete internationalization (i18n) system for Aprende Comigo, supporting Portuguese (Portugal) and English (UK).

## Language Strategy

### Source Language: English (UK)
- **All msgid strings are in English (UK)**
- Follows Django best practices
- Makes codebase internationally maintainable
- Allows easy addition of new languages

### Configuration
```python
# settings/base.py
LANGUAGE_CODE = "en-gb"  # Default/fallback language

LANGUAGES = [
    ("en-gb", "English (UK)"),           # Source language
    ("pt-pt", "Português (Portugal)"),   # Primary translation
]
```

### Key Principle
- **English in source code** → **Portuguese in .po files**
- English users see msgid directly (no translation needed)
- Portuguese users see msgstr translations

## For Developers

### Quick Commands
```bash
# Check for untranslated strings
python manage.py mark_translations --check

# Generate/update translation files
python manage.py makemessages -l pt_PT --no-location

# Compile translations
python manage.py compilemessages
```

### Marking Strings for Translation

#### Python Code
```python
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _lazy

# Views and functions - use gettext
messages.success(request, _("Your profile has been updated!"))

# Models - use gettext_lazy (evaluated at startup)
class School(models.Model):
    name = models.CharField(_lazy("School Name"), max_length=100)

# Pluralization
from django.utils.translation import ngettext
message = ngettext(
    "%(count)d student enrolled",
    "%(count)d students enrolled",
    student_count
) % {"count": student_count}

# Context-specific translations
from django.utils.translation import pgettext
button_text = pgettext("button", "Save")  # Context: button
title_text = pgettext("title", "Save")    # Context: title

# Translator comments
# Translators: This message appears after successful login
messages.success(request, _("Welcome back!"))
```

#### Templates
```django
{% load i18n %}

<!-- Simple translation -->
<h1>{% trans "Welcome to Aprende Comigo" %}</h1>

<!-- With variables -->
{% blocktrans with name=user.first_name %}
Welcome back, {{ name }}!
{% endblocktrans %}

<!-- Pluralization -->
{% blocktrans count counter=students.count %}
{{ counter }} student
{% plural %}
{{ counter }} students
{% endblocktrans %}

<!-- Translation with context -->
{% trans "Save" context "button" %}

<!-- Translator comments -->
{# Translators: Page title for dashboard #}
{% trans "Dashboard" %}
```

### Common Mistakes to Avoid

❌ **Don't**: Write Portuguese in source code
```python
messages.error(request, "Erro ao guardar")  # Wrong!
```

✅ **Do**: Write English in source code
```python
messages.error(request, _("Error saving"))  # Correct!
```

❌ **Don't**: Mix languages in templates
```html
<button>Guardar</button>  <!-- Wrong! -->
```

✅ **Do**: Use translation tags
```html
<button>{% trans "Save" %}</button>  <!-- Correct! -->
```

### Language Detection Order
Django determines user's language:
1. User's saved preference (cookie)
2. Browser's Accept-Language header
3. Default LANGUAGE_CODE (en-gb)

## For Translators

### Files to Work With
- **Portuguese**: `locale/pt_PT/LC_MESSAGES/django.po`
- **English**: Not needed - English is the source language

### Setup Instructions
1. Download [Poedit](https://poedit.net/) (free, recommended)
2. Open `django.po` file in Poedit
3. Translate strings from `msgid` (English) to `msgstr` (Portuguese)
4. Save frequently

### Translation Rules

#### 1. Keep Variables Unchanged
```
msgid "Hello, %(name)s!"
msgstr "Olá, %(name)s!"     ✅ Correct
msgstr "Olá, %(nome)s!"     ❌ Wrong - variable name changed
```

#### 2. Preserve HTML Tags
```
msgid "Click <strong>here</strong>"
msgstr "Clique <strong>aqui</strong>"  ✅ Keep tags
```

#### 3. Handle Context
```
msgctxt "button"
msgid "Save"
msgstr "Guardar"  (save a file)

msgctxt "finance" 
msgid "Save"
msgstr "Poupar"   (save money)
```

#### 4. Plural Forms
Portuguese has 2 plural forms:
```
msgid "%(count)d student"
msgid_plural "%(count)d students"
msgstr[0] "%(count)d aluno"     # singular
msgstr[1] "%(count)d alunos"    # plural
```

### Educational Terms Dictionary

| English | Portuguese (PT) |
|---------|-----------------|
| Student | Aluno/Aluna |
| Teacher | Professor/Professora |
| Guardian | Encarregado de Educação |
| School | Escola |
| Class | Aula |
| Course | Curso |
| Schedule | Horário |
| Dashboard | Painel |
| Profile | Perfil |
| Settings | Definições |

### Common UI Elements

| English | Portuguese (PT) |
|---------|-----------------|
| Save | Guardar |
| Cancel | Cancelar |
| Delete | Eliminar |
| Edit | Editar |
| Add | Adicionar |
| Search | Pesquisar |
| Loading... | A carregar... |
| Success | Sucesso |
| Error | Erro |
| Warning | Aviso |

### Error Messages

| English | Portuguese (PT) |
|---------|-----------------|
| Required field | Campo obrigatório |
| Invalid email | Email inválido |
| Please try again | Por favor tente novamente |
| Something went wrong | Algo correu mal |
| Access denied | Acesso negado |

### Handling msgid Changes

Sometimes developers change the original English text:

#### 1. Look for Obsolete Entries
You'll see old entries marked with `#~`:
```
# New entry (needs translation)
msgid "Welcome to the Aprende Comigo Platform"
msgstr ""

# Old entry (marked obsolete)
#~ msgid "Welcome to Aprende Comigo"
#~ msgstr "Bem-vindo ao Aprende Comigo"
```

#### 2. Copy and Adapt Translation
1. **Copy** the translation from obsolete entry to new one
2. **Adapt** for the new text if needed
3. **Delete** the obsolete lines (starting with `#~`)

```
# Updated
msgid "Welcome to the Aprende Comigo Platform"
msgstr "Bem-vindo à Plataforma Aprende Comigo"

# Delete these completely:
#~ msgid "Welcome to Aprende Comigo"
#~ msgstr "Bem-vindo ao Aprende Comigo"
```

### Questions & Support
- Leave comments: `# Translator: Not sure about context here`
- Ask development team for clarification on changes
- Mark as fuzzy if uncertain

## Workflow

### 1. Developer adds new strings
```python
# Mark string for translation
messages.info(request, _("Please check your email for verification link."))
```

### 2. Extract strings to .po files
```bash
python manage.py makemessages -l pt_PT --no-location
```

### 3. Translator works on .po file
- Open in Poedit
- Translate untranslated strings
- Handle any obsolete entries

### 4. Compile translations
```bash
python manage.py compilemessages
```

### 5. Test translations
- Use language switcher in UI (🇬🇧/🇵🇹 flags)
- Verify all pages show correct language
- Check for missing translations

## Language Switcher

### Location
- **Mobile**: Top header next to profile avatar
- **Desktop**: Left sidebar above logout button

### How It Works
- Dropdown with flag icons
- Instant language switching
- Preference saved for 1 year
- Fallback to English if translation missing

## Testing

### Manual Testing
1. Switch language using flag dropdown
2. Navigate all pages
3. Check for untranslated strings
4. Verify date/number formatting

### Automated Checks
```bash
# Check translation coverage
python scripts/translation_helper.py check

# Find untranslated strings in code
python manage.py mark_translations --check
```

## Best Practices

1. **Use lazy translation for models** - Evaluated once at startup
2. **Provide context for ambiguous terms** - Clarify meaning
3. **Include translator comments** - Explain context
4. **Test with longest translations** - Portuguese is often longer
5. **Don't concatenate translated strings** - Use variables instead
6. **Always write English in source code** - Never Portuguese

## File Structure
```
locale/
├── en_GB/
│   └── LC_MESSAGES/
│       └── django.po     # Not needed (source is English)
└── pt_PT/
    └── LC_MESSAGES/
        ├── django.po     # Edit this file
        └── django.mo     # Compiled (auto-generated)
```

## Summary

- **970+ strings** ready for translation
- **Source Language**: English (UK)
- **Target Language**: Portuguese (Portugal)
- **Translator works on**: `locale/pt_PT/LC_MESSAGES/django.po`
- **Language switching**: Available in navigation UI
- **Fallback**: English when translation missing

This system ensures consistency, maintainability, and scalability for Aprende Comigo's internationalization needs.