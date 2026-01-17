# YuKyu Frontend Modular Structure

## Overview

This directory contains the reorganized frontend code following a modular architecture pattern.
The code is designed to work alongside the existing `app.js` for gradual migration.

## Directory Structure

```
static/src/
├── index.js              # Entry point - exports all modules
├── README.md             # This documentation
│
├── config/
│   └── constants.js      # API URLs, colors, configuration
│
├── store/
│   └── state.js          # Global state management with Observer pattern
│
├── pages/
│   ├── index.js          # Page registry and exports
│   ├── Dashboard.js      # Dashboard view with KPIs and charts
│   ├── Employees.js      # Employee list and management
│   ├── LeaveRequests.js  # Leave request workflow
│   ├── Analytics.js      # Statistics and reports
│   ├── Compliance.js     # 5-day compliance check
│   ├── Notifications.js  # Notification center
│   └── Settings.js       # User and system settings
│
└── components/           # (Existing) Reusable UI components
    ├── Form.js
    ├── Modal.js
    └── Table.js
```

## Usage

### Method 1: Import as ES6 Modules

```html
<script type="module">
    import YuKyuApp, { Dashboard, State } from '/static/src/index.js';

    // Initialize
    await YuKyuApp.init();

    // Navigate to a page
    YuKyuApp.navigate('employees');

    // Access state
    const currentState = State.getState();
</script>
```

### Method 2: Integrate with Legacy App

```javascript
// In app.js or after it loads
import { integrateWithLegacyApp } from '/static/src/index.js';

// This extends the existing App object with new modules
integrateWithLegacyApp(window.App);

// Now you can use:
App.pages.Dashboard.render();
App.State.getState();
```

### Method 3: Import Individual Modules

```javascript
import { Dashboard } from '/static/src/pages/Dashboard.js';
import { getState, setState } from '/static/src/store/state.js';
import { API_BASE_URL, CHART_COLORS } from '/static/src/config/constants.js';

// Initialize dashboard
Dashboard.init();

// Render when needed
Dashboard.render();

// Access state
const employees = getState().data;
```

## Module Documentation

### State (`store/state.js`)

Global state management with Observer pattern.

```javascript
import {
    getState,           // Get current state
    setState,           // Update state (triggers subscribers)
    subscribe,          // Subscribe to state changes
    getFilteredData,    // Get employees filtered by year
    getFactoryStats     // Get factory statistics
} from '/static/src/store/state.js';

// Subscribe to changes
const unsubscribe = subscribe((newState, prevState) => {
    console.log('State changed:', newState);
}, ['year', 'data']); // Optional: only watch specific keys

// Later: unsubscribe when done
unsubscribe();
```

### Constants (`config/constants.js`)

Application configuration.

```javascript
import {
    API_BASE_URL,       // '/api'
    ENDPOINTS,          // All API endpoints
    VIEW_TITLES,        // Page title mapping
    CHART_COLORS,       // Chart color palette
    BADGE_CLASSES,      // CSS class mappings
    ANIMATION_DURATIONS // Animation timings
} from '/static/src/config/constants.js';
```

### Pages

Each page module exports:

- `init()` - Initialize the page (subscriptions, setup)
- `render()` - Render the page content
- `cleanup()` - Clean up when leaving the page
- Page-specific functions

Example with Dashboard:

```javascript
import { Dashboard } from '/static/src/pages/Dashboard.js';

// Initialize (call once)
Dashboard.init();

// Render (call when navigating to page)
Dashboard.render();

// Update specific components
Dashboard.updateComplianceGauge(85, 42, 50);
Dashboard.updateExpiringDays(employees);

// Clean up when leaving
Dashboard.cleanup();
```

## Compatibility

This modular structure is designed for **gradual migration**:

1. The existing `app.js` continues to work unchanged
2. New modules can be imported alongside existing code
3. The `integrateWithLegacyApp()` function bridges old and new code
4. Pages can be migrated one at a time

## Browser Support

Requires browsers with ES6 module support:
- Chrome 61+
- Firefox 60+
- Safari 11+
- Edge 16+

For older browsers, use a bundler like Vite or webpack.

## Development

### Adding a New Page

1. Create `pages/NewPage.js`:

```javascript
import { getState, subscribe } from '../store/state.js';
import { API_BASE_URL } from '../config/constants.js';

let isInitialized = false;

export function init() {
    if (isInitialized) return;
    subscribe(onStateChange, ['currentView']);
    isInitialized = true;
}

function onStateChange(newState) {
    if (newState.currentView === 'newpage') {
        render();
    }
}

export function render() {
    // Render logic
}

export function cleanup() {
    // Cleanup logic
}

export default { init, render, cleanup };
```

2. Add to `pages/index.js`:

```javascript
import * as NewPage from './NewPage.js';

export { NewPage };

export const pages = {
    // ... existing pages
    newpage: NewPage
};
```

### Running Tests

```bash
# Open test page in browser
http://localhost:8000/static/src/test.html
```

## File Sizes

| File | Lines | Purpose |
|------|-------|---------|
| constants.js | ~180 | Configuration |
| state.js | ~220 | State management |
| Dashboard.js | ~360 | Dashboard page |
| Employees.js | ~300 | Employees page |
| LeaveRequests.js | ~450 | Leave requests page |
| Analytics.js | ~380 | Analytics page |
| Compliance.js | ~250 | Compliance page |
| Notifications.js | ~320 | Notifications page |
| Settings.js | ~320 | Settings page |
| **Total** | **~2,800** | All modules |

Compare to original `app.js`: ~6,900 lines
