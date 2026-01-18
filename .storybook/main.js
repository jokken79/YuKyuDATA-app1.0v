/**
 * Storybook Configuration
 * Documents all frontend components with interactive examples and accessibility tests
 */

export default {
  stories: [
    '../static/src/components/**/*.stories.js',
    '../static/src/pages/**/*.stories.js',
  ],

  addons: [
    '@storybook/addon-essentials',
    '@storybook/addon-a11y',
    '@storybook/addon-links',
  ],

  framework: {
    name: '@storybook/html-vite',
    options: {},
  },

  docs: {
    autodocs: true,
  },

  features: {
    storyStoreV7: true,
  },
};
