#!/usr/bin/env python
"""
Script to generate API documentation from Django REST Framework.
This script updates the API_CONTRACT.md file with latest API endpoints.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add the project directory to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aprendecomigo.settings")

import django
from django.urls import URLPattern, URLResolver, get_resolver

django.setup()


def collect_urls(urlpatterns, base="", result=None):
    """Recursively collect URL patterns"""
    if result is None:
        result = []

    for pattern in urlpatterns:
        if isinstance(pattern, URLPattern):
            pattern_name = pattern.name or ""
            view_name = (
                str(pattern.callback.__name__)
                if hasattr(pattern.callback, "__name__")
                else str(pattern.callback)
            )
            url_path = base + str(pattern.pattern)
            result.append(
                {
                    "path": url_path.replace("^", "").replace("$", ""),
                    "name": pattern_name,
                    "view": view_name,
                }
            )
        elif isinstance(pattern, URLResolver):
            new_base = base + str(pattern.pattern)
            collect_urls(pattern.url_patterns, new_base, result)

    return result


def generate_endpoint_docs():
    """Generate documentation for all API endpoints"""
    print("Analyzing API endpoints...")

    # Get all URL patterns
    resolver = get_resolver()
    urls = collect_urls(resolver.url_patterns)

    # Filter for API endpoints
    api_urls = [url for url in urls if "/api/" in url["path"]]

    # Group by app
    grouped_urls = {}
    for url in api_urls:
        # Try to determine the app from the URL pattern
        path_parts = url["path"].split("/")
        if len(path_parts) > 2:  # noqa: PLR2004
            app = path_parts[2].capitalize()  # Use the part after /api/
        else:
            app = "API"

        if app not in grouped_urls:
            grouped_urls[app] = []

        grouped_urls[app].append(url)

    return grouped_urls


def update_api_contract(endpoints):
    """Update API_CONTRACT.md with endpoints"""
    contract_path = Path(__file__).parent.parent / "API_CONTRACT.md"

    # Read the existing file
    try:
        with open(contract_path) as f:
            contract_content = f.read()
    except FileNotFoundError:
        print("Warning: API_CONTRACT.md not found. Creating a new one.")
        contract_content = "# API Contract Documentation\n\n"

    # Generate the endpoints section
    endpoints_section = "\n## Available Endpoints\n\n"

    for app, urls in sorted(endpoints.items()):
        endpoints_section += f"### {app}\n\n"

        for url in sorted(urls, key=lambda x: x["path"]):
            endpoints_section += f"- `{url['path']}`: {url['name'] or 'Unnamed'}\n"
            endpoints_section += f"  - View: {url['view']}\n"

        endpoints_section += "\n"

    # Find the position to insert the endpoints
    # Look for a marker or use a section heading
    marker = "## Available Endpoints"
    next_marker = "## Response Format"

    if marker in contract_content:
        # Replace the existing section
        start = contract_content.find(marker)
        end = contract_content.find(next_marker, start)
        if end == -1:
            # Next section not found, replace until the end
            new_content = contract_content[:start] + endpoints_section
        else:
            new_content = contract_content[:start] + endpoints_section + contract_content[end:]
    # Add the section before the response format section
    elif next_marker in contract_content:
        pos = contract_content.find(next_marker)
        new_content = contract_content[:pos] + endpoints_section + contract_content[pos:]
    else:
        # Append to the end
        new_content = contract_content + endpoints_section

    # Update the last updated date
    today = datetime.now().strftime("%B %d, %Y")
    if "*Last updated:" in new_content:
        parts = new_content.split("*Last updated:")
        new_content = parts[0] + f"*Last updated: {today}*"
    else:
        new_content += f"\n\n---\n\n*Last updated: {today}*"

    # Write the updated contract
    with open(contract_path, "w") as f:
        f.write(new_content)

    print(f"Updated API contract at {contract_path}")


if __name__ == "__main__":
    try:
        endpoints = generate_endpoint_docs()
        update_api_contract(endpoints)
        print("API documentation generation complete!")
    except Exception as e:
        print(f"Error generating API docs: {e}")
