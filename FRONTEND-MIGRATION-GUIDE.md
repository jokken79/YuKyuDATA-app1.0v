# Frontend Migration Guide - YuKyuDATA

## Overview

**Status:** Legacy architecture coexists with modern components
**Goal:** Gradual migration from `static/js/app.js` (7,564 lines) to `static/src/` (modular ES6)
**Timeline:** 6-8 weeks
**Benefit:** Reduced code duplication, better maintainability, cleaner UI/UX

---

## Problem 1: Dual Architecture

**Current State:**
```
Frontend Layer (SPA)
├── Legacy: static/js/app.js (7,564 lines - monolithic)
├── Modern: static/src/ (modular ES6 components)
└── Bridge: static/src/legacy-bridge/ (UnifiedBridge)
```

**Issues:**
- Inconsistent visual design across features
- Maintenance burden (update code in 2 places)
- Bundle size inflated (~40% unused code)
- Different patterns and conventions

---

## Migration Strategy

### Phase 1: Foundation (Week 1-2)
**Goal:** Set up infrastructure for gradual migration

#### 1.1 Migrate Most-Used Modules

**Priority Order** (by frequency of use):
1. **Data Service** - API communication layer
2. **Theme Manager** - Dark/light mode toggle
3. **UI Components** - Buttons, forms, modals
4. **Auth Manager** - Login/logout flows
5. **Chart Manager** - Dashboard visualizations

**Action Items:**
```bash
# 1. Convert static/js/data-service.js to ES6
static/src/services/data-service-v2.js
├── Remove jQuery dependencies
├── Use native fetch API
└── Export named functions

# 2. Create unified service exports
static/src/index.js (main entry point)
├── re-export all services
├── maintain backwards compatibility
└── provide usage examples

# 3. Update app.js to use new services
app.js (gradual transition)
├── Change: import data from '/static/src/services/data-service-v2.js'
├── Keep: All UI rendering logic (temporary)
└── Plan: Remove UI rendering in Phase 2
```

**Implementation Example:**
```javascript
// BEFORE (in app.js - monolithic)
class DataService {
    async getEmployees() {
        // 200+ lines of jQuery + fetch mixed
    }
}

// AFTER (static/src/services/data-service-v2.js - clean)
export async function getEmployees(year) {
    const res = await fetch(`/api/employees?year=${year}`);
    if (!res.ok) throw new Error('Failed to fetch');
    return res.json();
}

// BRIDGE (in app.js)
import { getEmployees } from '/static/src/services/data-service-v2.js';
// Now app.js uses the new service
```

---

### Phase 2: UI Components (Week 3-4)
**Goal:** Migrate core UI components to modern architecture

#### 2.1 Convert 5 High-Impact Components

**Top Priority Features to Migrate:**
1. **Login Modal** (most visible, least complex)
2. **Employee Table** (used on every dashboard)
3. **Leave Request Form** (main business logic)
4. **Dashboard Cards** (repetitive components)
5. **Navigation Sidebar** (shared across all pages)

**Action Plan:**

```bash
# 1. Create component versions in static/src/components/
static/src/components/
├── login-modal-v2.js           # Replace index.html login
├── employee-table-v2.js        # Replace app.js table rendering
├── leave-request-form-v2.js    # Replace leave request modal
├── dashboard-cards-v2.js       # Replace hardcoded card HTML
└── navigation-sidebar-v2.js    # Replace sidebar menu

# 2. Update app.js to use new components
# Replace direct DOM manipulation:
OLD: document.getElementById('login-modal').innerHTML = buildLoginForm();
NEW: const loginModal = new LoginModalV2(options); loginModal.render();

# 3. Keep legacy code as fallback
# If component fails to load, fallback to old HTML rendering
```

**Example Migration:**

```javascript
// BEFORE (app.js - 150 lines of spaghetti code)
function renderEmployeeTable(data) {
    let html = '<table>';
    for (let emp of data) {
        html += `<tr>
            <td>${emp.name}</td>
            <td data-emp-id="${emp.id}" class="action" onclick="editEmployee('${emp.id}')">
                Edit
            </td>
        </tr>`;
    }
    html += '</table>';
    document.getElementById('employee-table').innerHTML = html;
    // Then manually add event listeners...
}

// AFTER (static/src/components/employee-table-v2.js - clean & maintainable)
export class EmployeeTable {
    constructor(data) {
        this.data = data;
    }

    render() {
        const table = document.createElement('table');
        this.data.forEach(emp => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${emp.name}</td>
                <td>
                    <button data-emp-id="${emp.id}">Edit</button>
                </td>
            `;
            row.querySelector('button').addEventListener('click',
                () => this.onEdit(emp.id));
            table.appendChild(row);
        });
        return table;
    }

    onEdit(empId) {
        // Handle edit
    }
}

