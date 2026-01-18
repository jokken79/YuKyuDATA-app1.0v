# Frontend Modernization Migration Guide

## Overview

YuKyuDATA v5.19+ has completed a major frontend modernization. This guide helps you understand the new architecture and how to migrate from legacy code.

## Architecture Changes

### Old Architecture (Legacy)
```
static/js/app.js (7,091 lines)
├── app.js - Monolithic SPA
├── modules/ - 15 utility modules
└── assets - Static files
```

### New Architecture (Modern)
```
static/src/ (Modular ES6)
├── components/ - 14 reusable components
├── pages/ - 7 page modules
├── store/ - State management (Observer pattern)
├── utils/ - Utilities & helpers
├── config/ - Configuration
├── services/ - API clients
└── index.js - Entry point
```

## Key Improvements

### 1. Modularity
- **Before**: Monolithic 7,091 line file
- **After**: 14 focused components + 7 pages

### 2. Performance
- **Webpack bundling** with tree-shaking
- **Code splitting** by page/component
- **Size reduction**: 293KB → ~100KB (-66%)

### 3. Accessibility
- **WCAG AA 100% compliance**
- Focus management (FocusManager)
- ARIA labels (AriaManager)
- Keyboard navigation (KeyboardNav)

### 4. PWA Support
- Service worker with caching strategies
- Offline functionality
- Background sync ready

### 5. Development Experience
- Storybook documentation
- ESLint + StyleLint
- Jest tests
- Hot module reloading

## Migration Steps

### Step 1: Build Modern Bundles

```bash
npm install
npm run build
```

This generates optimized bundles in `dist/`:
```
dist/
├── app.js (main bundle)
├── pages.chunk.js (page-specific code)
├── components.chunk.js (component code)
├── runtime.js (webpack runtime)
└── *.css (extracted stylesheets)
```

### Step 2: Update HTML

**Before (Legacy):**
```html
<script src="/static/js/app.js"></script>
<script src="/static/js/modules/data-service.js"></script>
<link rel="stylesheet" href="/static/css/main.css">
```

**After (Modern):**
```html
<!-- Main app bundle -->
<script src="/dist/app.js"></script>

<!-- Or use async loading for better performance -->
<script defer src="/dist/app.js"></script>

<!-- CSS is injected by webpack -->
```

### Step 3: Register Service Worker

Add to your HTML template or main JS:

```javascript
// Register PWA Service Worker
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/dist/service-worker.js')
    .then(registration => console.log('SW registered'))
    .catch(error => console.error('SW error:', error));
}
```

### Step 4: Update API Integration

**Before (Legacy):**
```javascript
// Direct fetch in app.js
fetch('/api/employees')
  .then(r => r.json())
  .then(data => {
    App.state.employees = data;
    App.render();
  });
```

**After (Modern):**
```javascript
// Using modern service layer
import * as State from '/static/src/store/state.js';

const response = await fetch('/api/employees');
const data = await response.json();
State.setStateValue('employees', data);
```

### Step 5: Component Migration

#### Modal Migration

**Before (Legacy):**
```javascript
// In app.js - show modal inline
App.showModal({
  title: '確認',
  content: '削除しますか？',
  onConfirm: () => deleteEmployee()
});
```

**After (Modern):**
```javascript
// Using Modal component
import { Modal } from '/static/src/components/Modal.js';

const modal = new Modal({
  title: '確認',
  content: '削除しますか？',
  onConfirm: () => deleteEmployee()
});
modal.open();
```

#### Table Migration

**Before (Legacy):**
```javascript
// Build HTML manually
const table = '<table>...' + employees.map(e =>
  '<tr><td>' + e.name + '</td>...</tr>'
).join('') + '</table>';
document.getElementById('table').innerHTML = table;
```

**After (Modern):**
```javascript
// Using DataTable component
import { DataTable } from '/static/src/components/Table.js';

const table = new DataTable({
  columns: [
    { key: 'name', label: '氏名', sortable: true },
    { key: 'balance', label: '残日数', type: 'number' }
  ],
  data: employees,
  pagination: { pageSize: 20 }
});
document.getElementById('container').appendChild(table.render());
```

#### Form Migration

**Before (Legacy):**
```javascript
// Manual form handling
const form = document.getElementById('myForm');
form.onsubmit = function(e) {
  e.preventDefault();
  const data = new FormData(form);
  // Manual validation...
};
```

**After (Modern):**
```javascript
// Using Form component
import { Form } from '/static/src/components/Form.js';

const form = new Form({
  fields: [
    { name: 'employee_num', label: '社員番号', required: true },
    { name: 'start_date', label: '開始日', type: 'date', required: true }
  ],
  onSubmit: async (data) => {
    await fetch('/api/leave-requests', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
  }
});
```

### Step 6: State Management Migration

**Before (Legacy):**
```javascript
// Direct object mutation
App.state = {
  employees: [],
  selectedYear: 2025
};
App.state.employees = newData; // Direct mutation
App.render();
```

