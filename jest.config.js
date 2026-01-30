/**
 * Jest Configuration for YuKyuDATA Application
 * Unit testing setup for ES6 modules and browser environment
 */

module.exports = {
  // Test environment with polyfills
  testEnvironment: 'jsdom',
  testEnvironmentOptions: {
    customExportConditions: [''],
  },
  
  // Setup test environment before running tests
  setupFilesAfterEnv: ['<rootDir>/tests/setup.js'],
  
  // Module transformation
  transform: {
    '^.+\\.js$': [
      'babel-jest',
      {
        presets: [
          ['@babel/preset-env', { targets: { node: 'current' } }]
        ]
      }
    ]
  },
  
  // Module file extensions
  moduleFileExtensions: ['js', 'json'],
  
  // Test file patterns - Only .test.js files (not .spec.js which are for Playwright)
  testMatch: [
    '**/tests/**/*.test.js'
  ],
  
  // Module path mapping (for absolute imports)
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/static/js/$1',
    '^@components/(.*)$': '<rootDir>/static/src/components/$1',
    '^@pages/(.*)$': '<rootDir>/static/src/pages/$1',
    '^@store/(.*)$': '<rootDir>/static/src/store/$1',
    '^@config/(.*)$': '<rootDir>/static/src/config/$1'
  },
  
  // Setup files
  setupFilesAfterEnv: ['<rootDir>/tests/setup.js'],
  
  // Coverage configuration
  collectCoverage: true,
  collectCoverageFrom: [
    'static/js/modules/**/*.js',
    'static/src/**/*.js',
    '!static/js/modules/**/*.test.js',
    '!static/js/modules/**/*.spec.js',
    '!static/src/**/*.test.js',
    '!static/src/**/*.spec.js',
    '!static/src/integration-example.js'
  ],
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'lcov', 'html'],
  coverageThreshold: {
    global: {
        branches: 5,
        functions: 5,
        lines: 5,
        statements: 5
    }
  },
  
  // Mock configurations
  clearMocks: true,
  restoreMocks: true,
  
  // Verbose output
  verbose: true,
  
  // Ignore patterns
  testPathIgnorePatterns: [
    '/node_modules/',
    '/dist/',
    '/build/',
    '/tests/e2e/',
    '\\.spec\\.js$'
  ],
  
  // Global variables
  globals: {
    'fetch': true,
    'localStorage': true,
    'sessionStorage': true,
    'requestAnimationFrame': true,
    'cancelAnimationFrame': true
  }
};