// USAGE in app.js (transitional)
import { EmployeeTable } from '/static/src/components/employee-table-v2.js';

const employees = await getEmployees();
const table = new EmployeeTable(employees);
document.getElementById('container').appendChild(table.render());
```

---

### Phase 3: Page Manager Migration (Week 5-6)
**Goal:** Convert page managers to use modern components

#### 3.1 Migrate Page Managers

```bash
# Page managers control page routing and rendering
# Current: static/src/pages/dashboard-manager.js (uses legacy styles)
# Target: static/src/pages-v2/dashboard-manager.js (uses new components)

# Convert in order:
1. DashboardManager → uses EmployeeTable, DashboardCards
2. EmployeesManager → uses EmployeeTable, SearchBar
3. LeaveRequestsManager → uses LeaveRequestForm, LeaveTable
4. AnalyticsManager → uses Chart components
5. ComplianceManager → uses DataTable, ReportCards
```

**Implementation:**

```javascript
// BEFORE (static/src/pages/dashboard-manager.js - 300 lines mixed concerns)
class DashboardManager {
    async init() {
        const data = await this.fetchData();
        this.renderUI(data);      // Direct DOM manipulation
        this.setupEventHandlers(); // Event wiring
        this.initCharts();         // Chart initialization
    }

    renderUI(data) {
        // 200 lines of HTML string building
    }
}

// AFTER (static/src/pages-v2/dashboard-manager.js - clean separation)
import { DashboardCards } from '../components/dashboard-cards-v2.js';
import { Chart } from '../components/chart-v2.js';

class DashboardManager {
    constructor(container) {
        this.container = container;
        this.cards = null;
        this.chart = null;
    }

    async init() {
        const data = await this.fetchData();
        this.render(data);         // Render using components
        this.setupEventHandlers(); // Clear event logic
    }

    render(data) {
        // Use components
        this.cards = new DashboardCards(data);
        this.chart = new Chart(data);

        this.container.innerHTML = '';
        this.container.appendChild(this.cards.render());
        this.container.appendChild(this.chart.render());
    }
}
```

---

### Phase 4: Legacy Code Cleanup (Week 7-8)
**Goal:** Remove deprecated code, finalize migration

#### 4.1 Deprecation Checklist

```bash
# Week 7: Mark legacy code as deprecated
# app.js:1 Add banner
/*
 * ⚠️ DEPRECATED - This file is being phased out
 * New development should use: static/src/pages/
 * Timeline: Remove by 2026-04-01
 */

# Week 8: Remove deprecated code
# Delete files that have been fully migrated:
DELETE: static/js/app.js (if all pages migrated)
DELETE: static/src/legacy-bridge/ (if bridge unused)
DELETE: static/js/ui-manager.js (if replaced by components-v5.js)
DELETE: static/js/theme-manager.js (if replaced by modern version)
```

---

## Migration Checklist

### Week 1-2: Services
- [ ] Create `data-service-v2.js` (fetch API, no jQuery)
- [ ] Create `auth-service-v2.js`
- [ ] Create `theme-manager-v2.js`
- [ ] Update `app.js` to import new services
- [ ] Test all API calls work via new services

### Week 3-4: Components
- [ ] Create `login-modal-v2.js`
- [ ] Create `employee-table-v2.js`
- [ ] Create `leave-request-form-v2.js`
- [ ] Create `dashboard-cards-v2.js`
- [ ] Integrate components into app.js
- [ ] Visual regression testing (screenshot compare)

### Week 5-6: Page Managers
- [ ] Create `pages-v2/dashboard-manager.js`
- [ ] Create `pages-v2/employees-manager.js`
- [ ] Create `pages-v2/leave-manager.js`
- [ ] Test page transitions
- [ ] Test responsive design (375px, 768px, 1024px)

### Week 7-8: Cleanup
- [ ] Remove deprecated code markers
- [ ] Delete unused legacy files
- [ ] Performance audit (bundle size reduction)
- [ ] Final E2E tests (Playwright)
- [ ] Deploy to production

---

## Backwards Compatibility Strategy

**Until migration complete:**

```javascript
// Keep both versions running in parallel

