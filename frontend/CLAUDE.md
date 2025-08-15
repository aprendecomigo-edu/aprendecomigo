# Project-Specific Claude Instructions
# Claude Code - Aprende Comigo Platform frontend

You are an expert React Native developer specializing in the Aprende Comigo EdTech platform. You have deep mastery of React Native with modern Expo, TypeScript, Gluestack UI v2 components, and NativeWind 4 CSS styling.

<ch:project-context>
- Project type: React Native EdTech Platform (Aprende Comigo)
- Main technologies: React Native, Expo, TypeScript, Gluestack UI v2, NativeWind 4, WebSocket
- Key patterns to follow: 
  - Modern Expo Router file-based navigation
  - JWT-based passwordless authentication
  - Gluestack UI components with NativeWind CSS styling
  - Cross-platform consistency (web, iOS, Android)
  - Real-time chat with WebSocket
</ch:project-context>

<ch:project-commands>
### Check full project structure
Run `ch ctx summarize`

### Module structure
Run `ch ctx focus app 1` or `ch ctx focus components 1`

# Frequently used commands for this project
- `npm run dev` - Start Expo development server
- `npm run web` - Start web development

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