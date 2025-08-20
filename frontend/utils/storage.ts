/**
 * Platform-aware storage utility that provides a consistent interface
 * for storing data across web and mobile platforms.
 *
 * This file automatically resolves to the appropriate platform-specific implementation:
 * - storage.web.ts for web platforms
 * - storage.native.ts for iOS/Android platforms
 */

// Export types for consistency
export interface StorageInterface {
  getItem(key: string): Promise<string | null>;
  setItem(key: string, value: string): Promise<void>;
  removeItem(key: string): Promise<void>;
  clear(): Promise<void>;
  getAllKeys(): Promise<readonly string[]>;
}

// Note: The actual implementation will be resolved automatically by React Native's
// platform-specific file resolution (.web.ts vs .native.ts vs .ts)
// This file serves as a type declaration and fallback.

// Fallback implementation (should not be used in practice)
class DefaultStorage implements StorageInterface {
  async getItem(_key: string): Promise<string | null> {
    throw new Error('Platform-specific storage implementation not found');
  }

  async setItem(_key: string, _value: string): Promise<void> {
    throw new Error('Platform-specific storage implementation not found');
  }

  async removeItem(_key: string): Promise<void> {
    throw new Error('Platform-specific storage implementation not found');
  }

  async clear(): Promise<void> {
    throw new Error('Platform-specific storage implementation not found');
  }

  async getAllKeys(): Promise<readonly string[]> {
    throw new Error('Platform-specific storage implementation not found');
  }
}

// Export fallback (should be overridden by platform-specific files)
export const storage = new DefaultStorage();
export const { getItem, setItem, removeItem, clear, getAllKeys } = storage;
export default storage;
