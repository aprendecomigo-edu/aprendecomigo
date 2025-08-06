import React, { useMemo } from 'react';
import { Calendar, DateData, MarkingProps } from 'react-native-calendars';
import { View } from 'react-native';
import { calendarTheme, darkCalendarTheme, DOT_COLORS, getMultiDotStyle } from './CalendarTheme';
import { ClassSchedule } from '@/api/schedulerApi';
import { Task } from '@/api/tasksApi';
import { validateDate, safeDateKey, getTodayKey } from './dateUtils';
import { useWorkingDays } from '@/hooks/useWorkingDays';

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
    <View style={{ 
      flexDirection: 'row', 
      justifyContent: 'center', 
      alignItems: 'center',
      position: 'absolute',
      bottom: 3,
      left: 0,
      right: 0,
    }}>
      {dots.slice(0, 3).map((dot, index) => { // Limit to 3 dots max
        const dotStyle = getMultiDotStyle(Math.min(dots.length, 3), index);
        return (
          <View
            key={`${dot.color}-${index}`}
            style={[
              {
                width: 8,
                height: 8,
                borderRadius: 4,
                backgroundColor: dot.color,
                marginHorizontal: 1,
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
  isDarkMode = false 
}) => {
  const { isWorkingDay, isLoading } = useWorkingDays();
  
  // Memoized marked dates computation for performance
  const markedDates = useMemo((): MarkedDates => {
    const marked: MarkedDates = {};
    const today = getTodayKey();
    
    // Add today's marking
    marked[today] = {
      customStyles: {
        container: {
          borderWidth: 2,
          borderColor: DOT_COLORS.class,
          borderRadius: 20, // Increased from 16 for better visibility
        },
        text: {
          color: isDarkMode ? '#ffffff' : '#030712',
          fontWeight: '600',
        },
      },
    };
    
    // Process classes with validation
    const safeClasses = classes || [];
    safeClasses.forEach(classItem => {
      const validation = validateDate(classItem.scheduled_date);
      if (!validation.isValid) return;
      
      const dateKey = safeDateKey(classItem.scheduled_date);
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
            borderRadius: 20,
          },
          text: {
            color: isDarkMode ? '#ffffff' : '#030712',
            fontWeight: '600',
          },
        };
      }
    });
    
    // Process tasks with validation
    const safeTasks = tasks || [];
    safeTasks.forEach(task => {
      if (!task.due_date) return;
      
      const validation = validateDate(task.due_date);
      if (!validation.isValid) return;
      
      const dateKey = safeDateKey(task.due_date);
      if (!marked[dateKey]) {
        marked[dateKey] = { dots: [], customStyles: {} };
      }
      
      if (!marked[dateKey].dots) {
        marked[dateKey].dots = [];
      }
      
      // Add task dot with priority-based color
      const taskColor = task.priority === 'high' ? DOT_COLORS.highPriority : 
                       task.priority === 'medium' ? DOT_COLORS.mediumPriority : 
                       DOT_COLORS.lowPriority;
      
      marked[dateKey].dots!.push({
        key: `task-${task.id}`,
        color: taskColor,
      });
      
      // Override today's marking if it has tasks
      if (dateKey === today) {
        marked[dateKey].customStyles = {
          container: {
            borderWidth: 2,
            borderColor: taskColor,
            borderRadius: 20,
          },
          text: {
            color: isDarkMode ? '#ffffff' : '#030712',
            fontWeight: '600',
          },
        };
      }
    });

    // Add working days styling - make non-working days visually distinct
    if (!isLoading) {
      // Get current month's dates
      const year = currentDate.getFullYear();
      const month = currentDate.getMonth();
      const daysInMonth = new Date(year, month + 1, 0).getDate();
      
      for (let day = 1; day <= daysInMonth; day++) {
        const date = new Date(year, month, day);
        const dayIndex = date.getDay() === 0 ? 6 : date.getDay() - 1; // Convert Sunday=0 to Sunday=6
        const dateKey = date.toISOString().split('T')[0];
        
        if (!isWorkingDay(dayIndex)) {
          // Style non-working days
          if (!marked[dateKey]) {
            marked[dateKey] = { customStyles: {} };
          }
          
          // Only add non-working day styling if it's not today and doesn't have events
          if (dateKey !== today && (!marked[dateKey].dots || marked[dateKey].dots!.length === 0)) {
            marked[dateKey].customStyles = {
              container: {
                opacity: 0.4, // Make non-working days more transparent
                backgroundColor: isDarkMode ? '#374151' : '#F3F4F6',
              },
              text: {
                color: isDarkMode ? '#9CA3AF' : '#6B7280',
                fontWeight: '400',
              },
            };
          }
        }
      }
    }
    
    return marked;
  }, [classes, tasks, isDarkMode, isWorkingDay, isLoading, currentDate]);

  return (
    <Calendar
      current={currentDate.toISOString().split('T')[0]}
      onDayPress={onDayPress}
      markedDates={markedDates}
      markingType="multi-dot"
      theme={isDarkMode ? darkCalendarTheme : calendarTheme}
      monthFormat="MMMM yyyy"
      firstDay={1} // Start week on Monday
      showWeekNumbers={false}
      disableMonthChange={false}
      hideArrows={true} // We handle navigation in parent component
      hideExtraDays={false}
      disableArrowLeft={true}
      disableArrowRight={true}
      style={{
        borderRadius: 12,
        elevation: 2,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
        backgroundColor: isDarkMode ? '#1F2937' : '#ffffff',
        paddingBottom: 8,
      }}
      dayComponent={({ date, state, marking }) => {
        const isToday = date?.dateString === getTodayKey();
        const hasMarking = marking && (marking.dots?.length > 0 || marking.customStyles);
        
        return (
          <View style={{ 
            width: 40, 
            height: 40, 
            justifyContent: 'center', 
            alignItems: 'center',
            position: 'relative',
          }}>
            <View
              style={[
                {
                  width: 32,
                  height: 32,
                  borderRadius: 16,
                  justifyContent: 'center',
                  alignItems: 'center',
                },
                marking?.customStyles?.container,
                isToday && !hasMarking ? {
                  borderWidth: 2,
                  borderColor: DOT_COLORS.class,
                } : {},
              ]}
            >
              {/* Day number text */}
              <View style={{
                justifyContent: 'center',
                alignItems: 'center',
              }}>
                <View
                  style={[
                    {
                      color: state === 'disabled' ? '#d9d9d9' : 
                            isToday ? (isDarkMode ? '#ffffff' : '#030712') :
                            state === 'today' ? (isDarkMode ? '#ffffff' : '#030712') :
                            isDarkMode ? '#ffffff' : '#030712',
                      fontSize: 16,
                      fontWeight: isToday ? '600' : '400',
                    },
                    marking?.customStyles?.text,
                  ]}
                />
              </View>
              
              {/* Multi-dot marking */}
              {marking?.dots && marking.dots.length > 0 && (
                <MultiDotMarking dots={marking.dots} />
              )}
            </View>
          </View>
        );
      }}
    />
  );
};

export default MonthView;