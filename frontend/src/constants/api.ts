/**
 * API constants for different environments
 */
import { DEV_API_URL, PROD_API_URL } from '@env';

// Current API URL based on environment
export const API_URL = __DEV__ ? DEV_API_URL : PROD_API_URL;
