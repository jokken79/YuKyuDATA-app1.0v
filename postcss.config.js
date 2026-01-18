/**
 * PostCSS Configuration
 * Processes CSS with autoprefixer, minification, and other optimizations
 */

module.exports = {
  plugins: [
    // Autoprefixer for vendor prefixes
    require('autoprefixer'),

    // CSS minification and optimization (production only)
    ...(process.env.NODE_ENV === 'production' ? [
      require('cssnano')({
        preset: [
          'default',
          {
            discardComments: {
              removeAll: true,
            },
            normalizeDeclarations: true,
            mergeRules: true,
          },
        ],
      }),
    ] : []),
  ],
};
