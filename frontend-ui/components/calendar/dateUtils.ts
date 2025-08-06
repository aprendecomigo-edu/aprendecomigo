/**
 * Date validation and formatting utilities for calendar components
 */

interface DateValidationResult {
  isValid: boolean;
  date?: Date;
  error?: string;
}

/**
 * Validates a date string and returns parsed date if valid
 */
export const validateDate = (dateString: string): DateValidationResult => {
  if (!dateString) {
    return { isValid: false, error: 'Date string is empty' };
  }

  try {
    const date = new Date(dateString);
    
    // Check if date is valid
    if (isNaN(date.getTime())) {
      return { isValid: false, error: 'Invalid date format' };
    }

    return { isValid: true, date };
  } catch (error) {
    return { isValid: false, error: 'Failed to parse date' };
  }
};

/**
 * Safely formats a date string for display
 */
export const safeFormatDate = (dateString: string): string => {
  const validation = validateDate(dateString);
  
  if (!validation.isValid || !validation.date) {
    return 'Invalid Date';
  }

  try {
    return validation.date.toLocaleDateString('pt-PT', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
  } catch (error) {
    return dateString; // Fallback to original string
  }
};

/**
 * Safely formats a date string for time display
 */
export const safeFormatTime = (dateString: string): string => {
  const validation = validateDate(dateString);
  
  if (!validation.isValid || !validation.date) {
    return 'Invalid Time';
  }

  try {
    return validation.date.toLocaleTimeString('pt-PT', {
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch (error) {
    return dateString; // Fallback to original string
  }
};

/**
 * Safely creates a date key for calendar marking
 */
export const safeDateKey = (dateString: string): string => {
  const validation = validateDate(dateString);
  
  if (!validation.isValid || !validation.date) {
    return ''; // Return empty string for invalid dates
  }

  return validation.date.toISOString().split('T')[0];
};

/**
 * Gets today's date key
 */
export const getTodayKey = (): string => {
  return new Date().toISOString().split('T')[0];
};

/**
 * Checks if a date is today
 */
export const isToday = (dateString: string): boolean => {
  const validation = validateDate(dateString);
  
  if (!validation.isValid || !validation.date) {
    return false;
  }

  const today = new Date();
  const date = validation.date;
  
  return (
    date.getFullYear() === today.getFullYear() &&
    date.getMonth() === today.getMonth() &&
    date.getDate() === today.getDate()
  );
};

/**
 * Gets the start of week for a given date (Sunday as first day)
 */
export const getWeekStart = (date: Date): Date => {
  const start = new Date(date);
  const day = start.getDay();
  const diff = start.getDate() - day;
  start.setDate(diff);
  start.setHours(0, 0, 0, 0);
  return start;
};

/**
 * Gets all dates in a week for a given date
 */
export const getWeekDates = (date: Date): Date[] => {
  const week = [];
  const startOfWeek = getWeekStart(date);

  for (let i = 0; i < 7; i++) {
    const day = new Date(startOfWeek);
    day.setDate(startOfWeek.getDate() + i);
    week.push(day);
  }
  
  return week;
};

/**
 * Formats a date for Portuguese locale with full format
 */
export const formatDateFull = (date: Date): string => {
  return date.toLocaleDateString('pt-PT', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
};

/**
 * Formats a date for Portuguese locale with short format
 */
export const formatDateShort = (date: Date): string => {
  return date.toLocaleDateString('pt-PT', {
    day: '2-digit',
    month: '2-digit',
    year: '2-digit',
  });
};