**After (Modern):**
```javascript
// Using Observer pattern
import * as State from '/static/src/store/state.js';

// Subscribe to changes
State.subscribe('employees', (newData) => {
  console.log('Employees updated:', newData);
  updateUI(newData);
});

// Update state
State.setStateValue('employees', newData);
```

## Breaking Changes

### 1. Global Namespace
- **Before**: Everything attached to `window.App`
- **After**: ES6 modules, no global pollution
- **Migration**: Use named imports instead

### 2. jQuery (if used)
- **Before**: jQuery for DOM manipulation
- **After**: Vanilla JS only
- **Migration**: Replace jQuery with native DOM APIs

### 3. String Concatenation (HTML)
- **Before**: `html += '<div>' + data + '</div>'`
- **After**: Template literals and `createElement()`
- **Migration**: Use `escapeHtml()` for user input

### 4. Global Event Listeners
- **Before**: `document.addEventListener()` everywhere
- **After**: Component-scoped listeners
- **Migration**: Use component lifecycle methods

## Testing

### Run Tests

```bash
# Unit tests
npm test

# Accessibility tests
npm run test:a11y

# With coverage
npm run test:coverage

# Watch mode
npm run test:watch
```

### E2E Tests

```bash
npx playwright test
npx playwright test --headed  # With UI
```

## Documentation

### Component Documentation

View Storybook documentation:

```bash
npm run storybook
# Opens http://localhost:6006
```

Browse:
- **Components** - All 14 reusable components
- **Pages** - Full page examples
- **Accessibility** - WCAG AA compliance demo
- **A11y** - Automated accessibility testing

### API Documentation

FastAPI Swagger UI:
```
http://localhost:8000/docs
```

## Performance Optimization

### Bundle Analysis

```bash
ANALYZE=1 npm run build
open dist/bundle-report.html
```

### Lighthouse Scores

Target metrics:
- **Performance**: 90+
- **Accessibility**: 95+
- **Best Practices**: 90+
- **SEO**: 95+

Check:
```bash
# Using DevTools Lighthouse
# Or via CLI:
npm run build
npx lighthouse http://localhost:8000 --view
```

## Troubleshooting

### Issue: "Module not found"

```javascript
// ✗ Wrong
import Modal from './components/Modal';

// ✓ Correct
import { Modal } from './components/Modal.js';
```

### Issue: "Service Worker not registering"

```javascript
// Make sure it's in your HTML
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/dist/service-worker.js');
}
```

### Issue: "Styling not applied"

```javascript
// Check that CSS is imported in your JS
import '/static/css/main.css';
import '/static/css/design-system/tokens.css';
```

### Issue: "Accessibility errors"

Run tests:
```bash
npm run test:a11y
npm run storybook  # View accessibility addon
```

## Rollback Plan

If you need to revert to legacy system:

```bash
# Keep legacy files intact
static/js/app.js  # Still available
static/js/modules/  # Still available

# Switch to legacy in HTML
<script src="/static/js/app.js"></script>
```

## Support

### Resources
- Storybook: http://localhost:6006
- API Docs: http://localhost:8000/docs
- Tests: `npm test`
- Linting: `npm run lint`

### Common Commands

```bash
# Development
npm run dev              # Hot reload
npm run storybook       # Component docs

# Build
npm run build           # Production build
npm run build:dev       # Dev build with source maps
npm run build:analyze   # Bundle analysis

# Testing
npm test                # All tests
npm run test:a11y       # Accessibility tests
npm run test:coverage   # Coverage report

# Quality
npm run lint            # Lint JS and CSS
npm run lint:js         # JavaScript only
npm run lint:css        # CSS only
```

## Deployment

### Production Build

```bash
npm run build
# Creates optimized dist/ folder

# Upload to server:
# dist/ → /var/www/html/dist/
# templates/index.html → /var/www/html/
```

### Docker

```bash
# Build with new frontend
docker-compose build
docker-compose up -d
```

### Service Worker Caching

Production caching strategies:
- **Static assets**: Cache-first
- **API calls**: Network-first with fallback
- **HTML**: Network-first

Cache invalidation:
```javascript
// Clear old caches
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.controller.postMessage({
    action: 'clearCache'
  });
}
```

## Timeline

| Phase | Duration | Tasks |
|-------|----------|-------|
| **Phase 1** | Week 1 | Update dependencies, build webpack |
| **Phase 2** | Week 2 | Migrate components, update HTML |
| **Phase 3** | Week 3 | Testing, optimization, documentation |
| **Phase 4** | Week 4 | Deploy, monitor, support |

## Conclusion

The modern architecture provides:
- ✓ Better performance (-66% bundle size)
- ✓ WCAG AA accessibility
- ✓ PWA capabilities
- ✓ Improved developer experience
- ✓ Easier maintenance

Start with the modular components for new features, and gradually migrate existing code.

---

**Version**: 5.19
**Last Updated**: 2026-01-17
**Questions?** Review `CLAUDE_MEMORY.md` or check component documentation
