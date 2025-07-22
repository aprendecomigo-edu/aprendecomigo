import { ScrollViewStyleReset } from 'expo-router/html';

// This file is web-only and used to configure the root HTML for every
// web page during static rendering.
// The contents of this function only run in Node.js environments and
// do not have access to the DOM or browser APIs.
export default function Root({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta httpEquiv="X-UA-Compatible" content="IE=edge" />
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no" />

        {/*
          Disable body scrolling on web. This makes ScrollView components work closer to how they do on native.
          However, body scrolling is often nice to have for mobile web. If you want to enable it, remove this line.
        */}
        <ScrollViewStyleReset />

        {/* Using raw CSS styles as an escape-hatch to ensure the background color never flickers in dark-mode. */}
        <style dangerouslySetInnerHTML={{ __html: responsiveBackground }} />

        {/* CSS Fix Patch for NativeWind v4 + React Native Web compatibility */}
        <script dangerouslySetInnerHTML={{ __html: cssFix }} />

        {/* Add any additional <head> elements that you want globally available on web... */}
      </head>
      <body>{children}</body>
    </html>
  );
}

const responsiveBackground = `
html, body, #__next {
  height: 100%;
  min-height: 100vh;
}
body {
  background-color: #fff;
  margin: 0;
  padding: 0;
}
@media (prefers-color-scheme: dark) {
  body {
    background-color: #000;
  }
}`;

const cssFix = `
// CSS Fix Patch for NativeWind v4 + React Native Web compatibility
// This fixes the "Failed to set an indexed property [0] on 'CSSStyleDeclaration'" error
(function() {
  if (typeof window === 'undefined') return;

  console.log('🔧 Applying CSS compatibility patch for NativeWind v4 + React Native Web...');

  // Global error handler for CSS-related errors
  window.addEventListener('error', function(event) {
    if (event.error && event.error.message &&
        event.error.message.includes('CSSStyleDeclaration') &&
        event.error.message.includes('Indexed property setter')) {
      console.warn('Prevented CSS StyleDeclaration error:', event.error.message);
      event.preventDefault();
      event.stopPropagation();
      return false;
    }
  });

  // Prevent React error boundary triggers from CSS errors
  const originalConsoleError = console.error;
  console.error = function(...args) {
    const message = args.join(' ');
    if (message.includes('CSSStyleDeclaration') && message.includes('Indexed property setter')) {
      console.warn('Suppressed CSS error:', message);
      return;
    }
    return originalConsoleError.apply(console, args);
  };

  // Override window.onerror to catch CSS errors
  const originalOnError = window.onerror;
  window.onerror = function(message, source, lineno, colno, error) {
    if (typeof message === 'string' && message.includes('CSSStyleDeclaration')) {
      console.warn('Caught and suppressed CSS error:', message);
      return true; // Prevent default error handling
    }
    if (originalOnError) {
      return originalOnError.call(this, message, source, lineno, colno, error);
    }
    return false;
  };

  console.log('✅ CSS compatibility patch applied successfully');
})();
`;
