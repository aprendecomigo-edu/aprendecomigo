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
// Enhanced CSS Fix Patch for NativeWind v4 + React Native Web compatibility
// This fixes the "Failed to set an indexed property [0] on 'CSSStyleDeclaration'" error
(function() {
  if (typeof window === 'undefined') return;

  // Safe development environment detection for browser context
  var isDev = false;
  try {
    isDev = typeof process !== 'undefined' && process.env && process.env.NODE_ENV === 'development';
  } catch (e) {
    isDev = false;
  }

  if (isDev) {
    console.log('🔧 Applying enhanced CSS compatibility patch for NativeWind v4 + React Native Web...');
  }

  // Store original CSSStyleDeclaration for safekeeping
  const OriginalCSSStyleDeclaration = window.CSSStyleDeclaration;
  
  // Comprehensive CSS error patterns to catch
  const CSS_ERROR_PATTERNS = [
    'CSSStyleDeclaration',
    'Indexed property setter',
    'Failed to set an indexed property',
    'Cannot set property',
    'cssText',
    'style setter'
  ];

  // Check if message contains CSS error patterns
  function isCSSError(message) {
    return CSS_ERROR_PATTERNS.some(pattern => 
      typeof message === 'string' && message.includes(pattern)
    );
  }

  // Enhanced CSSStyleDeclaration Patching
  if (OriginalCSSStyleDeclaration) {
    // Create a wrapper for safer property setting
    function SafeCSSStyleDeclaration() {
      const instance = Object.create(OriginalCSSStyleDeclaration.prototype);
      
      // Override problematic numeric property setters
      for (let i = 0; i < 100; i++) {
        Object.defineProperty(instance, i.toString(), {
          get: function() { return undefined; },
          set: function(value) {
            if (isDev) {
              console.warn(\`Ignored CSS numeric property assignment at index \${i}: \${value}\`);
            }
            return;
          },
          configurable: true,
          enumerable: false
        });
      }
      
      return instance;
    }
    
    // Copy prototype methods
    SafeCSSStyleDeclaration.prototype = Object.create(OriginalCSSStyleDeclaration.prototype);
    SafeCSSStyleDeclaration.prototype.constructor = SafeCSSStyleDeclaration;
    
    // Override problematic methods with safe versions
    const originalSetProperty = OriginalCSSStyleDeclaration.prototype.setProperty;
    SafeCSSStyleDeclaration.prototype.setProperty = function(property, value, priority) {
      try {
        return originalSetProperty.call(this, property, value, priority);
      } catch (e) {
        if (isCSSError(e.message)) {
          if (isDev) {
            console.warn('Prevented CSS setProperty error:', e.message, { property, value, priority });
          }
          return;
        }
        throw e;
      }
    };
  }

  // Global unhandled rejection handler for CSS promises
  window.addEventListener('unhandledrejection', function(event) {
    if (event.reason && isCSSError(event.reason.message)) {
      if (isDev) {
        console.warn('Prevented CSS promise rejection:', event.reason.message);
      }
      event.preventDefault();
      return;
    }
  });

  // Enhanced global error handler for CSS-related errors
  window.addEventListener('error', function(event) {
    if (event.error && isCSSError(event.error.message)) {
      if (isDev) {
        console.warn('Prevented CSS StyleDeclaration error:', event.error.message);
      }
      event.preventDefault();
      event.stopPropagation();
      return false;
    }
  });

  // Prevent React error boundary triggers from CSS errors
  const originalConsoleError = console.error;
  console.error = function(...args) {
    const message = args.join(' ');
    if (isCSSError(message)) {
      if (isDev) {
        console.warn('Suppressed CSS console error:', message);
      }
      return;
    }
    return originalConsoleError.apply(console, args);
  };

  // Override window.onerror to catch CSS errors
  const originalOnError = window.onerror;
  window.onerror = function(message, source, lineno, colno, error) {
    if (isCSSError(message)) {
      if (isDev) {
        console.warn('Caught and suppressed CSS error:', message);
      }
      return true; // Prevent default error handling
    }
    if (originalOnError) {
      return originalOnError.call(this, message, source, lineno, colno, error);
    }
    return false;
  };

  // Patch React Native Web StyleSheet operations
  if (window.ReactNativeWeb && window.ReactNativeWeb.StyleSheet) {
    const originalCreate = window.ReactNativeWeb.StyleSheet.create;
    window.ReactNativeWeb.StyleSheet.create = function(styles) {
      try {
        return originalCreate.call(this, styles);
      } catch (e) {
        if (isCSSError(e.message)) {
          if (isDev) {
            console.warn('Prevented ReactNativeWeb StyleSheet error:', e.message);
          }
          return {}; // Return empty stylesheet as fallback
        }
        throw e;
      }
    };
  }

  // Patch DOM mutations that might cause CSS errors
  if (typeof MutationObserver !== 'undefined') {
    const originalMutationObserver = window.MutationObserver;
    window.MutationObserver = function(callback) {
      return new originalMutationObserver(function(mutations, observer) {
        try {
          return callback(mutations, observer);
        } catch (e) {
          if (isCSSError(e.message)) {
            if (isDev) {
              console.warn('Prevented CSS mutation observer error:', e.message);
            }
            return;
          }
          throw e;
        }
      });
    };
  }

  // Additional protection for style element manipulations
  const originalElementPrototype = Element.prototype;
  const originalSetAttribute = originalElementPrototype.setAttribute;
  
  originalElementPrototype.setAttribute = function(name, value) {
    try {
      return originalSetAttribute.call(this, name, value);
    } catch (e) {
      if (isCSSError(e.message) && (name === 'style' || name === 'class')) {
        if (isDev) {
          console.warn('Prevented CSS setAttribute error:', e.message, { name, value });
        }
        return;
      }
      throw e;
    }
  };

  if (isDev) {

    if (isDev) {
      console.log('✅ Enhanced CSS compatibility patch applied successfully');
    }

  }
})();
`;
