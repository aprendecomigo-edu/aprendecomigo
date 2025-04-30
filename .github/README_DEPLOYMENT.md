# PythonAnywhere Deployment with GitHub Actions

This repository is configured to automatically deploy to PythonAnywhere when changes are pushed to the `main` branch.

## Setup Instructions

### 1. PythonAnywhere API Token

You'll need to generate an API token from PythonAnywhere:

1. Log in to your PythonAnywhere account
2. Go to Account Settings
3. Click on the "API Token" tab
4. Generate a new API token

### 2. GitHub Repository Secrets

Add the following secrets to your GitHub repository:

1. Go to your GitHub repository
2. Click on "Settings" → "Secrets and variables" → "Actions"
3. Add the following secrets:

**Required:**
- `PA_API_TOKEN`: Your PythonAnywhere API token
- `PA_USERNAME`: Your PythonAnywhere username
- `PA_DOMAIN`: Your website domain on PythonAnywhere (e.g., yourusername.pythonanywhere.com)

**Optional:**
- `PA_HOST`: The API host to use - should be EITHER `eu.pythonanywhere.com` OR `www.pythonanywhere.com` depending on your account location
- `PA_VIRTUALENV_PATH`: Path to your virtualenv on PythonAnywhere (e.g., `/home/yourusername/.virtualenvs/myenv`)
- `PA_SOURCE_DIR`: The source directory containing manage.py (default: `backend`)

### 3. Initial PythonAnywhere Setup

Before the automatic deployment works, you need to set up your PythonAnywhere account:

1. Create a web app on PythonAnywhere (Django framework)
2. Set up the correct Python version, virtualenv path, and source directory in your web app settings
3. Make sure your WSGI configuration file is properly set up

### 4. First Deployment

1. Push changes to the `main` branch
2. GitHub Actions will trigger the deployment workflow
3. Monitor the deployment process in the "Actions" tab of your repository

## How It Works

The deployment process:

1. When you push to the `main` branch, the GitHub Actions workflow is triggered
2. The script first tests the API connection to validate credentials
3. It uploads all files from your backend directory to PythonAnywhere
4. It creates a console to run post-deployment tasks:
   - Installing Python requirements (if PA_VIRTUALENV_PATH is set)
   - Running database migrations (if PA_VIRTUALENV_PATH is set)
5. The script monitors console output for potential errors
6. Finally, it reloads your web application to apply the changes

## Running Deployment Locally

### Using Environment Variables

You can run the deployment script locally using environment variables:

```bash
# Set environment variables
export PA_API_TOKEN="your-api-token"
export PA_USERNAME="your-username"
export PA_DOMAIN="your-domain.pythonanywhere.com"
export PA_HOST="eu.pythonanywhere.com"  # or www.pythonanywhere.com for US accounts
export PA_VIRTUALENV_PATH="/home/yourusername/.virtualenvs/myenv"
export PA_SOURCE_DIR="backend"

# Run the deployment script
python backend/scripts/deploy_to_pythonanywhere.py
```

### Using a .env File (Recommended)

Alternatively, you can create a `.env` file in the `backend/` directory with the following content:

```
PA_API_TOKEN=your-api-token
PA_USERNAME=your-username
PA_DOMAIN=your-domain.pythonanywhere.com
PA_HOST=eu.pythonanywhere.com
PA_VIRTUALENV_PATH=/home/yourusername/.virtualenvs/myenv
PA_SOURCE_DIR=backend
```

Then simply run:

```bash
# Install python-dotenv if you don't have it
pip install python-dotenv

# Run the deployment script
python backend/scripts/deploy_to_pythonanywhere.py
```

The script will automatically load the environment variables from the `.env` file.

## Troubleshooting

If the deployment fails:

1. Check the GitHub Actions logs for error messages
2. Verify that your API token is correct and has not expired
3. Make sure your web app is correctly configured on PythonAnywhere
4. Check that the paths in the deployment script match your project structure
5. Review console output for errors during requirements installation or migrations
6. Verify you're using the correct API host (`eu.pythonanywhere.com` for EU accounts or `www.pythonanywhere.com` for US accounts)
7. If you get 404 errors, check the URLs being constructed in the debug output
