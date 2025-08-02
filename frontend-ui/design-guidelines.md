# Aprende Comigo - Design System Guidelines

**Last Updated:** August 2, 2025  
**Version:** 1.0  

This document defines the complete design system for the Aprende Comigo EdTech platform, establishing consistent visual patterns that work seamlessly across web, iOS, and Android platforms.

## Table of Contents

1. [Design Philosophy](#design-philosophy)
2. [Color System](#color-system)
3. [Gradient Patterns](#gradient-patterns)
4. [Glassmorphism Effects](#glassmorphism-effects)
5. [Card Patterns](#card-patterns)
6. [Typography Patterns](#typography-patterns)
7. [Background Patterns](#background-patterns)
8. [Interactive States](#interactive-states)
9. [Cross-Platform Usage](#cross-platform-usage)
10. [Implementation Examples](#implementation-examples)

## Design Philosophy

The Aprende Comigo design system emphasizes:

- **🎨 Modern Aesthetics**: Contemporary gradients and glass effects for premium feel
- **🔄 Consistency**: Identical visual language across all platforms
- **⚡ Performance**: Optimized patterns that work efficiently on all devices
- **🎯 Accessibility**: High contrast and clear visual hierarchy
- **📱 Responsive**: Seamless adaptation from mobile to desktop

## Color System

### Brand Color Palette

Our color system is built on the updated brand colors that reflect the landing page aesthetic:

#### Primary Colors
- **Electric Blue** (`#0EA5E9`) - Main brand color for primary actions
- **Deep Blue** (`#0284C7`) - Hover and active states
- **Cyan Flash** (`#38BDF8`) - Light accent variants

#### Accent Colors
- **Golden Orange** (`#F59E0B`) - Primary accent color
- **Burnt Orange** (`#F97316`) - Secondary accent color
- **Neon Magenta** (`#D946EF`) - Tertiary accent color

#### Neutral Colors
- **Light Gray** (`#F3F4F6`) - Background and subtle elements

## Gradient Patterns

### 🎨 Gradient System

Our gradient system provides consistent, beautiful color transitions that work across all platforms.

#### Primary Gradients

| **Pattern Name** | **Class Name** | **CSS Definition** | **Use Cases** |
|------------------|----------------|-------------------|---------------|
| **Primary Gradient** | `bg-gradient-primary` | `linear-gradient(135deg, #f59e0b, #38bdf8)` | Text gradients, hero elements, brand accents |
| **Accent Gradient** | `bg-gradient-accent` | `linear-gradient(135deg, #0ea5e9, #d946ef)` | Headlines, call-to-action text, key messaging |
| **Accent Dark Gradient** | `bg-gradient-accent-dark` | `linear-gradient(135deg, #f97316, #38bdf8)` | Secondary headings, button gradients |
| **Subtle Gradient** | `bg-gradient-subtle` | `linear-gradient(135deg, #f3f4f6 60%, #f59e0b 100%)` | Card backgrounds, section dividers |

#### Background Gradients

| **Pattern Name** | **Class Name** | **CSS Definition** | **Use Cases** |
|------------------|----------------|-------------------|---------------|
| **Page Background** | `bg-gradient-page` | `linear-gradient(135deg, #f8fafc 0%, #e2e8f0 50%, #f1f5f9 100%)` | Full page backgrounds, main content areas |
| **Section Light** | `bg-gradient-section-light` | `linear-gradient(to-br, from-gray-50, to-blue-50)` | Section backgrounds, content areas |
| **Dark Background** | `bg-gradient-dark` | `linear-gradient(to-br, from-gray-900, via-black, to-gray-800)` | Dark sections, footer backgrounds |

### Usage Examples

#### Text Gradients
```typescript
// Landing Page HTML
<h1 class="text-4xl font-bold">
  <span class="bg-gradient-primary">Aprende Comigo</span>
</h1>

// React Native
<Text className="text-4xl font-bold">
  <Text className="text-gradient-primary">Aprende Comigo</Text>
</Text>
```

#### Background Gradients
```typescript
// Landing Page HTML
<section class="bg-gradient-page min-h-screen">
  <div class="bg-gradient-subtle p-8 rounded-2xl">
    Content
  </div>
</section>

// React Native
<View className="bg-gradient-page min-h-screen">
  <View className="bg-gradient-subtle p-8 rounded-2xl">
    Content
  </View>
</View>
```

## Glassmorphism Effects

### 🪟 Glass Effect System

Glassmorphism creates depth and modern visual appeal through transparency and blur effects.

#### Glass Patterns

| **Pattern Name** | **Class Name** | **Properties** | **Use Cases** |
|------------------|----------------|----------------|---------------|
| **Glass Navigation** | `glass-nav` | `rgba(255,255,255,0.9) + blur(20px) + subtle border` | Navigation bars, headers, floating menus |
| **Glass Container** | `glass-container` | `rgba(255,255,255,0.8) + blur(10px) + subtle border` | Content cards, modal backgrounds |
| **Glass Light** | `glass-light` | `rgba(255,255,255,0.6) + blur(8px) + minimal border` | Badges, tags, subtle overlays |
| **Glass Strong** | `glass-strong` | `rgba(255,255,255,0.95) + blur(25px) + defined border` | Important modals, confirmation dialogs |

#### Technical Specifications

```css
/* Glass Navigation */
.glass-nav {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

/* Glass Container */
.glass-container {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05);
}

/* Glass Light */
.glass-light {
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.15);
}
```

### Usage Examples

```typescript
// Landing Page HTML
<nav class="glass-nav w-full rounded-2xl p-4">
  <div class="flex items-center justify-between">
    <span class="bg-gradient-primary font-brand">aprendecomigo</span>
    <button class="glass-light px-4 py-2 rounded-full">
      Sign Up
    </button>
  </div>
</nav>

// React Native
<View className="glass-nav w-full rounded-2xl p-4">
  <View className="flex-row items-center justify-between">
    <Text className="bg-gradient-primary font-brand">aprendecomigo</Text>
    <Pressable className="glass-light px-4 py-2 rounded-full">
      <Text>Sign Up</Text>
    </Pressable>
  </View>
</View>
```

## Card Patterns

### 🎯 Card Component System

Cards provide structured content containers with consistent styling and interactive behavior.

#### Card Types

| **Pattern Name** | **Class Name** | **Design Characteristics** | **Use Cases** |
|------------------|----------------|---------------------------|---------------|
| **Hero Card** | `hero-card` | White gradient + shadow + transform on hover | Process steps, feature highlights, call-to-action cards |
| **Feature Card** | `feature-card` | Clean background + border + hover elevation | Feature grid items, service descriptions |
| **Feature Card Gradient** | `feature-card-gradient` | Subtle gradient + border + smooth transitions | Premium features, highlighted content |
| **Glass Card** | `glass-card` | Glassmorphism + rounded corners + shadow | Modern overlays, floating content |

#### Technical Specifications

```css
/* Hero Card */
.hero-card {
  background: linear-gradient(135deg, #ffffff 0%, #f9fafb 100%);
  border: 1px solid #e5e7eb;
  border-radius: 1.5rem;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.hero-card:hover {
  transform: translateY(-6px) scale(1.02);
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

/* Feature Card Gradient */
.feature-card-gradient {
  background: linear-gradient(135deg, #f3f4f6 60%, #f59e0b 100%);
  border: 1px solid #e2e8f0;
  border-radius: 1.5rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.feature-card-gradient:hover {
  transform: translateY(-4px);
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
  border-color: #10b981;
}
```

### Usage Examples

```typescript
// Landing Page HTML
<div class="hero-card p-8 transform lg:-rotate-3 lg:hover:rotate-0">
  <div class="bg-emerald-100 p-4 rounded-2xl mb-6 w-fit">
    <div class="w-8 h-8 bg-emerald-500 rounded-lg flex items-center justify-center">
      <span class="text-white font-bold">1</span>
    </div>
  </div>
  <h4 class="font-bold text-xl mb-3">Configure ou Junte-se</h4>
  <p class="text-gray-600 leading-relaxed">Description text here...</p>
</div>

// React Native
<View className="hero-card p-8">
  <View className="bg-emerald-100 p-4 rounded-2xl mb-6 w-fit">
    <View className="w-8 h-8 bg-emerald-500 rounded-lg items-center justify-center">
      <Text className="text-white font-bold">1</Text>
    </View>
  </View>
  <Text className="font-bold text-xl mb-3">Configure ou Junte-se</Text>
  <Text className="text-gray-600 leading-relaxed">Description text here...</Text>
</View>
```

## Typography Patterns

### 📝 Text Treatment System

Typography patterns provide consistent text styling that enhances readability and visual hierarchy.

#### Font Families

| **Class Name** | **Font Stack** | **Use Cases** |
|----------------|----------------|---------------|
| `font-brand` | "Kirang Haerang", system-ui | Logo, brand elements, decorative text |
| `font-primary` | "Work Sans", sans-serif | Headlines, navigation, primary text |
| `font-body` | "Poppins", sans-serif | Body text, descriptions, content |
| `font-mono` | "SF Mono", Monaco, "Cascadia Code", monospace | Code, technical text, data |

#### Typography Scale with Gradients

```typescript
// Gradient Headlines
<h1 className="text-4xl md:text-6xl font-black leading-tight">
  <span className="bg-gradient-primary">Primary Headline</span>
</h1>

<h2 className="text-3xl md:text-4xl font-bold">
  <span className="bg-gradient-accent">Secondary Headline</span>
</h2>

// Brand Typography
<span className="text-2xl font-brand bg-gradient-primary">
  aprendecomigo
</span>

// Body Text with Accents
<p className="text-gray-600 text-xl leading-relaxed">
  Regular text with <span className="bg-gradient-accent-dark font-semibold">gradient highlights</span>
</p>
```

## Background Patterns

### 🌅 Background System

Background patterns create visual depth and establish the overall aesthetic foundation.

#### Page Backgrounds

| **Pattern Name** | **Class Name** | **Visual Effect** | **Use Cases** |
|------------------|----------------|------------------|---------------|
| **Main Page** | `bg-gradient-page` | Subtle gray gradient | Main content areas, landing pages |
| **Section Light** | `bg-gradient-section-light` | Gray to blue transition | Content sections, card containers |
| **Dark Section** | `bg-gradient-dark` | Dark gradient with overlays | Footer, dark mode sections, CTAs |

#### Overlay Patterns

```css
/* Dark section with colored overlay */
.bg-gradient-dark {
  background: linear-gradient(to-br, from-gray-900, via-black, to-gray-800);
  position: relative;
}

.bg-gradient-dark::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(to-br, from-emerald-500/10, to-purple-500/10);
  pointer-events: none;
}
```

## Interactive States

### ⚡ Interaction Design System

Interactive states provide clear feedback and enhance user experience across all platforms.

#### Hover States (Web)

```css
/* Button Hover */
.btn-primary:hover {
  background: linear-gradient(135deg, #d97706, #2563eb);
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
}

/* Card Hover */
.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
}
```

#### Press States (Native)

```css
/* Button Press */
.btn-primary:active {
  transform: scale(0.98);
  opacity: 0.9;
}

/* Card Press */
.feature-card:active {
  transform: scale(0.99);
  opacity: 0.95;
}
```

#### Loading States

```typescript
// Loading Button
<Pressable className={cn(
  "bg-gradient-primary px-8 py-4 rounded-full",
  isLoading && "opacity-70 cursor-not-allowed"
)}>
  {isLoading ? (
    <ActivityIndicator color="white" />
  ) : (
    <Text className="text-white font-bold">Continue</Text>
  )}
</Pressable>
```

## Cross-Platform Usage

### 🔄 Platform Consistency

#### HTML/CSS (Landing Page)
```html
<nav class="glass-nav w-full shadow-xl rounded-2xl">
  <div class="bg-gradient-primary">Brand Text</div>
  <button class="hero-card p-4">Action</button>
</nav>
```

#### React Native (Mobile App)
```typescript
<View className="glass-nav w-full shadow-xl rounded-2xl">
  <Text className="bg-gradient-primary">Brand Text</Text>
  <Pressable className="hero-card p-4">
    <Text>Action</Text>
  </Pressable>
</View>
```

### Platform-Specific Considerations

#### Web-Only Features
- `cursor-pointer` for interactive elements
- `hover:` states for mouse interactions
- Complex `box-shadow` effects

#### Native-Only Features
- `active:` states for touch interactions
- Platform-specific shadows (iOS vs Android)
- Safe area handling

#### Shared Features
- All gradient patterns work identically
- Glass effects adapt automatically
- Color system is fully consistent

## Implementation Examples

### 🚀 Complete Examples

#### Modern Authentication Card

```typescript
// Landing Page HTML
<div class="glass-container max-w-md mx-auto p-8 rounded-3xl">
  <h2 class="text-3xl font-bold text-center mb-8">
    <span class="bg-gradient-accent">Sign in to your account</span>
  </h2>
  
  <form class="space-y-6">
    <div class="glass-light p-4 rounded-xl">
      <input type="email" placeholder="Email" 
             class="w-full bg-transparent outline-none" />
    </div>
    
    <button class="w-full bg-gradient-primary text-white py-4 rounded-xl font-bold
                   hover:shadow-xl transition-all">
      Sign In
    </button>
  </form>
</div>

// React Native
<View className="glass-container max-w-md mx-auto p-8 rounded-3xl">
  <Text className="text-3xl font-bold text-center mb-8">
    <Text className="bg-gradient-accent">Sign in to your account</Text>
  </Text>
  
  <View className="space-y-6">
    <View className="glass-light p-4 rounded-xl">
      <TextInput placeholder="Email" 
                 className="w-full bg-transparent" 
                 placeholderTextColor="#666" />
    </View>
    
    <Pressable className="w-full bg-gradient-primary py-4 rounded-xl
                         active:scale-98 transition-all">
      <Text className="text-white text-center font-bold">Sign In</Text>
    </Pressable>
  </View>
</View>
```

#### Feature Showcase Section

```typescript
// Landing Page HTML
<section class="bg-gradient-page py-20">
  <div class="max-w-6xl mx-auto px-8">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-bold mb-6">
        <span class="bg-gradient-accent">Amazing Features</span>
      </h2>
    </div>
    
    <div class="grid md:grid-cols-2 gap-8">
      <div class="feature-card-gradient rounded-3xl p-8 group">
        <div class="bg-blue-100 p-4 rounded-2xl mb-6 w-fit 
                    group-hover:scale-110 transition-transform">
          <span class="text-3xl">🚀</span>
        </div>
        <h3 class="font-bold text-xl mb-4">Fast Performance</h3>
        <p class="text-gray-600 leading-relaxed">
          Lightning-fast experience across all platforms.
        </p>
      </div>
    </div>
  </div>
</section>

// React Native
<View className="bg-gradient-page py-20">
  <View className="max-w-6xl mx-auto px-8">
    <View className="text-center mb-16">
      <Text className="text-4xl font-bold mb-6">
        <Text className="bg-gradient-accent">Amazing Features</Text>
      </Text>
    </View>
    
    <View className="grid md:grid-cols-2 gap-8">
      <View className="feature-card-gradient rounded-3xl p-8 group">
        <View className="bg-blue-100 p-4 rounded-2xl mb-6 w-fit">
          <Text className="text-3xl">🚀</Text>
        </View>
        <Text className="font-bold text-xl mb-4">Fast Performance</Text>
        <Text className="text-gray-600 leading-relaxed">
          Lightning-fast experience across all platforms.
        </Text>
      </View>
    </View>
  </View>
</View>
```

## Design Token Reference

### Quick Reference Table

| **Category** | **Pattern** | **Class Name** | **Primary Use** |
|--------------|-------------|----------------|-----------------|
| **Gradients** | Primary | `bg-gradient-primary` | Brand text, key elements |
| **Gradients** | Accent | `bg-gradient-accent` | Headlines, CTAs |
| **Gradients** | Page | `bg-gradient-page` | Background areas |
| **Glass** | Navigation | `glass-nav` | Headers, navbars |
| **Glass** | Container | `glass-container` | Content cards |
| **Cards** | Hero | `hero-card` | Feature highlights |
| **Cards** | Feature | `feature-card-gradient` | Grid items |
| **Typography** | Brand | `font-brand` | Logo, brand text |
| **Typography** | Primary | `font-primary` | Headlines |
| **Typography** | Body | `font-body` | Content text |

---

## Implementation Notes

### ⚠️ Important Considerations

1. **Performance**: All patterns are optimized for cross-platform performance
2. **Accessibility**: High contrast ratios maintained in all color combinations  
3. **Responsive**: All patterns adapt to different screen sizes automatically
4. **Browser Support**: Fallbacks provided for older browsers
5. **Dark Mode**: All patterns support automatic dark mode variants

### 🔧 Next Steps

1. Implement these patterns in `config.ts` and `tailwind.config.js`
2. Test across web, iOS, and Android platforms
3. Update existing components to use standardized patterns
4. Create component library examples using these patterns

---

**Remember**: Consistency is key. Always use the documented class names and avoid custom implementations that deviate from this system.

For implementation details, see:
- [Styling Guidelines](./styling-guidelines.md)
- [Cross-Platform Component Guidelines](./components/ui/GUIDELINES.md)