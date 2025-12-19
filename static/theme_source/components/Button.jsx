/**
 * Button Component
 *
 * A versatile button component with multiple variants and sizes.
 * Supports icons, loading states, and full accessibility.
 *
 * @example
 * <Button variant="default">Click me</Button>
 * <Button variant="gradient" size="lg">Submit</Button>
 * <Button variant="ghost" size="icon"><Icon /></Button>
 */

import React from 'react';
import { cn } from '../hooks/utils';

// Button variants with styles
const buttonVariants = {
  default: 'bg-primary text-primary-foreground hover:bg-primary/90 shadow-lg shadow-primary/25',
  destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/90 shadow-lg shadow-destructive/25',
  outline: 'border border-input bg-background hover:bg-accent hover:text-accent-foreground',
  secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
  ghost: 'hover:bg-accent hover:text-accent-foreground',
  link: 'text-primary underline-offset-4 hover:underline',
  success: 'bg-emerald-500 text-white hover:bg-emerald-600 shadow-lg shadow-emerald-500/25',
  warning: 'bg-amber-500 text-white hover:bg-amber-600 shadow-lg shadow-amber-500/25',
  gradient: 'bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white hover:opacity-90 shadow-lg shadow-indigo-500/25',
  neon: 'border border-neon-blue/50 text-neon-blue bg-transparent hover:bg-neon-blue/10 hover:shadow-neon-blue hover:border-neon-blue',
};

// Button sizes
const buttonSizes = {
  default: 'h-10 px-4 py-2',
  sm: 'h-9 rounded-md px-3 text-sm',
  lg: 'h-11 rounded-lg px-8',
  xl: 'h-12 rounded-xl px-10 text-base',
  icon: 'h-10 w-10',
};

/**
 * Button Component
 *
 * @param {Object} props - Component props
 * @param {string} [props.variant='default'] - Button variant
 * @param {string} [props.size='default'] - Button size
 * @param {boolean} [props.isLoading=false] - Show loading spinner
 * @param {boolean} [props.disabled=false] - Disable button
 * @param {React.ReactNode} [props.leftIcon] - Icon on left side
 * @param {React.ReactNode} [props.rightIcon] - Icon on right side
 * @param {React.ReactNode} props.children - Button content
 * @param {string} [props.className] - Additional CSS classes
 * @param {React.Ref} ref - Forward ref
 */
const Button = React.forwardRef(({
  variant = 'default',
  size = 'default',
  isLoading = false,
  disabled = false,
  leftIcon,
  rightIcon,
  children,
  className,
  ...props
}, ref) => {
  const isDisabled = disabled || isLoading;

  return (
    <button
      ref={ref}
      disabled={isDisabled}
      className={cn(
        // Base styles
        'inline-flex items-center justify-center whitespace-nowrap rounded-lg text-sm font-medium',
        'ring-offset-background transition-all duration-200',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
        'disabled:pointer-events-none disabled:opacity-50',
        'active:scale-[0.98]',
        // Variant styles
        buttonVariants[variant],
        // Size styles
        buttonSizes[size],
        // Custom classes
        className
      )}
      {...props}
    >
      {/* Loading spinner */}
      {isLoading && (
        <svg
          className="animate-spin -ml-1 mr-2 h-4 w-4"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      )}

      {/* Left icon */}
      {!isLoading && leftIcon && (
        <span className="mr-2" aria-hidden="true">{leftIcon}</span>
      )}

      {/* Button text */}
      {children}

      {/* Right icon */}
      {rightIcon && (
        <span className="ml-2" aria-hidden="true">{rightIcon}</span>
      )}
    </button>
  );
});

Button.displayName = 'Button';

export { Button, buttonVariants, buttonSizes };
export default Button;
