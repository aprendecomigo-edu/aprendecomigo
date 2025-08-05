# React Native Calendars Integration Plan
## Aprende Comigo Platform

**Date:** 2025-01-04  
**Objective:** Integrate react-native-calendars package to enhance calendar functionality and user experience

---

## Executive Summary

This plan details the integration of `react-native-calendars` (v1.1313.0) into our existing calendar system to provide a modern, interactive calendar interface that improves booking flows and schedule visualization for all user types.

**Current State:**
- Basic list/week views with manual navigation
- Form-based date selection in booking flow
- Limited visual calendar interaction
- Custom-built calendar logic

**Target State:**
- Rich interactive calendar widgets
- Intuitive date/event selection
- Visual event representation with markings
- Enhanced user experience across all platforms

---

## Phase 1: Technical Assessment & Setup

### 1.1 Compatibility Verification ✅

**Current Stack Analysis:**
- React Native: 0.74.5 ✅ Compatible
- Expo: ~51.0.6 ✅ Expo compatible (no ejection required)
- TypeScript: ~5.3.3 ✅ Full TypeScript support
- Platform: Cross-platform (web, iOS, Android) ✅ Supported

**Package Details:**
- Version: 1.1313.0 (latest stable)
- Pure JavaScript implementation
- No native linking required
- MIT License

### 1.2 Installation & Configuration

```bash
cd frontend-ui
npm install react-native-calendars@1.1313.0
# or
yarn add react-native-calendars@1.1313.0
```

**Dependencies Check:**
- No additional native dependencies required
- Compatible with existing Expo/Gluestack UI setup

### 1.3 Portuguese Localization Setup

```typescript
import { LocaleConfig } from 'react-native-calendars';

LocaleConfig.locales['pt'] = {
  monthNames: [
    'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
  ],
  monthNamesShort: [
    'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
    'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'
  ],
  dayNames: [
    'Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado'
  ],
  dayNamesShort: ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'],
  today: 'Hoje'
};
LocaleConfig.defaultLocale = 'pt';
```

---

## Phase 2: Component Integration

### 2.1 Enhanced Calendar Components

**New Components to Create:**

1. **`CalendarWidget.tsx`** - Main calendar component
   - Month view with interactive date selection
   - Event marking system (dots, periods)
   - Integration with Gluestack UI theming

2. **`AgendaView.tsx`** - Agenda-style calendar
   - Timeline view with events
   - Scrollable date list
   - Optimized for mobile devices

3. **`CalendarEventMarkers.tsx`** - Event visualization
   - Color-coded event types (classes, tasks, availability)
   - Multiple dot indicators
   - Status-based styling

4. **`DateSelector.tsx`** - Enhanced date picker
   - Replace form-based date selection
   - Visual calendar date picker
   - Range selection capability

### 2.2 Integration with Existing Architecture

**File Structure:**
```
frontend-ui/components/
├── calendar/
│   ├── CalendarWidget.tsx
│   ├── AgendaView.tsx
│   ├── CalendarEventMarkers.tsx
│   ├── DateSelector.tsx
│   ├── CalendarTheme.ts
│   └── types.ts
└── ...
```

**TypeScript Integration:**
```typescript
// Enhanced types for calendar events
export interface CalendarEvent {
  id: string;
  date: string; // YYYY-MM-DD format
  title: string;
  type: 'class' | 'task' | 'availability' | 'unavailability';
  status?: 'scheduled' | 'confirmed' | 'completed' | 'cancelled';
  time?: string;
  duration?: number;
  color?: string;
}

export interface CalendarMarking {
  marked?: boolean;
  dotColor?: string;
  activeOpacity?: number;
  selectedColor?: string;
  selected?: boolean;
  disabled?: boolean;
}
```

### 2.3 Gluestack UI Theme Integration

