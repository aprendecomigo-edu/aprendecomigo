# Gemini CLI Configuration

This directory contains configuration files for [Gemini CLI](https://github.com/google-gemini/gemini-cli), an AI-powered command-line assistant for code development.

## Files

- **`settings.json`** - Project-specific Gemini CLI configuration
- **`GEMINI.md`** - Project context and development guidelines for Gemini AI (located in project root)

## Configuration Overview

Our Gemini CLI is configured with:

- **Auto-accept enabled** for safe read-only operations to speed up development
- **Git-aware file filtering** to respect `.gitignore` patterns
- **Restricted tool access** focused on Django + React Native development needs
- **Excluded dangerous commands** for safety (rm -rf, sudo operations, etc.)
- **Playwright MCP server** for browser automation and web testing capabilities

## Key Features

### Allowed Development Tools
- Django management commands (`python manage.py`)
- Node.js/npm/yarn/expo for frontend development
- Git operations
- File operations (read, edit, create)
- Standard Unix utilities (ls, cat, grep, find)

### Security Restrictions
- Prevents destructive file operations
- Blocks system-level modifications
- Sandboxing disabled for better local development experience

### Browser Automation (Playwright MCP)
- **Web page interaction** - Navigate, click, type, and interact with web elements
- **Accessibility-first** - Uses structured accessibility tree instead of screenshots
- **Cross-platform testing** - Perfect for testing React Native web builds
- **Form automation** - Automate user registration, login flows, and form testing
- **Screenshot capture** - Take screenshots for debugging and documentation
- **Network monitoring** - Inspect API calls and network requests
- **PDF generation** - Save pages as PDF for reports or documentation

## Usage

With Gemini CLI installed, run from the project root:

```bash
# Start Gemini CLI with project context
gemini

# Check loaded context
/memory show

# Refresh context if GEMINI.md changes
/memory refresh

# Example browser automation commands
gemini "Navigate to localhost:3000 and test the login form"
gemini "Take a screenshot of the React Native web app dashboard"
gemini "Test user registration flow and capture any console errors"
```

### Editor Configuration

**✅ Configured: nano** - Your default editor is already set to nano (beginner-friendly alternative to vim).

To use a different editor:

**VS Code (if available):**
First install VS Code command line tools: Open VS Code → Command Palette (⌘⇧P) → "Shell Command: Install 'code' command in PATH"
```bash
export EDITOR="code --wait"
export VISUAL="code --wait"
```

**Nano (Currently active):**
```bash
export EDITOR="nano"
export VISUAL="nano"
```

**Other options:**
```bash
# TextEdit (macOS GUI)
export EDITOR="open -W -n"

# Sublime Text
export EDITOR="subl --wait"
```

Changes are automatically saved to your `~/.zshrc` file.

**Test your editor configuration:**
```bash
echo $EDITOR  # Should show: nano
```

**Nano Quick Reference:**
- `Ctrl+X` - Exit
- `Ctrl+O` - Save (Write Out)
- `Ctrl+K` - Cut line
- `Ctrl+U` - Paste line
- `Ctrl+W` - Search

The AI will automatically load the project context from `../GEMINI.md` and apply the settings from `settings.json`.

### Browser Testing Examples

With the Playwright MCP server, you can now:

```bash
# Test your React Native web build
npm run web  # Start your web server
gemini "Open localhost:3000 and test the authentication flow"

# Automate form testing
gemini "Fill out the teacher registration form with test data and submit"

# Debug UI issues
gemini "Navigate to the student dashboard and take a screenshot"

# Test responsive design
gemini "Resize browser to mobile size and test navigation menu"
```

## Customization

To modify the configuration:

1. Edit `settings.json` for tool restrictions and behavior
2. Update `../GEMINI.md` for project-specific context and guidelines
3. Run `/memory refresh` in Gemini CLI to reload changes

### Advanced Playwright Configuration

You can customize the Playwright MCP server by modifying the `args` array in `settings.json`:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": [
        "@playwright/mcp@latest",
        "--headless",
        "--device", "iPhone 15",
        "--output-dir", "./qa-tests/browser-automation"
      ]
    }
  }
}
```

Useful options for educational platform testing:
- `--headless` - Run without visible browser (faster for automated testing)
- `--device "iPhone 15"` - Test mobile-responsive React Native web interface
- `--output-dir "./qa-tests/browser-automation"` - Save screenshots and traces
- `--save-trace` - Record detailed interaction traces for debugging
- `--ignore-https-errors` - Useful for local development with self-signed certificates

For more information, see the [Gemini CLI documentation](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/configuration.md) and [Playwright MCP documentation](https://raw.githubusercontent.com/microsoft/playwright-mcp/refs/heads/main/README.md).
