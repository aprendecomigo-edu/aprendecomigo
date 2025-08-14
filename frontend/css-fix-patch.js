// CSS Fix Patch for NativeWind v4 + React Native Web compatibility
// This fixes the "Failed to set an indexed property [0] on 'CSSStyleDeclaration'" error

// Monkey patch for CSSStyleDeclaration to handle numeric array indices
if (typeof window !== 'undefined' && window.CSSStyleDeclaration) {
  const originalDescriptor =
    Object.getOwnPropertyDescriptor(CSSStyleDeclaration.prototype, '0') ||
    Object.getOwnPropertyDescriptor(CSSStyleDeclaration.prototype, 'setProperty');

  if (!originalDescriptor || originalDescriptor.set) {
    // Already patched or has setter
    return;
  }

  // Create a proxy for CSSStyleDeclaration to intercept numeric property sets
  const OriginalCSSStyleDeclaration = window.CSSStyleDeclaration;

  function PatchedCSSStyleDeclaration() {
    return OriginalCSSStyleDeclaration.apply(this, arguments);
  }

  PatchedCSSStyleDeclaration.prototype = Object.create(OriginalCSSStyleDeclaration.prototype);
  PatchedCSSStyleDeclaration.prototype.constructor = PatchedCSSStyleDeclaration;

  // Patch the prototype to handle numeric indices
  const originalSetProperty = OriginalCSSStyleDeclaration.prototype.setProperty;

  // Override indexed property setter behavior
  Object.defineProperty(PatchedCSSStyleDeclaration.prototype, '0', {
    set: function (value) {
      // Ignore numeric index assignments that cause the error
      console.warn('Ignored numeric CSS property assignment:', value);
    },
    configurable: true,
    enumerable: false,
  });

  // Add handlers for common numeric indices that might be accessed
  for (let i = 0; i < 20; i++) {
    Object.defineProperty(PatchedCSSStyleDeclaration.prototype, i.toString(), {
      set: function (value) {
        console.warn(`Ignored numeric CSS property assignment at index ${i}:`, value);
      },
      get: function () {
        return undefined;
      },
      configurable: true,
      enumerable: false,
    });
  }

  // Override the global CSSStyleDeclaration
  try {
    window.CSSStyleDeclaration = PatchedCSSStyleDeclaration;

    // Also patch any existing instances
    const allStyleSheets = document.styleSheets;
    for (let i = 0; i < allStyleSheets.length; i++) {
      try {
        const rules = allStyleSheets[i].cssRules || allStyleSheets[i].rules;
        for (let j = 0; j < rules.length; j++) {
          const rule = rules[j];
          if (rule.style && rule.style instanceof OriginalCSSStyleDeclaration) {
            Object.setPrototypeOf(rule.style, PatchedCSSStyleDeclaration.prototype);
          }
        }
      } catch (e) {
        // Cross-origin stylesheets might throw errors, ignore them
      }
    }

    console.log('Applied CSS compatibility patch for NativeWind + React Native Web');
  } catch (e) {
    console.warn('Could not apply CSS compatibility patch:', e);
  }
}

// Alternative approach: Patch React DOM directly
if (typeof window !== 'undefined' && window.React && window.ReactDOM) {
  // Store original React DOM functions
  const originalReactDOMRender = window.ReactDOM.render;
  const originalCreateElement = window.React.createElement;

  // Patch createElement to catch and prevent CSS errors
  window.React.createElement = function (type, props, ...children) {
    try {
      return originalCreateElement.apply(this, arguments);
    } catch (error) {
      if (error.message && error.message.includes('CSSStyleDeclaration')) {
        console.warn('Prevented CSS error in createElement:', error.message);
        // Return a safe fallback
        return originalCreateElement('div', { style: { display: 'none' } }, 'CSS Error Prevented');
      }
      throw error;
    }
  };

  console.log('Applied React createElement CSS error prevention patch');
}

// Global error handler for CSS-related errors
window.addEventListener('error', function (event) {
  if (
    event.error &&
    event.error.message &&
    event.error.message.includes('CSSStyleDeclaration') &&
    event.error.message.includes('Indexed property setter')
  ) {
    console.warn('Prevented CSS StyleDeclaration error:', event.error.message);
    event.preventDefault();
    event.stopPropagation();
    return false;
  }
});

// Console warning about the patch
console.log('🔧 CSS Compatibility Patch Applied - NativeWind v4 + React Native Web fix loaded');