**Custom Theme Configuration:**
```typescript
// components/calendar/CalendarTheme.ts
export const calendarTheme = {
  backgroundColor: '#ffffff',
  calendarBackground: '#ffffff',
  textSectionTitleColor: '#b6c1cd',
  selectedDayBackgroundColor: '#00adf5',
  selectedDayTextColor: '#ffffff',
  todayTextColor: '#00adf5',
  dayTextColor: '#2d4150',
  textDisabledColor: '#d9e1e8',
  dotColor: '#00adf5',
  selectedDotColor: '#ffffff',
  arrowColor: 'orange',
  monthTextColor: 'blue',
  indicatorColor: 'blue',
  textDayFontFamily: 'monospace',
  textMonthFontFamily: 'monospace',
  textDayHeaderFontFamily: 'monospace',
  textDayFontSize: 16,
  textMonthFontSize: 16,
  textDayHeaderFontSize: 13
};
```

---

## Phase 3: Data Integration

### 3.1 API Data Transformation

**Event Data Mapping:**
```typescript
// Transform scheduler API data for calendar
export const transformSchedulerDataForCalendar = (
  classes: ClassSchedule[],
  tasks: Task[],
  availability: TeacherAvailability[]
): { [date: string]: CalendarMarking } => {
  const markings: { [date: string]: CalendarMarking } = {};
  
  // Process class schedules
  classes.forEach(classItem => {
    const date = classItem.scheduled_date;
    markings[date] = {
      marked: true,
      dotColor: getStatusColor(classItem.status),
      events: [...(markings[date]?.events || []), {
        id: `class-${classItem.id}`,
        type: 'class',
        title: classItem.title,
        time: classItem.start_time,
        status: classItem.status
      }]
    };
  });
  
  // Process tasks
  tasks.forEach(task => {
    if (task.due_date) {
      const date = task.due_date.split('T')[0];
      markings[date] = {
        ...markings[date],
        marked: true,
        dotColor: getPriorityColor(task.priority)
      };
    }
  });
  
  return markings;
};
```

### 3.2 Real-time Updates

**WebSocket Integration:**
```typescript
// Listen for schedule changes and update calendar
useEffect(() => {
  const handleScheduleUpdate = (event: ScheduleUpdateEvent) => {
    // Refresh calendar data
    loadCalendarData();
  };
  
  // WebSocket subscription logic here
  return () => {
    // Cleanup subscription
  };
}, []);
```

### 3.3 Data Caching Strategy

**Optimize for Performance:**
- Cache calendar data for current month ± 2 months
- Lazy load adjacent months on swipe
- Update cache on data changes
- Offline capability with cached data

---

## Phase 4: User Role Implementation

### 4.1 Role-Based Calendar Views

**School Owners:**
- Full calendar overview of all classes and teachers
- Multi-school view capability
- Bulk scheduling operations
- Revenue tracking per day/month

**Teachers:**
- Personal availability management
- Class schedule overview
- Student booking requests
- Time-off request interface

**Students/Parents:**
- Available slot visualization
- Booked class overview
- Assignment due dates
- Payment due dates

**Implementation Pattern:**
```typescript
const CalendarScreen: React.FC = () => {
  const { userProfile } = useUserProfile();
  
  const renderCalendarForRole = () => {
    switch (userProfile?.user_type) {
      case 'school_owner':
        return <SchoolOwnerCalendar />;
      case 'teacher':
        return <TeacherCalendar />;
      case 'student':
      case 'parent':
        return <StudentParentCalendar />;
      default:
        return <DefaultCalendar />;
    }
  };
  
  return renderCalendarForRole();
};
```

### 4.2 Permission-Based Interactions

**Action Authorization:**
```typescript
const getCalendarPermissions = (userType: string) => ({
  canCreateEvents: ['school_owner', 'teacher'].includes(userType),
  canEditEvents: ['school_owner', 'teacher'].includes(userType),
  canDeleteEvents: ['school_owner'].includes(userType),
  canViewAllEvents: ['school_owner'].includes(userType),
  canBookSlots: ['student', 'parent'].includes(userType)
});
```

---

## Phase 5: Enhanced Booking Flow

### 5.1 Visual Date Selection

