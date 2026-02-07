/**
 * Design Tokens
 * Define valores centralizados para diseño consistente
 * Se usa en CSS, JavaScript y Storybook
 */

const designTokens = {
  // COLORES
  colors: {
    // Primary
    primary: {
      50: '#e8f9f8',
      100: '#c4f0ef',
      200: '#9fe8e6',
      300: '#5dd9d1',
      400: '#2bcab9',
      500: '#1DA1A1', // Primary main
      600: '#1a8f91',
      700: '#177d81',
      800: '#156b71',
      900: '#0f4a52',
    },
    // Secondary
    secondary: {
      50: '#f5f5f5',
      100: '#e0e0e0',
      200: '#c2c2c2',
      300: '#a3a3a3',
      400: '#848484',
      500: '#666666', // Secondary main
      600: '#555555',
      700: '#444444',
      800: '#333333',
      900: '#1a1a1a',
    },
    // Accent/Warning
    accent: {
      50: '#fff8e1',
      100: '#ffeeb3',
      200: '#ffe480',
      300: '#ffda4d',
      400: '#ffd033',
      500: '#ffc107', // Orange main
      600: '#ffb300',
      700: '#ff9800',
      800: '#f57c00',
      900: '#e65100',
    },
    // Status colors
    success: '#4caf50',
    warning: '#ff9800',
    error: '#f44336',
    info: '#2196f3',
    
    // Neutral
    white: '#ffffff',
    black: '#000000',
    transparent: 'transparent',
  },

  // TIPOGRAFÍA
  typography: {
    fontFamily: {
      base: "'Inter', 'Segoe UI', sans-serif",
      mono: "'Courier New', monospace",
    },
    fontSize: {
      xs: '0.75rem',      // 12px
      sm: '0.875rem',     // 14px
      base: '1rem',       // 16px
      lg: '1.125rem',     // 18px
      xl: '1.25rem',      // 20px
      '2xl': '1.5rem',    // 24px
      '3xl': '1.875rem',  // 30px
      '4xl': '2.25rem',   // 36px
      '5xl': '3rem',      // 48px
    },
    fontWeight: {
      light: 300,
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
      extrabold: 800,
    },
    lineHeight: {
      tight: 1.25,
      normal: 1.5,
      relaxed: 1.75,
      loose: 2,
    },
    letterSpacing: {
      tight: '-0.02em',
      normal: '0em',
      wide: '0.02em',
      wider: '0.05em',
    },
  },

  // ESPACIADO (8px baseline)
  spacing: {
    0: '0',
    1: '0.25rem',   // 4px
    2: '0.5rem',    // 8px
    3: '0.75rem',   // 12px
    4: '1rem',      // 16px
    5: '1.25rem',   // 20px
    6: '1.5rem',    // 24px
    8: '2rem',      // 32px
    10: '2.5rem',   // 40px
    12: '3rem',     // 48px
    16: '4rem',     // 64px
    20: '5rem',     // 80px
  },

  // BORDER RADIUS
  borderRadius: {
    none: '0',
    sm: '0.25rem',  // 4px
    base: '0.375rem', // 6px
    md: '0.5rem',   // 8px
    lg: '0.75rem',  // 12px
    xl: '1rem',     // 16px
    '2xl': '1.5rem', // 24px
    full: '9999px',
  },

  // SOMBRAS
  shadows: {
    none: 'none',
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    base: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
    '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
  },

  // TRANSICIONES
  transitions: {
    fast: '150ms ease-in-out',
    base: '250ms ease-in-out',
    slow: '350ms ease-in-out',
  },

  // BREAKPOINTS (Mobile First)
  breakpoints: {
    xs: '320px',
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    '2xl': '1536px',
  },

  // Z-INDEX
  zIndex: {
    hide: -1,
    auto: 'auto',
    base: 0,
    dropdown: 1000,
    sticky: 1020,
    fixed: 1030,
    modalBackdrop: 1040,
    modal: 1050,
    popover: 1060,
    tooltip: 1070,
  },
};

// CSS Variables string para inyectar en <head>
const generateCSSVariables = (theme = 'light') => {
  const vars = {
    // Light theme
    '--bg-primary': theme === 'light' ? designTokens.colors.white : designTokens.colors.secondary[900],
    '--bg-secondary': theme === 'light' ? designTokens.colors.secondary[50] : designTokens.colors.secondary[800],
    '--text-primary': theme === 'light' ? designTokens.colors.secondary[900] : designTokens.colors.white,
    '--text-secondary': theme === 'light' ? designTokens.colors.secondary[600] : designTokens.colors.secondary[300],
    '--border-color': theme === 'light' ? designTokens.colors.secondary[200] : designTokens.colors.secondary[700],
    
    // Colors
    '--color-primary': designTokens.colors.primary[500],
    '--color-primary-dark': designTokens.colors.primary[700],
    '--color-accent': designTokens.colors.accent[500],
    '--color-success': designTokens.colors.success,
    '--color-error': designTokens.colors.error,
    '--color-warning': designTokens.colors.warning,
    '--color-info': designTokens.colors.info,
  };
  
  return Object.entries(vars)
    .map(([key, value]) => `${key}: ${value};`)
    .join('\n');
};

module.exports = {
  designTokens,
  generateCSSVariables,
};
