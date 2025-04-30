# API Usage Guide

This document explains how to make API requests to the backend in different environments.

## API Configuration

The API is configured to automatically point to the correct backend URL based on the current environment:

- **Development**:
  - iOS: `http://localhost:8000/api`
  - Android: `http://10.0.2.2:8000/api` (Android emulator uses 10.0.2.2 to access host machine)
  - Web: `http://localhost:8000/api`

- **Staging**: `https://staging-api.aprendecomigo.com/api`

- **Production**: `https://api.aprendecomigo.com/api`

## Making API Requests

### Using the API Client

We use a pre-configured Axios client for all API requests. This client automatically:
1. Uses the correct backend URL for your environment
2. Attaches authentication tokens
3. Handles common error cases

```typescript
import apiClient from '@/api/apiClient';

// Example GET request
const fetchData = async () => {
  try {
    const response = await apiClient.get('/endpoint');
    return response.data;
  } catch (error) {
    console.error('Error fetching data:', error);
    throw error;
  }
};

// Example POST request
const createData = async (data) => {
  try {
    const response = await apiClient.post('/endpoint', data);
    return response.data;
  } catch (error) {
    console.error('Error creating data:', error);
    throw error;
  }
};
```

## Adding New API Endpoints

If you need to add new API endpoints or services:

1. Add the new endpoint URLs to `constants/api.ts` if they differ by environment:

```typescript
const config = {
  development: {
    API_URL: // existing URL,
    NEW_SERVICE_URL: 'http://localhost:8001/service',
  },
  staging: {
    API_URL: // existing URL,
    NEW_SERVICE_URL: 'https://staging-service.aprendecomigo.com',
  },
  production: {
    API_URL: // existing URL,
    NEW_SERVICE_URL: 'https://service.aprendecomigo.com',
  },
};

// Export the new URL
export const NEW_SERVICE_URL = activeConfig.NEW_SERVICE_URL;
```

2. Create service-specific API clients if needed:

```typescript
// in api/newServiceClient.ts
import axios from 'axios';
import { NEW_SERVICE_URL } from '@/constants/api';

const newServiceClient = axios.create({
  baseURL: NEW_SERVICE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export default newServiceClient;
```

## Testing with Physical Devices

When testing with physical devices on a local network, you'll need to update the development API URL to point to your computer's local IP address:

1. Find your computer's IP address (usually something like 192.168.1.X)
2. Update the API URL in `constants/api.ts`:

```typescript
// Uncomment and modify this line for testing on physical devices
config.development.API_URL = 'http://192.168.1.X:8000/api'; // Replace X with your IP
```

## Troubleshooting API Connections

If you're having issues connecting to the API:

1. Verify the correct environment is set (check console logs)
2. Ensure your backend server is running at the expected URL
3. Check that your device/emulator can reach the server (network connectivity)
4. For physical devices, ensure you're using the correct IP address
5. For development, check if CORS is properly configured on the backend

## Environment Variables in CI/CD

The GitHub Actions workflows automatically set the correct environment:

- `staging.yml` sets `EXPO_PUBLIC_ENV=staging`
- `production.yml` sets `EXPO_PUBLIC_ENV=production`

This ensures that the deployed applications connect to the correct backend environment.
