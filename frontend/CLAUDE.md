# Project-Specific Claude Instructions
# Claude Code - Aprende Comigo Platform frontend

You are an expert React Native developer specializing in the Aprende Comigo EdTech platform. You have deep mastery of React Native with modern Expo, TypeScript, Gluestack UI v2 components, and NativeWind 4 CSS styling.

<ch:project-context>
- Project type: React Native EdTech Platform (Aprende Comigo)
- Main technologies: React Native, Expo SDK 53, React 19, TypeScript, Gluestack UI v2, NativeWind 4, WebSocket
- Key patterns to follow: 
  - Modern Expo Router file-based navigation
  - JWT-based passwordless authentication
  - Gluestack UI components with NativeWind CSS styling
  - Cross-platform consistency (web, iOS, Android)
  - Real-time chat with WebSocket
- React 19 Compatibility: Web bundling uses production builds due to react-refresh compatibility issues
</ch:project-context>

<ch:project-commands>
### Check full project structure
Run `ch ctx summarize`

### Module structure
Run `ch ctx focus app 1` or `ch ctx focus components 1`

# Frequently used commands for this project
- `npm run dev` - Start Expo development server (mobile only - iOS/Android)
- `npm run dev:mobile` - Start mobile development (alias for dev)
- `npm run build:web` - Build web app for testing (due to React 19 compatibility)
- `npm run preview:web` - Serve built web app locally at http://localhost:3000

## React 19 + Expo SDK 53 Development Workflow

### Background
React 19 introduced module structure changes that are incompatible with react-refresh v0.14.2, causing web bundling issues. Our solution maintains full mobile development experience while using production-only web builds.

### Mobile Development (Unchanged - Full Features)
```bash
npm run dev          # Start mobile dev server (iOS + Android)
npm run dev:mobile   # Same as above
```
- ✅ Hot reload and fast refresh
- ✅ Real-time debugging
- ✅ Full development experience
- ✅ WebSocket support
- ✅ All native modules available

### Web Development (Production Build Workflow)
```bash
# Single command workflow
npm run build:web && npm run preview:web

# Or step by step:
npm run build:web    # Build web app (~30-60s)
npm run preview:web  # Serve at http://localhost:3000
```

#### Environment-Specific Web Builds
```bash
npm run build:web            # Development environment
npm run build:web:staging    # Staging environment  
npm run build:web:prod       # Production environment
```

### Development Strategy Recommendations
1. **Mobile First**: Develop new features on mobile with hot reload
2. **Web Verification**: Test web compatibility after mobile implementation
3. **Cross-Platform Components**: Use platform detection utilities from `utils/platform.ts`
4. **Responsive Design**: Ensure components work across all screen sizes

### Platform Detection & Environment Variables
The `utils/platform.ts` file provides enhanced platform detection:
```typescript
import { 
  isWeb, isMobile, isWebBuild, 
  platformFeatures, buildEnv 
} from '@/utils/platform';

// Platform-specific rendering
if (platformFeatures.supportsHotReload) {
  // Mobile development features
}

// Environment-aware logic
if (buildEnv === 'production') {
  // Production-specific behavior
}
```

### Key Technical Changes
- **Metro Config**: Enhanced with platform-specific optimizations
- **Environment Variables**: `EXPO_PUBLIC_PLATFORM=web` for web builds
- **Build Process**: NativeWind CSS generation integrated
- **Error Handling**: Helpful messages when attempting web dev server

### Performance Considerations
- **Web Build Time**: ~30-60 seconds per change
- **Mobile Development**: Unchanged performance (instant hot reload)
- **Bundle Size**: Optimized with platform-specific configurations
- **Production Ready**: Web builds are production-optimized by default

### Known Issues & Solutions
- **Missing Dependencies**: Some `@gluestack-ui/*` packages may need to be installed as they are encountered during development
- **Build Failures**: If you encounter missing package errors, install them with `npm install @gluestack-ui/[package-name]`
- **TypeScript Errors**: Existing TS errors in tests/QA files don't affect build process
- **App Config**: Fixed `__DEV__` reference in `app.config.js` for web builds compatibility

# Typescript Helpers
- `ch ts deps` - Node.js/TypeScript analysis
- `ch ts qi` - Quick install with appropriate package manager
- `ch ts build` - Run build with error checking
- `ch ts test` - Run tests
- `ch ts lint` - Run linter
- `ch ts tc` - Run TypeScript type checking
- `ch ts analyze|structure` - Analyze project structure
</ch:project-commands>

<ch:project-notes>

## Development Standards
1. **TypeScript Excellence**: Strict typing for all components, no 'any' types
2. **Component Architecture**: Small, focused components following single responsibility. Use composition over inheritance. Implement proper prop drilling prevention with context when needed.
3. **Styling**: Gluestack UI v2 + NativeWind 4 CSS. Ensure responsive design that works across all screen sizes. Follow the platform's design system for consistency.
4. **Performance**: React.memo for expensive components, use useMemo and useCallback appropriately, optimize list rendering with FlashList or FlatList, lazy load components when beneficial
5. **State Management**: Local state for component-specific data, React Context for cross-component state, and consider the existing API client patterns for server state.
6. **Error Handling**: Error boundaries, user-friendly messages, handle network failures gracefully, and ensure offline functionality where appropriate
7. **Testability**: Separate view from business logic and app state. Keep your business logic testing (which shouldn’t rely on your React components) independent of the components themselves, whose job is primarily rendering your app’s UI.

## User Roles & Features
- Multi-role management: School Owner, Teacher, Student, Parent
- Real-time tutoring with WebSocket support
- Payment processing and teacher compensation
- Cross-institutional functionality for teachers

## Key Development Practices
- Write self-documenting code with clear variable and function names
- Follow existing code patterns in the codebase
- Analyze existing patterns before implementing
- Ensure cross-platform consistency (web, iOS, Android)
- Implement proper loading states and error handling
- Write self-documenting code with JSDoc for complex logic
- Ensure accessibility with ARIA labels and keyboard navigation
</ch:project-notes>

## Helper Scripts Available

You have access to efficient helper scripts that streamline common development tasks:

**🚀 Quick Start:**
```bash
chp  # Run this first! Provides comprehensive project analysis
```
Also, `ch ts analyze|structure` - For deeper project structure

**🔍 Common Tasks (more efficient than manual commands):**
- `chs find-code "pattern"` - Fast code search (better than grep)
- `ch m read-many file1 file2` - Batch file reading (saves tokens)
- `chg quick-commit "msg"` - Complete git workflow in one command
- `ch ctx for-task "description"` - Generate focused context for specific tasks

These helpers bundle multiple operations into single commands, providing:
- Structured output optimized for analysis
- Automatic error handling
- Token-efficient responses
- Consistent patterns across tech stacks

Run `ch help` to see all available commands and categories.