# Netlify Deployment Setup

This project is configured to automatically deploy to Netlify when changes are pushed to the main branch. The deployment is managed through GitHub Actions.

## Initial Setup

### 1. Create a Netlify Site

If you haven't already created a Netlify site for this project:

1. Sign up or log in to [Netlify](https://app.netlify.com/)
2. Click "New site from Git" and choose "GitHub"
3. Select your repository but **don't** set up continuous deployment through Netlify itself (we'll use GitHub Actions instead)
4. Configure your site name and other settings as needed

### 2. Get Netlify Authentication Token

To allow GitHub Actions to deploy to Netlify, you need an authentication token:

1. Go to [Netlify user settings](https://app.netlify.com/user/applications)
2. Under "Personal access tokens", click "New access token"
3. Give it a name (e.g., "GitHub Actions Deploy")
4. Set the appropriate scope (at least "sites:write")
5. Click "Generate token" and copy the token value

### 3. Get Netlify Site ID

To identify which Netlify site to deploy to:

1. Go to your site in the Netlify dashboard
2. The site ID is in the URL: `https://app.netlify.com/sites/[SITE_NAME]/settings/general`
   - It looks like: `a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6`
3. Or find it in your site settings under "Site information"

### 4. Add GitHub Secrets

Add the Netlify token and site ID as secrets in your GitHub repository:

1. Go to your GitHub repository
2. Navigate to "Settings" > "Secrets and variables" > "Actions"
3. Click "New repository secret"
4. Add the following secrets:
   - Name: `NETLIFY_AUTH_TOKEN`, Value: [your-netlify-auth-token]
   - Name: `NETLIFY_SITE_ID`, Value: [your-netlify-site-id]

## About the Deployment Setup

### Output Type Configuration

This app is configured to use static rendering (`"output": "static"` in app.json), which outputs separate HTML files for every route in the app directory. This is why we don't need to set up redirects for SPA routing.

If you change the output type to `"single"` in the future, you would need to add a `_redirects` file to handle client-side routing.

### How the GitHub Actions Workflow Works

The workflow:

1. Triggers when code is pushed to the main branch
2. Sets up Node.js and installs dependencies
3. Builds the website with `npx expo export -p web`
4. Deploys the built files to Netlify

## Alternative: Using Netlify's Built-in CI/CD

Instead of GitHub Actions, you can use Netlify's built-in continuous deployment:

1. Start a new Netlify project
2. Pick GitHub as your Git hosting service and select your repository
3. Configure the build settings:
   - Build command: `cd frontend-ui && npx expo export -p web`
   - Publish directory: `frontend-ui/dist`
4. Click "Deploy site"

## Manual Deployment

If you need to deploy manually:

1. Install the Netlify CLI: `npm install -g netlify-cli`
2. Build the website: `cd frontend-ui && npx expo export -p web`
3. Deploy to Netlify: `netlify deploy --dir dist`

For production deployment: `netlify deploy --dir dist --prod`
