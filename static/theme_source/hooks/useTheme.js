/**
 * useTheme Hook
 *
 * A React hook for managing dark/light theme with localStorage persistence.
 *
 * @example
 * const { theme, setTheme, resolvedTheme, toggleTheme } = useTheme();
 *
 * @version 1.0.0
 */

import { useState, useEffect, useCallback, createContext, useContext } from 'react';

// Storage key for theme preference
const THEME_STORAGE_KEY = 'kintai-theme';

/**
 * Theme Context
 */
const ThemeContext = createContext({
  theme: 'system',
  setTheme: () => {},
  resolvedTheme: 'dark',
  toggleTheme: () => {},
});

/**
 * Theme Provider Component
 *
 * Wrap your app with this provider to enable theme functionality.
 *
 * @example
 * <ThemeProvider defaultTheme="dark">
 *   <App />
 * </ThemeProvider>
 */
export function ThemeProvider({
  children,
  defaultTheme = 'dark',
  storageKey = THEME_STORAGE_KEY,
}) {
  const [theme, setThemeState] = useState(defaultTheme);
  const [resolvedTheme, setResolvedTheme] = useState('dark');
  const [mounted, setMounted] = useState(false);

  // Initialize theme from localStorage
  useEffect(() => {
    setMounted(true);
    const stored = localStorage.getItem(storageKey);
    if (stored) {
      setThemeState(stored);
    }
  }, [storageKey]);

  // Apply theme to document
  useEffect(() => {
    if (!mounted) return;

    const root = window.document.documentElement;
    root.classList.remove('light', 'dark');

    let effectiveTheme;
    if (theme === 'system') {
      effectiveTheme = window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light';
    } else {
      effectiveTheme = theme;
    }

    root.classList.add(effectiveTheme);
    setResolvedTheme(effectiveTheme);
  }, [theme, mounted]);

  // Listen for system theme changes
  useEffect(() => {
    if (!mounted) return;

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = () => {
      if (theme === 'system') {
        const root = window.document.documentElement;
        const effectiveTheme = mediaQuery.matches ? 'dark' : 'light';
        root.classList.remove('light', 'dark');
        root.classList.add(effectiveTheme);
        setResolvedTheme(effectiveTheme);
      }
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [theme, mounted]);

  // Set theme with localStorage persistence
  const setTheme = useCallback((newTheme) => {
    localStorage.setItem(storageKey, newTheme);
    setThemeState(newTheme);
  }, [storageKey]);

  // Toggle between light and dark
  const toggleTheme = useCallback(() => {
    const newTheme = resolvedTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
  }, [resolvedTheme, setTheme]);

  const value = {
    theme,
    setTheme,
    resolvedTheme,
    toggleTheme,
  };

  // Prevent flash of wrong theme
  if (!mounted) {
    return <div className="dark">{children}</div>;
  }

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}

/**
 * useTheme Hook
 *
 * @returns {Object} Theme context value
 * @property {string} theme - Current theme setting ('dark', 'light', 'system')
 * @property {Function} setTheme - Set theme function
 * @property {string} resolvedTheme - Resolved theme ('dark' or 'light')
 * @property {Function} toggleTheme - Toggle between dark and light
 */
export function useTheme() {
  const context = useContext(ThemeContext);

  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }

  return context;
}

export { ThemeContext, THEME_STORAGE_KEY };
export default useTheme;