**Replace Current Form-Based Selection:**
```typescript
// Before: Dropdown date selection
<Select>
  <SelectItem label="2025-01-15" value="2025-01-15" />
</Select>

// After: Interactive calendar selection
<CalendarWidget
  onDayPress={(day) => {
    setSelectedDate(day.dateString);
    loadAvailableSlots(day.dateString);
  }}
  markedDates={{
    [selectedDate]: { selected: true, selectedColor: 'blue' }
  }}
/>
```

### 5.2 Availability Visualization

**Show Available Time Slots on Calendar:**
```typescript
const BookingCalendar: React.FC = () => {
  const [availabilityData, setAvailabilityData] = useState({});
  
  const markings = useMemo(() => {
    return transformAvailabilityForCalendar(availabilityData);
  }, [availabilityData]);
  
  return (
    <Calendar
      markedDates={markings}
      markingType="multi-dot"
      onDayPress={handleDateSelection}
    />
  );
};
```

### 5.3 Conflict Prevention

**Visual Conflict Indicators:**
- Red dots for unavailable dates
- Yellow dots for partially available dates
- Green dots for fully available dates
- Disabled styling for past dates

---

## Phase 6: Business Logic Integration

### 6.1 Revenue Optimization Features

**School Owner Dashboard Enhancements:**
```typescript
// Daily revenue visualization on calendar
const RevenueCalendar: React.FC = () => {
  const markings = useMemo(() => {
    return Object.entries(dailyRevenue).reduce((acc, [date, revenue]) => ({
      ...acc,
      [date]: {
        customStyles: {
          container: {
            backgroundColor: getRevenueColor(revenue),
          },
          text: {
            color: 'white',
            fontWeight: 'bold'
          }
        }
      }
    }), {});
  }, [dailyRevenue]);
  
  return <Calendar markingType="custom" markedDates={markings} />;
};
```

### 6.2 Teacher Utilization Tracking

**Optimize Teacher Scheduling:**
- Visual representation of teacher utilization rates
- Identify under-utilized time slots
- Suggest optimal scheduling patterns
- Track student demand patterns

### 6.3 Payment Integration

**Payment Due Date Visualization:**
```typescript
// Show payment due dates on calendar
const paymentMarkings = payments.reduce((acc, payment) => ({
  ...acc,
  [payment.due_date]: {
    marked: true,
    dotColor: payment.status === 'overdue' ? 'red' : 'orange'
  }
}), {});
```

---

## Phase 7: Platform-Specific Optimizations

### 7.1 Web Platform

**Desktop Optimizations:**
- Larger calendar view
- Keyboard navigation support
- Hover states for events
- Context menu for quick actions

**Implementation:**
```typescript
import { Platform } from 'react-native';

const CalendarWrapper: React.FC = () => {
  const calendarProps = Platform.select({
    web: {
      calendarWidth: 400,
      calendarHeight: 350,
      showWeekNumbers: true
    },
    default: {
      calendarWidth: undefined,
      calendarHeight: undefined,
      showWeekNumbers: false
    }
  });
  
  return <Calendar {...calendarProps} />;
};
```

### 7.2 Mobile Optimizations

**Touch-Friendly Interface:**
- Swipe navigation between months
- Long-press for quick actions
- Optimized touch targets
- Responsive layout for different screen sizes

### 7.3 Accessibility Improvements

**WCAG Compliance:**
```typescript
const accessibleCalendar = {
  accessibilityLabel: 'Calendar for class scheduling',
  accessibilityHint: 'Swipe left or right to navigate months',
  accessibilityRole: 'button'
};
```

---

## Phase 8: Testing & Quality Assurance

### 8.1 Automated Testing Strategy

**Test Categories:**
1. **Unit Tests** - Calendar component rendering
2. **Integration Tests** - API data transformation
3. **E2E Tests** - Booking flow completion
4. **Cross-Platform Tests** - Web, iOS, Android consistency

