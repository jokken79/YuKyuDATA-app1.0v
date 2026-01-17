/**
 * Jest Configuration for YuKyuDATA Application
 * Unit testing setup for ES6 modules and browser environment
 */

module.exports = {
  // Test environment
  testEnvironment: 'jsdom',
  
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
  
  // Test file patterns
  testMatch: [
    '**/tests/**/*.test.js',
    '**/tests/**/*.spec.js'
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
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
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
    '/build/'
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
