# ArariPRO Premium Theme - ThemetheBestJp1219

A premium dark/light theme with glassmorphism effects and neon accents, extracted from Arari-PRO and designed for Japanese business applications.

## Features

- **Dark/Light Mode**: Full theme support with CSS variables
- **Glassmorphism**: Beautiful glass effects for cards and overlays
- **Neon Accents**: Cyan (#00f2ea) and purple (#bd00ff) glow effects
- **Accessible**: WCAG compliant color contrast and focus states
- **Responsive**: Mobile-first design with all breakpoints
- **Animations**: Smooth micro-interactions and loading states
- **Japanese-Ready**: Optimized for Japanese text and Yen formatting

## Quick Start

### 1. Copy Files to Your Project

```bash
# Copy the theme folder to your project
cp -r ThemetheBestJp1219/ your-project/src/theme/
```

### 2. Update Tailwind Config

Replace your `tailwind.config.js` with `tailwind.config.theme.js`:

```javascript
// tailwind.config.js
import themeConfig from './src/theme/tailwind.config.theme.js';
export default themeConfig;
```

Or merge the configurations:

```javascript
// tailwind.config.js
import { theme } from './src/theme/tailwind.config.theme.js';

export default {
  // ... your config
  theme: {
    extend: {
      ...theme.extend,
      // your overrides
    }
  }
}
```

### 3. Import Global Styles

Add to your main CSS file or App entry:

```css
/* In your main CSS file */
@import './theme/styles/globals.css';
@import './theme/styles/animations.css';
@import './theme/styles/utilities.css';
```

### 4. Add Theme Provider (Optional)

For theme switching support:

```jsx
// App.jsx
import { ThemeProvider } from './theme/hooks/useTheme';

function App() {
  return (
    <ThemeProvider defaultTheme="dark">
      <YourApp />
    </ThemeProvider>
  );
}
```

### 5. Use Components

```jsx
import { Button, Card, CardHeader, CardTitle, Input } from './theme/components';

function MyComponent() {
  return (
    <Card hover>
      <CardHeader>
        <CardTitle>Welcome</CardTitle>
      </CardHeader>
      <CardContent>
        <Input placeholder="Enter text..." />
        <Button variant="gradient">Submit</Button>
      </CardContent>
    </Card>
  );
}
```

## File Structure

```
ThemetheBestJp1219/
  ├── components/           # React components
  │   ├── Button.jsx       # Button with variants
  │   ├── Card.jsx         # Card components
  │   ├── Input.jsx        # Input with validation
  │   ├── Badge.jsx        # Status badges
  │   ├── GlassCard.jsx    # Glassmorphism card
  │   ├── Skeleton.jsx     # Loading placeholders
  │   ├── Table.jsx        # Data table
  │   ├── Modal.jsx        # Dialog/modal
  │   ├── Alert.jsx        # Alert messages
  │   ├── Navigation.jsx   # Sidebar/header
  │   ├── Progress.jsx     # Progress indicators
  │   └── index.js         # All exports
  ├── styles/
  │   ├── globals.css      # CSS variables & base
  │   ├── animations.css   # Animation classes
  │   └── utilities.css    # Utility classes
  ├── hooks/
  │   ├── utils.js         # Utility functions
  │   └── useTheme.js      # Theme hook
  ├── examples/
  │   ├── DashboardExample.jsx
  │   └── FormExample.jsx
  ├── theme-tokens.json    # Design tokens (JSON)
  ├── tailwind.config.theme.js  # Tailwind config
  └── README.md            # This file
```

## Color System

### Semantic Colors (CSS Variables)

| Variable | Dark Mode | Light Mode | Usage |
|----------|-----------|------------|-------|
| `--background` | #0a0a0a | #fafafa | Page background |
| `--foreground` | #fafafa | #0a0a0a | Primary text |
| `--primary` | Cyan 500 | Blue 500 | Primary actions |
| `--secondary` | Slate 800 | Slate 100 | Secondary elements |
| `--muted` | Slate 800 | Slate 100 | Disabled/muted |
| `--accent` | Slate 800 | Slate 100 | Accent elements |
| `--destructive` | Red 600 | Red 500 | Destructive actions |

### Neon Colors

| Name | Hex | Usage |
|------|-----|-------|
| `neon-blue` | #00f2ea | Active states, highlights |
| `neon-purple` | #bd00ff | Gradients, accents |
| `neon-dark` | #0a0a0f | Deep backgrounds |

### Status Colors

```jsx
// Success
<Badge variant="success">Active</Badge>

// Warning
<Badge variant="warning">Pending</Badge>

// Danger
<Badge variant="danger">Error</Badge>

// Info
<Badge variant="info">New</Badge>
```

## Component Reference

### Button

```jsx
// Variants
<Button variant="default">Default</Button>
<Button variant="secondary">Secondary</Button>
<Button variant="outline">Outline</Button>
<Button variant="ghost">Ghost</Button>
<Button variant="destructive">Delete</Button>
<Button variant="success">Confirm</Button>
<Button variant="gradient">Premium</Button>
<Button variant="neon">Neon</Button>

// Sizes
<Button size="sm">Small</Button>
<Button size="default">Default</Button>
<Button size="lg">Large</Button>
<Button size="icon"><Icon /></Button>

// States
<Button isLoading>Loading...</Button>
<Button disabled>Disabled</Button>
```

### Card

```jsx
<Card hover gradient>
  <CardHeader>
    <CardTitle>Card Title</CardTitle>
    <CardDescription>Card description</CardDescription>
  </CardHeader>
  <CardContent>
    Content here
  </CardContent>
  <CardFooter>
    <Button>Action</Button>
  </CardFooter>
</Card>
```

### GlassCard

```jsx
// Default glass effect
<GlassCard>Content</GlassCard>

// Neo gradient effect
<GlassCard variant="neo">Premium Content</GlassCard>

// With shimmer on hover
<GlassCard shimmer>Hover me</GlassCard>
```

### Input

```jsx
// Basic input
<Input placeholder="Enter text..." />

// With label and error
<InputField
  label="Email"
  type="email"
  error="Invalid email"
  helperText="We'll never share your email"
  required
/>

// Search input with icon
<SearchInput placeholder="Search..." />
```

### Table

```jsx
<Table>
  <TableHeader>
    <TableRow>
      <TableHead sortable sorted="asc" onSort={handleSort}>Name</TableHead>
      <TableHead>Status</TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    <TableRow>
      <TableCell>John Doe</TableCell>
      <TableCell><Badge variant="success">Active</Badge></TableCell>
    </TableRow>
  </TableBody>
</Table>
```

### Modal

```jsx
<Modal isOpen={isOpen} onClose={handleClose} size="md">
  <ModalHeader onClose={handleClose}>
    <ModalTitle>Confirm Action</ModalTitle>
    <ModalDescription>This action cannot be undone.</ModalDescription>
  </ModalHeader>
  <ModalContent>
    Are you sure you want to proceed?
  </ModalContent>
  <ModalFooter>
    <Button variant="outline" onClick={handleClose}>Cancel</Button>
    <Button variant="destructive">Delete</Button>
  </ModalFooter>
</Modal>
```

### Skeleton Loading

```jsx
// Basic skeleton
<Skeleton className="h-4 w-[200px]" />

// Text lines
<SkeletonText lines={3} />

// Card skeleton
<SkeletonCard />

// Table skeleton
<SkeletonTable rows={5} columns={4} />

// Stats card skeleton
<SkeletonStatsCard />
```

### Progress

```jsx
// Linear progress
<Progress value={75} variant="neon" showLabel />

// Circular progress
<CircularProgress value={60} size={120} />

// Step progress
<StepProgress
  steps={['Upload', 'Process', 'Complete']}
  currentStep={1}
/>
```

## Utility Classes

### Glass Effects

```html
<!-- Glass background with blur -->
<div class="glass">Header content</div>

<!-- Glass card -->
<div class="glass-card">Card content</div>
```

### Text Gradients

```html
<!-- Cyan to purple gradient -->
<h1 class="text-gradient">Gradient Text</h1>

<!-- Gold gradient -->
<span class="text-gradient-gold">Premium</span>
```

### Animations

```html
<!-- Fade in animation -->
<div class="animate-fade-in">Fades in</div>

<!-- Slide from right -->
<div class="animate-slide-in-right">Slides in</div>

<!-- Glow pulse -->
<button class="animate-glow">Glowing button</button>

<!-- Shimmer loading -->
<div class="shimmer">Loading...</div>
```

### Hover Effects

```html
<!-- Scale on hover -->
<div class="hover-scale">Scales up</div>

<!-- Lift on hover -->
<div class="hover-lift">Lifts up</div>

<!-- Glow on hover -->
<button class="hover-glow">Glows</button>
```

## Theme Switching

```jsx
import { useTheme } from './theme/hooks/useTheme';

function ThemeToggle() {
  const { theme, toggleTheme, resolvedTheme } = useTheme();

  return (
    <button onClick={toggleTheme}>
      {resolvedTheme === 'dark' ? 'Light Mode' : 'Dark Mode'}
    </button>
  );
}
```

## Japanese Formatting Utilities

```jsx
import { formatYen, formatNumber, formatPercent } from './theme/hooks/utils';

// Currency: "¥1,234,567"
formatYen(1234567)

// Number: "1,234,567"
formatNumber(1234567)

// Percentage: "12.5%"
formatPercent(12.5)
```

## Accessibility

All components include:

- Proper ARIA labels and roles
- Keyboard navigation support
- Focus visible indicators
- Screen reader support
- Color contrast compliance (WCAG AA)

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Dependencies

For production use, install these packages:

```bash
npm install clsx tailwind-merge
```

Then update `hooks/utils.js`:

```javascript
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}
```

## Credits

Theme extracted from Arari-PRO by Universal Kikaku Co., Ltd.

## License

MIT License
