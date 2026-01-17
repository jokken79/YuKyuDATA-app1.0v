/** @type { import('@storybook/html').Preview } */

// Import all CSS files from the design system
import '../static/css/design-system/tokens.css';
import '../static/css/design-system/components.css';
import '../static/css/design-system/accessibility.css';
import '../static/css/design-system/utilities.css';
import '../static/css/design-system/themes.css';
import '../static/css/main.css';
import '../static/css/ui-enhancements.css';

const preview = {
  parameters: {
    actions: { argTypesRegex: '^on[A-Z].*' },
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
    backgrounds: {
      default: 'dark',
      values: [
        {
          name: 'dark',
          value: '#000000',
        },
        {
          name: 'light',
          value: '#f1f5f9',
        },
      ],
    },
    docs: {
      description: {
        component: 'YuKyuDATA Design System - Componentes UI para gestion de vacaciones',
      },
    },
  },
  decorators: [
    (Story, context) => {
      // Apply theme based on background selection
      const theme = context.globals.backgrounds?.value === '#f1f5f9' ? 'light' : 'dark';
      const storyContent = Story();

      return `
        <div data-theme="${theme}" style="padding: 2rem; min-height: 100vh; background: ${theme === 'dark' ? '#000000' : '#f1f5f9'};">
          ${typeof storyContent === 'string' ? storyContent : storyContent.outerHTML || storyContent}
        </div>
      `;
    },
  ],
  globalTypes: {
    theme: {
      description: 'Global theme for components',
      defaultValue: 'dark',
      toolbar: {
        title: 'Theme',
        icon: 'circlehollow',
        items: ['dark', 'light'],
        dynamicTitle: true,
      },
    },
  },
};

export default preview;