**Test Implementation:**
```typescript
// Example test for calendar event rendering
describe('CalendarWidget', () => {
  it('renders events correctly', () => {
    const mockEvents = [
      { id: '1', date: '2025-01-15', title: 'Math Class', type: 'class' }
    ];
    
    render(<CalendarWidget events={mockEvents} />);
    expect(screen.getByText('Math Class')).toBeTruthy();
  });
});
```

### 8.2 Performance Testing

**Metrics to Monitor:**
- Calendar render time: <200ms
- Event loading time: <500ms
- Memory usage with large datasets
- Smooth scrolling performance

### 8.3 User Acceptance Testing

**Test Scenarios by Role:**
- School owners creating bulk schedules
- Teachers setting availability
- Students booking classes
- Parents viewing child's schedule

---

## Implementation Timeline

### Week 1: Foundation
- [ ] Install and configure react-native-calendars
- [ ] Set up Portuguese localization
- [ ] Create basic CalendarWidget component
- [ ] Integrate with Gluestack UI theme

### Week 2: Core Integration
- [ ] Transform existing API data for calendar
- [ ] Implement event marking system
- [ ] Create role-based calendar views
- [ ] Test cross-platform compatibility

### Week 3: Enhanced Features
- [ ] Replace booking flow date selection
- [ ] Add availability visualization
- [ ] Implement conflict detection
- [ ] Create agenda view component

### Week 4: Optimization & Testing
- [ ] Performance optimizations
- [ ] Comprehensive testing
- [ ] User acceptance testing
- [ ] Documentation and deployment

---

## Risk Assessment & Mitigation

### Technical Risks

**Risk: Calendar performance with large datasets**
- *Mitigation*: Implement virtual scrolling and data pagination
- *Fallback*: Lazy loading with month-based data fetching

**Risk: Theme integration conflicts**
- *Mitigation*: Create custom theme adapter for Gluestack UI
- *Fallback*: Override CSS styles with NativeWind classes

**Risk: Cross-platform rendering differences**
- *Mitigation*: Platform-specific testing and adjustments
- *Fallback*: Platform.select() for platform-specific implementations

### Business Risks

**Risk: User adoption of new interface**
- *Mitigation*: Gradual rollout with A/B testing
- *Fallback*: Keep existing views as alternative option

**Risk: Performance impact on low-end devices**
- *Mitigation*: Performance profiling and optimization
- *Fallback*: Simplified calendar view for low-end devices

---

## Success Metrics

### Technical KPIs
- Calendar load time: <2s (Target: <1s)
- User interaction response: <200ms
- Crash rate: <0.1%
- Cross-platform consistency: 100%

### Business KPIs
- Booking completion rate: +15%
- User engagement time: +25%
- Schedule conflicts: -30%
- Customer satisfaction: +20%

### User Experience KPIs
- Calendar interaction rate: +40%
- Booking abandonment rate: -25%
- Support tickets for scheduling: -50%

---

## Post-Implementation Roadmap

### Phase 9: Advanced Features (Month 2)
- Drag & drop event rescheduling
- Recurring event templates
- Calendar sharing between users
- Bulk operations interface

### Phase 10: AI Integration (Month 3)
- Smart scheduling suggestions
- Optimal time slot recommendations
- Automated conflict resolution
- Predictive availability planning

### Phase 11: Analytics Dashboard (Month 4)
- Calendar usage analytics
- Booking pattern insights
- Revenue optimization suggestions
- Teacher utilization reports

---

## Conclusion

This implementation plan provides a comprehensive approach to integrating react-native-calendars into the Aprende Comigo platform. The phased approach ensures minimal disruption to current operations while delivering significant user experience improvements.

The integration aligns with our business objectives of increasing revenue through improved booking flows and enhanced user engagement across all platforms.

**Next Steps:**
1. Review and approve implementation plan
2. Allocate development resources
3. Begin Phase 1 implementation
4. Set up monitoring and success tracking

---

**Document Owner:** Founder  
**Last Updated:** 2025-01-04  
**Status:** Draft - Pending Approval