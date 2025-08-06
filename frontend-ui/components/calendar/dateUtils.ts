/**
 * Date validation and utility functions for calendar components
 * Ensures robustness against malformed API responses
 */

export interface ValidatedDate {
  isValid: boolean;
  date: Date | null;
  error?: string;
}

/**
 * Validates and parses a date string from API responses
 * @param dateString - Date string to validate
 * @returns ValidatedDate object with validation results
 */
export function validateDate(dateString: string | undefined | null): ValidatedDate {
  if (!dateString) {
    return {
      isValid: false,
      date: null,
      error: 'Date string is null or undefined'
    };
  }

  // Check if it's already a valid ISO date string
  if (typeof dateString !== 'string') {
    return {
      isValid: false,
      date: null,
      error: 'Date must be a string'
    };
  }

  try {
    const date = new Date(dateString);
    
    // Check if the date is valid
    if (isNaN(date.getTime())) {
      return {
        isValid: false,
        date: null,
        error: 'Invalid date format'
      };
    }

    // Additional check for reasonable date ranges (not too far in past/future)
    const now = new Date();
    const minDate = new Date(now.getFullYear() - 10, 0, 1); // 10 years ago
    const maxDate = new Date(now.getFullYear() + 10, 11, 31); // 10 years from now

    if (date < minDate || date > maxDate) {
      return {
        isValid: false,
        date: null,
        error: 'Date is outside reasonable range'
      };
    }

    return {
      isValid: true,
      date,
      error: undefined
    };
  } catch (error) {
    return {
      isValid: false,
      date: null,
      error: `Date parsing error: ${error}`
    };
  }
}

/**
 * Safely formats a date string for display
 * @param dateString - Date string to format
 * @param locale - Locale for formatting (default: 'pt-PT')
 * @param options - Intl.DateTimeFormatOptions
 * @returns Formatted date string or fallback
 */
export function safeFormatDate(
  dateString: string | undefined | null,
  locale = 'pt-PT',
  options: Intl.DateTimeFormatOptions = {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  }
): string {
  const validation = validateDate(dateString);
  
  if (!validation.isValid || !validation.date) {
    return 'Invalid Date';
  }

  try {
    return validation.date.toLocaleDateString(locale, options);
  } catch (error) {
    return 'Format Error';
  }
}

/**
 * Safely formats a date string for time display
 * @param dateString - Date string to format
 * @param locale - Locale for formatting (default: 'pt-PT')
 * @returns Formatted time string or fallback
 */
export function safeFormatTime(
  dateString: string | undefined | null,
  locale = 'pt-PT'
): string {
  const validation = validateDate(dateString);
  
  if (!validation.isValid || !validation.date) {
    return 'Invalid Time';
  }

  try {
    return validation.date.toLocaleTimeString(locale, {
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (error) {
    return 'Format Error';
  }
}

/**
 * Extracts date key (YYYY-MM-DD) safely from a date string
 * @param dateString - Date string to extract key from
 * @returns Date key string or null if invalid
 */
export function safeDateKey(dateString: string | undefined | null): string | null {
  const validation = validateDate(dateString);
  
  if (!validation.isValid || !validation.date) {
    return null;
  }

  try {
    return validation.date.toISOString().split('T')[0];
  } catch (error) {
    return null;
  }
}

/**
 * Filters and validates an array of dates, removing invalid ones
 * @param dates - Array of date strings
 * @returns Array of validated date objects
 */
export function validateDatesArray(dates: (string | undefined | null)[]): Array<{
  original: string | undefined | null;
  validated: ValidatedDate;
}> {
  return dates.map(date => ({
    original: date,
    validated: validateDate(date)
  }));
}

/**
 * Gets today's date as a safe date key
 * @returns Today's date in YYYY-MM-DD format
 */
export function getTodayKey(): string {
  return new Date().toISOString().split('T')[0];
}

/**
 * Checks if a date string represents today
 * @param dateString - Date string to check
 * @returns boolean indicating if the date is today
 */
export function isToday(dateString: string | undefined | null): boolean {
  const dateKey = safeDateKey(dateString);
  return dateKey === getTodayKey();
}