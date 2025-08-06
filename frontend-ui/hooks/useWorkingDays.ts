import { createContext, useContext, useMemo } from 'react';
import { useSchoolSettings } from './useSchoolSettings';

// Working days presets
export const WORKING_DAYS_PRESETS = {
  MONDAY_FRIDAY: {
    name: 'Monday - Friday',
    days: [0, 1, 2, 3, 4], // Monday to Friday
  },
  MONDAY_SATURDAY: {
    name: 'Monday - Saturday',
    days: [0, 1, 2, 3, 4, 5], // Monday to Saturday (default)
  },
  SUNDAY_THURSDAY: {
    name: 'Sunday - Thursday',
    days: [6, 0, 1, 2, 3], // Sunday to Thursday (Middle East pattern)
  },
  ALL_DAYS: {
    name: 'Every Day',
    days: [0, 1, 2, 3, 4, 5, 6], // All days
  },
} as const;

// Day name mappings (0=Monday, 6=Sunday)
export const DAY_NAMES = {
  0: 'Monday',
  1: 'Tuesday', 
  2: 'Wednesday',
  3: 'Thursday',
  4: 'Friday',
  5: 'Saturday',
  6: 'Sunday',
} as const;

export const DAY_NAMES_SHORT = {
  0: 'Mon',
  1: 'Tue',
  2: 'Wed', 
  3: 'Thu',
  4: 'Fri',
  5: 'Sat',
  6: 'Sun',
} as const;

export interface WorkingDaysContextValue {
  workingDays: number[];
  isWorkingDay: (dayIndex: number) => boolean;
  getWorkingWeekDates: (baseDate: Date) => Date[];
  getNonWorkingWeekDates: (baseDate: Date) => Date[];
  getWorkingDayName: (dayIndex: number) => string;
  getWorkingDayShortName: (dayIndex: number) => string;
  isLoading: boolean;
}

const WorkingDaysContext = createContext<WorkingDaysContextValue | null>(null);

export const useWorkingDays = (): WorkingDaysContextValue => {
  const { schoolSettings, loading } = useSchoolSettings();
  
  const workingDays = useMemo(() => {
    // Default to Monday-Saturday if no settings or empty array
    return schoolSettings?.working_days && schoolSettings.working_days.length > 0 
      ? schoolSettings.working_days 
      : WORKING_DAYS_PRESETS.MONDAY_SATURDAY.days;
  }, [schoolSettings?.working_days]);

  const isWorkingDay = useMemo(() => {
    return (dayIndex: number) => workingDays.includes(dayIndex);
  }, [workingDays]);

  const getWorkingWeekDates = useMemo(() => {
    return (baseDate: Date): Date[] => {
      const weekDates = getWeekDates(baseDate);
      return weekDates.filter((date) => {
        const dayIndex = date.getDay() === 0 ? 6 : date.getDay() - 1; // Convert Sunday=0 to Sunday=6
        return isWorkingDay(dayIndex);
      });
    };
  }, [isWorkingDay]);

  const getNonWorkingWeekDates = useMemo(() => {
    return (baseDate: Date): Date[] => {
      const weekDates = getWeekDates(baseDate);
      return weekDates.filter((date) => {
        const dayIndex = date.getDay() === 0 ? 6 : date.getDay() - 1; // Convert Sunday=0 to Sunday=6
        return !isWorkingDay(dayIndex);
      });
    };
  }, [isWorkingDay]);

  const getWorkingDayName = useMemo(() => {
    return (dayIndex: number): string => DAY_NAMES[dayIndex as keyof typeof DAY_NAMES];
  }, []);

  const getWorkingDayShortName = useMemo(() => {
    return (dayIndex: number): string => DAY_NAMES_SHORT[dayIndex as keyof typeof DAY_NAMES_SHORT];
  }, []);

  return {
    workingDays,
    isWorkingDay,
    getWorkingWeekDates,
    getNonWorkingWeekDates,
    getWorkingDayName,
    getWorkingDayShortName,
    isLoading: loading,
  };
};

// Helper function to get week dates (same as in calendar components)
const getWeekDates = (date: Date): Date[] => {
  const week = [];
  const startOfWeek = new Date(date);
  const day = startOfWeek.getDay();
  const diff = startOfWeek.getDate() - day; // First day is Sunday
  startOfWeek.setDate(diff);

  for (let i = 0; i < 7; i++) {
    const dayDate = new Date(startOfWeek);
    dayDate.setDate(startOfWeek.getDate() + i);
    week.push(dayDate);
  }
  return week;
};

export { WorkingDaysContext };