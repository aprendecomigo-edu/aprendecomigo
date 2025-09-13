#!/usr/bin/env python
"""
Translation helper script for Aprende Comigo.
Helps identify untranslated strings and generate translation files.
"""

import os
import sys

import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aprendecomigo.settings.development")
django.setup()

from django.conf import settings  # noqa: E402
from django.core.management import call_command  # noqa: E402


def generate_messages():
    """Generate or update translation files for all configured languages."""
    print("🌍 Generating translation files...")

    languages = [lang[0] for lang in settings.LANGUAGES]

    for lang in languages:
        print(f"\n📝 Processing {lang}...")
        try:
            # Generate messages without location info for cleaner .po files
            call_command(
                "makemessages",
                locale=lang,
                no_location=True,
                no_obsolete=True,
                verbosity=2,
                ignore=["venv/*", ".venv/*", "static/*", "media/*", "staticfiles/*"],
            )
            print(f"✅ Successfully generated messages for {lang}")
        except Exception as e:
            print(f"❌ Error generating messages for {lang}: {e}")


def compile_messages():
    """Compile all translation files."""
    print("\n🔨 Compiling translation files...")

    try:
        call_command("compilemessages", verbosity=2)
        print("✅ Successfully compiled all translation files")
    except Exception as e:
        print(f"❌ Error compiling messages: {e}")


def check_coverage():
    """Check translation coverage for each language."""
    import polib

    print("\n📊 Checking translation coverage...")

    languages = [lang[0] for lang in settings.LANGUAGES if lang[0] != settings.LANGUAGE_CODE]

    for lang in languages:
        po_file = os.path.join(settings.BASE_DIR, "locale", lang, "LC_MESSAGES", "django.po")

        if os.path.exists(po_file):
            po = polib.pofile(po_file)
            total = len(po)
            translated = len(po.translated_entries())
            untranslated = len(po.untranslated_entries())
            fuzzy = len(po.fuzzy_entries())

            if total > 0:
                percentage = (translated / total) * 100
                print(f"\n{lang}: {percentage:.1f}% complete")
                print(f"  ✅ Translated: {translated}")
                print(f"  ❌ Untranslated: {untranslated}")
                print(f"  ⚠️  Fuzzy: {fuzzy}")

                if untranslated > 0:
                    print("\n  First 5 untranslated strings:")
                    for entry in po.untranslated_entries()[:5]:
                        print(f"    - {entry.msgid[:50]}...")
            else:
                print(f"\n{lang}: No strings found")
        else:
            print(f"\n{lang}: Translation file not found at {po_file}")


def create_translator_package():
    """Create a ZIP package for translators with .po files and instructions."""
    from datetime import datetime
    import zipfile

    print("\n📦 Creating translator package...")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"translations_{timestamp}.zip"

    with zipfile.ZipFile(zip_filename, "w") as zipf:
        # Add .po files
        for lang in [lang[0] for lang in settings.LANGUAGES]:
            po_file = os.path.join("locale", lang, "LC_MESSAGES", "django.po")
            if os.path.exists(os.path.join(settings.BASE_DIR, po_file)):
                zipf.write(os.path.join(settings.BASE_DIR, po_file), po_file)

        # Add instructions
        instructions = """
TRANSLATION INSTRUCTIONS FOR APRENDE COMIGO
===========================================

1. Install Poedit (free translation editor):
   https://poedit.net/

2. Open the .po files in Poedit:
   - locale/pt-pt/LC_MESSAGES/django.po (Portuguese)
   - locale/en-gb/LC_MESSAGES/django.po (English)

3. For each untranslated string:
   - Look at the "msgid" (source text in English)
   - Enter your translation in "msgstr"
   - If you see %(variable)s, keep it exactly as is
   - If you see HTML tags like <strong>, keep them

4. Save your work frequently

5. When done, send back the edited .po files

IMPORTANT NOTES:
- Do NOT modify msgid lines
- Keep all %(variable)s placeholders unchanged
- Preserve HTML tags
- If unsure about context, leave a comment

Thank you for your translation work!
"""
        zipf.writestr("INSTRUCTIONS.txt", instructions)

    print(f"✅ Translator package created: {zip_filename}")
    return zip_filename


def main():
    """Main function to run translation tasks."""
    import argparse

    parser = argparse.ArgumentParser(description="Translation helper for Aprende Comigo")
    parser.add_argument("command", choices=["generate", "compile", "check", "package", "all"], help="Command to run")

    args = parser.parse_args()

    if args.command == "generate":
        generate_messages()
    elif args.command == "compile":
        compile_messages()
    elif args.command == "check":
        check_coverage()
    elif args.command == "package":
        create_translator_package()
    elif args.command == "all":
        generate_messages()
        check_coverage()
        compile_messages()
        create_translator_package()


if __name__ == "__main__":
    main()