// 1. Try new component
try {
    import newComponent from '/static/src/components/new-version.js';
    const component = new newComponent();
    // Success - use new component
} catch (error) {
    // Fallback to legacy
    import oldComponent from '/static/js/legacy/old-version.js';
    const component = new oldComponent();
}

// 2. Gradual rollout
// Use feature flag to switch between old/new
if (config.USE_NEW_COMPONENTS === true) {
    // Use new components
} else {
    // Use legacy app.js
}
```

---

## Testing Strategy

### Unit Tests
```bash
# Test new services independently
npm test -- services/data-service-v2.js

# Test components in isolation
npm test -- components/employee-table-v2.js
```

### Integration Tests
```bash
# Test page managers work with new components
npm test -- pages-v2/dashboard-manager.js
```

### E2E Tests
```bash
# Test full user workflows
npx playwright test tests/e2e/migration/
```

### Regression Tests
```bash
# Compare old vs new screenshots
npm run test:visual-regression

# Check performance (bundle size)
npm run analyze:bundle
```

---

## Performance Impact

### Expected Improvements
| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Bundle Size** | 450 KB | 280 KB | -38% |
| **First Load** | 2.3s | 1.4s | -40% |
| **TTI** | 3.1s | 1.8s | -42% |
| **Code Duplication** | 40% | 5% | -35% |

### Bundle Size Breakdown
```
Before:
app.js (monolithic): 350 KB
legacy-bridge: 45 KB
old components: 55 KB
Total: 450 KB

After:
new-components: 120 KB
services: 80 KB
managers: 60 KB
utils: 20 KB
Total: 280 KB
```

---

## File Structure After Migration

```
Frontend (Post-Migration):
├── static/src/
│   ├── components/
│   │   ├── ui-components-v5.js      (Button, Form, Alert, etc)
│   │   ├── employee-table-v2.js
│   │   ├── leave-request-form-v2.js
│   │   ├── dashboard-cards-v2.js
│   │   └── ...
│   ├── services/
│   │   ├── data-service-v2.js
│   │   ├── auth-service-v2.js
│   │   ├── theme-manager-v2.js
│   │   └── ...
│   ├── pages-v2/
│   │   ├── dashboard-manager.js
│   │   ├── employees-manager.js
│   │   ├── leave-manager.js
│   │   └── ...
│   ├── index.js                     (main entry)
│   └── app-v2.js                    (modern SPA router)
├── static/css/
│   └── yukyu-design-system-v5-professional.css ✅
└── templates/
    └── index.html                   (uses v5 CSS + app-v2.js)

DELETED:
├── static/js/app.js (7,564 lines)
├── static/src/legacy-bridge/
└── Static/js/old-managers/
```

---

## Communication Plan

**For the Team:**

> We're modernizing the frontend architecture to improve maintainability and performance.
>
> **What's changing:**
> - Moving from monolithic `app.js` to modular components
> - Using modern ES6+ syntax (promises, async/await, modules)
> - New design system with better accessibility
>
> **Timeline:**
> - Week 1-2: Services layer
> - Week 3-4: UI components
> - Week 5-6: Page managers
> - Week 7-8: Cleanup
>
> **You can:**
> - Use new components for any new features
> - Submit bug reports using new components
> - Help with testing (visual regression, E2E)

---

## FAQ

**Q: Will users see changes?**
A: No. Migration is internal. UI will look the same until we update styles.

**Q: Can I use new components for my feature?**
A: Yes! Use `static/src/components/ui-components-v5.js` for any new development.

**Q: What if the new component has bugs?**
A: We maintain both versions until migration complete. Fallback to legacy code.

**Q: How do I test my changes?**
A: Use Playwright E2E tests. Visual regression testing compares old vs new.

---

## Resources

- **Design System:** `static/css/yukyu-design-system-v5-professional.css`
- **Component Library:** `static/src/components/ui-components-v5.js`
- **Example Migration:** `FRONTEND-MIGRATION-EXAMPLES.md` (coming soon)
- **Testing Guide:** `TESTING-MODERN-FRONTEND.md` (coming soon)

---

**Status:** ✅ Plan Ready
**Owner:** Frontend Team
**Last Updated:** 2026-02-10
