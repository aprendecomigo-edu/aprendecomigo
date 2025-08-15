import React from 'react';
import { View, Text } from 'react-native';
import { Calendar, DateData, MarkingProps } from 'react-native-calendars';

import { calendarTheme, darkCalendarTheme, DOT_COLORS, getMultiDotStyle } from './CalendarTheme';

import { ClassSchedule } from '@/api/schedulerApi';
import { Task } from '@/api/tasksApi';

interface MonthViewProps {
  currentDate: Date;
  classes: ClassSchedule[];
  tasks: Task[];
  onDayPress: (day: DateData) => void;
  isDarkMode?: boolean;
}

interface MarkedDates {
  [key: string]: MarkingProps;
}

// Custom dot component for multi-dot marking
const MultiDotMarking: React.FC<{ dots: { color: string; key: string }[] }> = ({ dots }) => {
  if (dots.length === 0) return null;

  return (
    <View
      style={{
        flexDirection: 'row',
        justifyContent: 'center',
        alignItems: 'center',
        position: 'absolute',
        bottom: 2,
        left: 0,
        right: 0,
      }}
    >
      {dots.slice(0, 3).map((dot, index) => {
        // Limit to 3 dots max
        const dotStyle = getMultiDotStyle(Math.min(dots.length, 3), index);
        return (
          <View
            key={`${dot.color}-${index}`}
            style={[
              {
                width: 6,
                height: 6,
                borderRadius: 3,
                backgroundColor: dot.color,
              },
              dotStyle,
            ]}
          />
        );
      })}
    </View>
  );
};

export const MonthView: React.FC<MonthViewProps> = ({
  currentDate,
  classes,
  tasks,
  onDayPress,
  isDarkMode = false,
}) => {
  // Create marked dates object with dots for events
  const createMarkedDates = (): MarkedDates => {
    const marked: MarkedDates = {};
    const today = new Date().toISOString().split('T')[0];

    // Add today's marking
    marked[today] = {
      customStyles: {
        container: {
          borderWidth: 2,
          borderColor: DOT_COLORS.class,
          borderRadius: 16,
        },
        text: {
          color: isDarkMode ? '#ffffff' : '#030712',
          fontWeight: '600',
        },
      },
    };

    // Process classes
    const safeClasses = classes || [];
    safeClasses.forEach(classItem => {
      const dateKey = classItem.scheduled_date;
      if (!marked[dateKey]) {
        marked[dateKey] = { dots: [], customStyles: {} };
      }

      if (!marked[dateKey].dots) {
        marked[dateKey].dots = [];
      }

      // Add class dot
      marked[dateKey].dots!.push({
        key: `class-${classItem.id}`,
        color: DOT_COLORS.class,
      });

      // Override today's marking if it has events
      if (dateKey === today) {
        marked[dateKey].customStyles = {
          container: {
            borderWidth: 2,
            borderColor: DOT_COLORS.class,
            borderRadius: 16,
          },
          text: {
            color: isDarkMode ? '#ffffff' : '#030712',
            fontWeight: '600',
          },
        };
      }
    });

    // Process tasks
    const safeTasks = tasks || [];
    safeTasks.forEach(task => {
      if (!task.due_date) return;

      const dateKey = task.due_date.split('T')[0];
      if (!marked[dateKey]) {
        marked[dateKey] = { dots: [], customStyles: {} };
      }

      if (!marked[dateKey].dots) {
        marked[dateKey].dots = [];
      }

      // Determine dot color based on task properties
      let dotColor = DOT_COLORS.task;
      if (task.is_urgent) {
        dotColor = DOT_COLORS.urgent;
      } else if (task.status === 'completed') {
        dotColor = DOT_COLORS.completed;
      }

      // Add task dot
      marked[dateKey].dots!.push({
        key: `task-${task.id}`,
        color: dotColor,
      });

      // Override today's marking if it has events
      if (dateKey === today) {
        marked[dateKey].customStyles = {
          container: {
            borderWidth: 2,
            borderColor: DOT_COLORS.class,
            borderRadius: 16,
          },
          text: {
            color: isDarkMode ? '#ffffff' : '#030712',
            fontWeight: '600',
          },
        };
      }
    });

    return marked;
  };

  const markedDates = createMarkedDates();

  return (
    <Calendar
      current={currentDate.toISOString().split('T')[0]}
      onDayPress={onDayPress}
      monthFormat="MMMM yyyy"
      onMonthChange={month => {
        // Handle month change if needed
        if (__DEV__) {
          console.log('Month changed to:', month);
        }
      }}
      hideArrows={false}
      renderArrow={direction => (direction === 'left' ? '←' : '→')}
      hideExtraDays={true}
      disableMonthChange={false}
      firstDay={1} // Monday as first day
      hideDayNames={false}
      showWeekNumbers={false}
      disableAllTouchEventsForDisabledDays={true}
      enableSwipeMonths={true}
      markedDates={markedDates}
      markingType="multi-dot"
      theme={isDarkMode ? darkCalendarTheme : calendarTheme}
      style={{
        borderWidth: 1,
        borderColor: isDarkMode ? '#374151' : '#e5e7eb',
        borderRadius: 12,
        marginHorizontal: 4,
      }}
      // Custom day component for multi-dot rendering
      dayComponent={({ date, state, marking }) => {
        const isToday = date?.dateString === new Date().toISOString().split('T')[0];
        const isSelected = marking?.selected;
        const dots = marking?.dots || [];

        let textColor = isDarkMode ? '#ffffff' : '#030712';
        let backgroundColor = 'transparent';
        let borderColor = 'transparent';
        let borderWidth = 0;

        if (state === 'disabled') {
          textColor = isDarkMode ? '#6b7280' : '#9ca3af';
        } else if (isSelected) {
          backgroundColor = DOT_COLORS.class;
          textColor = '#ffffff';
        } else if (isToday) {
          borderColor = DOT_COLORS.class;
          borderWidth = 2;
        }

        return (
          <View
            style={{
              width: 32,
              height: 32,
              alignItems: 'center',
              justifyContent: 'center',
              position: 'relative',
              backgroundColor,
              borderColor,
              borderWidth,
              borderRadius: 16,
            }}
          >
            <Text
              style={{
                fontSize: 16,
                color: textColor,
                fontWeight: isToday ? '600' : '400',
              }}
            >
              {date?.day}
            </Text>
            {dots.length > 0 && <MultiDotMarking dots={dots} />}
          </View>
        );
      }}
    />
  );
};

export default MonthView;
