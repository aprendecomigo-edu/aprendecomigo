import { Theme } from 'react-native-calendars';
import { Platform } from 'react-native';

// Use Aprende Comigo color system with actual hex colors (React Native compatible)
// These colors match the design system defined in tailwind.config.js

export const calendarTheme: Theme = {
  // Background colors
  backgroundColor: '#ffffff',
  calendarBackground: '#ffffff',
  
  // Text colors
  textSectionTitleColor: '#4b5563',
  selectedDayBackgroundColor: '#2563eb',
  selectedDayTextColor: '#ffffff',
  todayTextColor: '#2563eb',
  dayTextColor: '#030712',
  textDisabledColor: '#9ca3af',
  dotColor: '#2563eb',
  selectedDotColor: '#ffffff',
  arrowColor: '#2563eb',
  disabledArrowColor: '#9ca3af',
  monthTextColor: '#030712',
  indicatorColor: '#2563eb',
  
  // Font styling
  textDayFontFamily: Platform.OS === 'ios' ? 'System' : 'Roboto',
  textMonthFontFamily: Platform.OS === 'ios' ? 'System' : 'Roboto',
  textDayHeaderFontFamily: Platform.OS === 'ios' ? 'System' : 'Roboto',
  textDayFontWeight: '400',
  textMonthFontWeight: '600',
  textDayHeaderFontWeight: '500',
  textDayFontSize: 16,
  textMonthFontSize: 18,
  textDayHeaderFontSize: 13,
  
  // Additional styling
  'stylesheet.calendar.header': {
    week: {
      marginTop: 5,
      flexDirection: 'row',
      justifyContent: 'space-between',
    },
  },
  
  // Day marking styles - these will be used for our multi-dot implementation
  'stylesheet.day.basic': {
    base: {
      width: 40,
      height: 40,
      alignItems: 'center',
      justifyContent: 'center',
      margin: 2,
    },
    today: {
      backgroundColor: 'transparent',
      borderWidth: 2,
      borderColor: '#2563eb',
      borderRadius: 20,
    },
    selected: {
      backgroundColor: '#2563eb',
      borderRadius: 20,
    },
  },
};

export const darkCalendarTheme: Theme = {
  // Background colors - Dark mode
  backgroundColor: '#030712',
  calendarBackground: '#030712',
  
  // Text colors - Dark mode
  textSectionTitleColor: '#9ca3af',
  selectedDayBackgroundColor: '#2563eb',
  selectedDayTextColor: '#ffffff',
  todayTextColor: '#2563eb',
  dayTextColor: '#ffffff',
  textDisabledColor: '#6b7280',
  dotColor: '#2563eb',
  selectedDotColor: '#ffffff',
  arrowColor: '#2563eb',
  disabledArrowColor: '#6b7280',
  monthTextColor: '#ffffff',
  indicatorColor: '#2563eb',
  
  // Font styling
  textDayFontFamily: Platform.OS === 'ios' ? 'System' : 'Roboto',
  textMonthFontFamily: Platform.OS === 'ios' ? 'System' : 'Roboto',
  textDayHeaderFontFamily: Platform.OS === 'ios' ? 'System' : 'Roboto',
  textDayFontWeight: '400',
  textMonthFontWeight: '600',
  textDayHeaderFontWeight: '500',
  textDayFontSize: 16,
  textMonthFontSize: 18,
  textDayHeaderFontSize: 13,
  
  // Additional styling
  'stylesheet.calendar.header': {
    week: {
      marginTop: 5,
      flexDirection: 'row',
      justifyContent: 'space-between',
    },
  },
  
  // Day marking styles - Dark mode
  'stylesheet.day.basic': {
    base: {
      width: 40,
      height: 40,
      alignItems: 'center',
      justifyContent: 'center',
      margin: 2,
    },
    today: {
      backgroundColor: 'transparent',
      borderWidth: 2,
      borderColor: '#2563eb',
      borderRadius: 20,
    },
    selected: {
      backgroundColor: '#2563eb',
      borderRadius: 20,
    },
  },
};

// Dot colors for different event types - Using actual hex colors
export const DOT_COLORS = {
  class: '#2563eb',      // primary-600 - Blue for classes
  task: '#d97706',       // warning-600 - Orange for tasks  
  urgent: '#dc2626',     // error-600 - Red for urgent items
  completed: '#16a34a',  // success-600 - Green for completed items
} as const;

// Multi-dot positioning helper
export const getMultiDotStyle = (dotCount: number, index: number) => {
  if (dotCount === 1) {
    return { marginLeft: 0, marginRight: 0 };
  }
  
  const spacing = 6; // Space between dots
  const totalWidth = (dotCount * 6) + ((dotCount - 1) * spacing);
  const startOffset = -(totalWidth / 2) + 3; // Center the dots
  
  return {
    marginLeft: index === 0 ? startOffset : spacing,
    marginRight: 0,
  };
};