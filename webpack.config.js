/**
 * Webpack Configuration for YuKyu Frontend
 * Bundles modern ES6 modules with tree-shaking, code splitting, and PWA support
 */

const path = require('path');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const TerserPlugin = require('terser-webpack-plugin');
const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');
const { InjectManifest } = require('workbox-webpack-plugin');

const isDevelopment = process.env.NODE_ENV !== 'production';

module.exports = {
  mode: isDevelopment ? 'development' : 'production',
  entry: {
    // Main app bundle
    app: './static/src/index.js',

    // Legacy adapter for backwards compatibility
    legacy: './static/src/legacy-adapter.js',
  },

  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: isDevelopment
      ? '[name].js'
      : '[name].[contenthash].js',
    chunkFilename: isDevelopment
      ? '[name].chunk.js'
      : '[name].[contenthash].chunk.js',
    publicPath: '/dist/',
    clean: true,
    // Generate bundle analysis stats
    ...(process.env.ANALYZE && {
      analyzerMode: 'json',
      analyzerFile: 'dist/stats.json',
    }),
  },

  // Enable source maps for debugging
  devtool: isDevelopment ? 'eval-source-map' : 'source-map',

  // Module resolution
  resolve: {
    extensions: ['.js', '.json'],
    alias: {
      '@components': path.resolve(__dirname, 'static/src/components/'),
      '@pages': path.resolve(__dirname, 'static/src/pages/'),
      '@store': path.resolve(__dirname, 'static/src/store/'),
      '@config': path.resolve(__dirname, 'static/src/config/'),
      '@utils': path.resolve(__dirname, 'static/src/utils/'),
      '@services': path.resolve(__dirname, 'static/src/services/'),
    },
  },

  // Module rules
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: [
              [
                '@babel/preset-env',
                {
                  targets: { browsers: ['last 2 versions', 'ie >= 11'] },
                  modules: false,
                  useBuiltIns: 'usage',
                  corejs: 3,
                },
              ],
            ],
            plugins: [
              // Remove console logs in production
              ...(process.env.NODE_ENV === 'production'
                ? [['transform-remove-console', { exclude: ['error', 'warn'] }]]
                : []),
            ],
          },
        },
      },
      {
        test: /\.css$/,
        use: [
          isDevelopment ? 'style-loader' : MiniCssExtractPlugin.loader,
          {
            loader: 'css-loader',
            options: {
              importLoaders: 1,
              sourceMap: true,
              modules: false,
            },
          },
          {
            loader: 'postcss-loader',
            options: {
              postcssOptions: {
                plugins: [
                  'autoprefixer',
                  ...(process.env.NODE_ENV === 'production'
                    ? [['cssnano', { preset: ['default', { discardComments: { removeAll: true } }] }]]
                    : []),
                ],
              },
            },
          },
        ],
      },
    ],
  },

  // Optimization
  optimization: {
    minimize: !isDevelopment,
    minimizer: [
      new TerserPlugin({
        terserOptions: {
          compress: {
            drop_console: true,
            drop_debugger: true,
            pure_funcs: ['console.log'],
          },
          output: {
            comments: false,
          },
        },
        extractComments: false,
      }),
    ],
    // Code splitting strategy
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        // Vendor libraries
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          priority: 10,
          reuseExistingChunk: true,
        },
        // Common chunks used by multiple entry points
        common: {
          minChunks: 2,
          priority: 5,
          reuseExistingChunk: true,
        },
        // Page-specific chunks
        pages: {
          test: /[\\/]static[\\/]src[\\/]pages[\\/]/,
          name: 'pages',
          priority: 15,
          reuseExistingChunk: true,
        },
        // Component chunks
        components: {
          test: /[\\/]static[\\/]src[\\/]components[\\/]/,
          name: 'components',
          priority: 14,
          reuseExistingChunk: true,
        },
      },
    },
    // Use deterministic hashes for better cache busting
    moduleIds: 'deterministic',
    runtimeChunk: {
      name: 'runtime',
    },
  },

  // Plugins
  plugins: [
    // Extract CSS into separate files
    new MiniCssExtractPlugin({
      filename: isDevelopment
        ? '[name].css'
        : '[name].[contenthash].css',
      chunkFilename: isDevelopment
        ? '[name].chunk.css'
        : '[name].[contenthash].chunk.css',
    }),

    // Service worker for PWA with Workbox
    new InjectManifest({
      swSrc: './static/src/service-worker.js',
      swDest: 'service-worker.js',
      dontCacheBustURLsMatching: /\.[0-9a-f]{8}\./,
      mode: 'production',
      maximumFileSizeToCacheInBytes: 5 * 1024 * 1024, // 5MB
      clientsClaim: true,
      skipWaiting: true,
      // Precache patterns
      globPatterns: [
        'dist/**/*.{js,css}',
        'static/css/**/*.css',
        'static/locales/**/*.json',
      ],
      globIgnores: [
        '**/*.map',
        '**/index.html',
      ],
    }),

    // Bundle analyzer
    ...(process.env.ANALYZE
      ? [new BundleAnalyzerPlugin({
          openAnalyzer: false,
          analyzerMode: 'static',
          reportFilename: 'dist/bundle-report.html',
        })]
      : []),
  ],

  // Dev server configuration
  devServer: {
    port: 3000,
    hot: true,
    historyApiFallback: true,
    compress: true,
    client: {
      overlay: {
        errors: true,
        warnings: false,
      },
    },
    // Proxy API calls to backend
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        pathRewrite: { '^/api': '/api' },
      },
      '/docs': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },

  // Performance
  performance: {
    maxEntrypointSize: 512000,
    maxAssetSize: 512000,
    hints: isDevelopment ? false : 'warning',
  },
};
