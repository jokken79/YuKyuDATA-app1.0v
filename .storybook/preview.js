/**
 * Storybook Preview Configuration
 * Global decorators, parameters, and theme configuration
 */

// Import global styles
import '../static/css/main.css';
import '../static/css/design-system/tokens.css';
import '../static/css/design-system/components.css';
import '../static/css/design-system/accessibility-wcag-aa.css';

// Global story parameters
export const parameters = {
  // Accessibility testing
  a11y: {
    // Axe accessibility testing
    config: {
      rules: [
        {
          id: 'color-contrast',
          enabled: true,
        },
        {
          id: 'aria-required-attr',
          enabled: true,
        },
      ],
    },
    options: {
      checks: {
        'color-contrast': {
          options: {
            levels: 'aa', // WCAG AA
          },
        },
      },
    },
  },

  // Viewport settings
  viewport: {
    viewports: {
      mobile: {
        name: 'Mobile',
        styles: {
          width: '375px',
          height: '667px',
        },
        type: 'mobile',
      },
      tablet: {
        name: 'Tablet',
        styles: {
          width: '768px',
          height: '1024px',
        },
        type: 'tablet',
      },
      desktop: {
        name: 'Desktop',
        styles: {
          width: '1280px',
          height: '1024px',
        },
        type: 'desktop',
      },
    },
  },

  // Layout settings
  layout: 'centered',

  // Dark mode
  darkMode: {
    dark: {
      base: 'dark',
      colorPrimary: '#f59e0b',
      colorSecondary: '#0891b2',
      appBg: '#1e293b',
      appContentBg: '#0f172a',
      appBorderColor: '#334155',
      textColor: '#f1f5f9',
    },
    light: {
      base: 'light',
      colorPrimary: '#f59e0b',
      colorSecondary: '#0891b2',
      appBg: '#f8fafc',
      appContentBg: '#ffffff',
      appBorderColor: '#e2e8f0',
      textColor: '#1e293b',
    },
  },
};

// Global decorators
export const decorators = [
  // Add padding and background
  (story) => {
    const container = document.createElement('div');
    container.style.padding = '2rem';
    container.style.background = 'var(--color-background, #f8fafc)';
    container.appendChild(story.render());
    return container;
  },

  // Accessibility checker
  (story) => {
    const element = story.render();
    // Add data-testid for testing
    if (element && typeof element.setAttribute === 'function') {
      element.setAttribute('data-testid', 'storybook-component');
    }
    return element;
  },
];

// Global story parameters
export const globalTypes = {
  theme: {
    name: 'Theme',
    description: 'Global theme for all stories',
    defaultValue: 'light',
    toolbar: {
      icon: 'circlehollow',
      items: [
        { value: 'light', icon: 'circlehollow', title: 'Light' },
        { value: 'dark', icon: 'circle', title: 'Dark' },
      ],
      showName: true,
    },
  },

  locale: {
    name: 'Language',
    description: 'Component language',
    defaultValue: 'ja',
    toolbar: {
      icon: 'globe',
      items: [
        { value: 'ja', right: '日本語', title: 'Japanese' },
        { value: 'en', right: 'English', title: 'English' },
        { value: 'es', right: 'Español', title: 'Spanish' },
      ],
      showName: true,
    },
  },
};
