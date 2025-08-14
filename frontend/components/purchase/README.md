# Purchase System Components

This directory contains the complete purchase flow implementation for the Aprende Comigo tutoring platform. The system replaces mock purchase buttons with fully functional Stripe payment integration.

## Overview

The purchase system provides:
- **Pricing Plan Selection**: Interactive cards displaying available tutoring plans
- **Student Information Collection**: Form for authenticated and guest users
- **Stripe Payment Processing**: Secure payment handling with comprehensive error management
- **Student Balance Display**: Real-time balance and package information
- **Cross-platform Support**: Works on web, iOS, and Android with responsive design

## Component Architecture

### Core Components

#### `PurchaseFlow`
Main orchestrator component that manages the complete purchase process:
- State management for the entire flow
- Step-by-step navigation (plan selection → user info → payment → success)
- Error handling and recovery
- Progress tracking

#### `PricingPlanSelector`
Displays available pricing plans with:
- Automatic plan loading with caching
- Popular plan highlighting
- Responsive grid layout
- Loading and error states

#### `PricingPlanCard`
Individual plan display with:
- Plan details and features
- Price formatting
- Selection states
- Hover effects and animations

#### `StudentInfoForm`
Student information collection:
- Name and email validation
- Guest user support
- Integration with authenticated users
- Real-time validation feedback

#### `StripePaymentForm`
Secure payment processing:
- Stripe Elements integration
- PCI-compliant payment collection
- Real-time payment status
- Comprehensive error handling

#### `StudentBalanceCard`
Balance information display:
- Current hours remaining
- Active package status
- Upcoming expirations
- Purchase history

## API Integration

### Endpoints Used
- `GET /finances/api/pricing-plans/` - Active pricing plans
- `POST /finances/api/purchase/initiate/` - Purchase initiation
- `GET /finances/api/student-balance/` - Student balance info
- `GET /finances/api/stripe/config/` - Stripe configuration

### Data Flow
1. **Plan Selection**: Fetch pricing plans from backend
2. **Information Collection**: Validate user data and prepare purchase
3. **Payment Initiation**: Create Stripe payment intent
4. **Payment Processing**: Handle Stripe payment confirmation
5. **Completion**: Update balance and show success state

## Usage Examples

### Basic Purchase Flow
```tsx
import { PurchaseFlow } from '@/components/purchase';

function PurchasePage() {
  const handleComplete = (transactionId: number) => {
    console.log('Purchase completed:', transactionId);
    // Navigate to success page or dashboard
  };

  return (
    <PurchaseFlow 
      onPurchaseComplete={handleComplete}
      onCancel={() => router.push('/')}
    />
  );
}
```

### Pricing Display Only
```tsx
import { PricingPlanSelector } from '@/components/purchase';

function LandingPage() {
  const handlePlanSelect = (plan) => {
    // Navigate to full purchase flow
    router.push('/purchase');
  };

  return (
    <PricingPlanSelector 
      onPlanSelect={handlePlanSelect}
    />
  );
}
```

### Balance Information
```tsx
import { StudentBalanceCard } from '@/components/purchase';

function StudentDashboard() {
  return (
    <div>
      <h1>Your Account</h1>
      <StudentBalanceCard />
    </div>
  );
}
```

## Styling and Theming

All components use:
- **Gluestack UI** components for consistent design
- **NativeWind CSS** for responsive styling
- **Lucide React Native** icons for cross-platform compatibility
- **Tailwind CSS** classes for responsive layouts

### Responsive Design
- Mobile-first approach
- Breakpoint-aware layouts
- Touch-friendly interaction areas
- Platform-specific adaptations

## Error Handling

The system includes comprehensive error handling for:
- **Network Issues**: Connection timeouts and retries
- **Validation Errors**: Form validation with clear feedback
- **Payment Errors**: Stripe error handling with user-friendly messages
- **Server Errors**: Graceful degradation with retry options

## Security Features

- **PCI Compliance**: Stripe handles all payment data
- **Input Validation**: Client and server-side validation
- **CSRF Protection**: Built into API endpoints
- **Rate Limiting**: Purchase attempt throttling
- **Secure Headers**: Proper content security policies

## Testing

### Manual Testing Checklist
- [ ] Plan selection on different screen sizes
- [ ] Form validation with various inputs
- [ ] Payment flow with test cards
- [ ] Error scenarios (network failures, invalid cards)
- [ ] Guest vs authenticated user flows
- [ ] Cross-browser compatibility

### Test Cards (Stripe)
- **Success**: 4242 4242 4242 4242
- **Declined**: 4000 0000 0000 0002
- **Insufficient funds**: 4000 0000 0000 9995

## Performance Considerations

- **Lazy Loading**: Components load on demand
- **Caching**: Pricing plans cached for 1 hour
- **Optimistic Updates**: UI updates before API confirmation
- **Code Splitting**: Stripe components only load when needed

## Browser Support

- **Web**: Modern browsers with ES2015+ support
- **Mobile**: React Native WebView with JavaScript enabled
- **iOS**: Native iOS through Expo
- **Android**: Native Android through Expo

## Deployment Notes

### Environment Variables Required
```
EXPO_PUBLIC_STRIPE_PUBLIC_KEY=pk_test_...
EXPO_PUBLIC_API_URL=https://api.aprendecomigo.com/api
```

### Backend Dependencies
- Django with Stripe webhook endpoints configured
- PostgreSQL for transaction storage
- Redis for caching (optional but recommended)

## Troubleshooting

### Common Issues

**"Payment configuration not available"**
- Check Stripe public key is set correctly
- Verify backend Stripe configuration endpoint

**"Network connection error"**
- Check API_URL environment variable
- Verify backend server is running and accessible

**"Payment processing is only available on web platform"**
- Mobile payment processing requires native Stripe SDKs
- Consider implementing react-native-stripe-sdk for mobile

### Debugging

Enable debug logging:
```tsx
// In development
console.log('Purchase state:', purchaseState);
```

Check network requests in dev tools for API call failures.

## Future Enhancements

- **Mobile Native Payments**: Implement native Stripe SDKs
- **Subscription Management**: Cancel/modify subscription UI
- **Payment Methods**: Save cards for future purchases
- **Promotional Codes**: Discount code support
- **Multi-currency**: Support for different currencies
- **Accessibility**: Enhanced screen reader support
- **Error Boundaries**: Add React error boundaries for better error handling
- **Caching Strategy**: Implement pricing plan caching with TTL
- **Analytics**: Add purchase funnel analytics and conversion tracking