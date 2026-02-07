# YuKyu DATA - Clean Tech SaaS Design System
> **Version:** 2.0 (Clean Tech Edition)
> **Status:** Production
> **Theme:** Light (Default) / Dark (Deep Navy)

## 1. Core Philosophy: "Invisible Precision"
We moved away from "Gaming/Glass" aesthetics to a **Clean Tech SaaS** look (inspired by Stripe, Linear, Notion).
- **Light Mode:** Almost white (`#FAF5FF`), no heavy dots, card-based.
- **Dark Mode:** Deep Navy (`#020617`), high contrast, glowing accents.
- **Grid:** Layout is strictly controlled by CSS Grid (`layout.css`).

## 2. Color Palette (Variables)
| Token | Light Mode Value | Dark Mode Value | Usage |
|-------|------------------|-----------------|-------|
| `--bg-base` | `#f3f4f6` (Clean Silver) | `#020617` (Slate 950) | Main App Background |
| `--bg-surface` | `#ffffff` (Pure White) | `#1e293b` (Slate 800) | Cards / Panels |
| `--primary` | `hsl(258, 89%, 66%)` | (Glow effect added) | Action Buttons, Active States |
| `--text-primary`| `#1e1b4b` (Indigo Deep)| `#f8fafc` (Slate 50) | Main Headings |

## 3. UI Components
### The "Clean Card" (`.glass-panel`)
Instead of heavy blur, we use solid surfaces with subtle definition.
```css
.glass-panel {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  box-shadow: var(--shadow-sm);
  /* No backdrop-filter in Light Mode */
}
```

### Typography
- **Headings & Data:** `Fira Code` (Monospace) - Promoting the "Engineering" feel.
- **Body:** `Fira Sans` - High legibility for tables.

## 4. Dark Mode Strategy
Dark mode overrides are handled via `[data-theme="dark"]` in `variables.css`.
- Text automatically inverts to White/Slate-200.
- Shadows change to "Glows" (colored drop-shadows).

## 5. Critical Files
- `static/css/nexus-theme/layout.css`: CSS Grid Shell (Sidebar + Content).
- `static/css/nexus-theme/variables.css`: The Source of Truth for colors.
- `static/css/unified-design-system.css`: Component styling.

*Updated by Antigravity (UI-UX Pro Max) - Jan 2026*
