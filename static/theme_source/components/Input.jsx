/**
 * Input Component
 *
 * A styled input component with focus states and accessibility support.
 * Includes variants for different input types.
 *
 * @example
 * <Input type="text" placeholder="Enter text..." />
 * <Input type="email" error="Invalid email" />
 */

import React from 'react';
import { cn } from '../hooks/utils';

/**
 * Input Component
 *
 * @param {Object} props - Component props
 * @param {string} [props.type='text'] - Input type
 * @param {string} [props.error] - Error message
 * @param {string} [props.className] - Additional CSS classes
 */
const Input = React.forwardRef(({
  type = 'text',
  error,
  className,
  ...props
}, ref) => (
  <input
    type={type}
    ref={ref}
    className={cn(
      // Base styles
      'flex h-10 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm',
      'ring-offset-background',
      // File input styles
      'file:border-0 file:bg-transparent file:text-sm file:font-medium',
      // Placeholder styles
      'placeholder:text-muted-foreground',
      // Focus styles
      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
      // Disabled styles
      'disabled:cursor-not-allowed disabled:opacity-50',
      // Hover styles
      'transition-all duration-200 hover:border-primary/50',
      // Error styles
      error && 'border-red-500 focus-visible:ring-red-500',
      className
    )}
    aria-invalid={error ? 'true' : undefined}
    {...props}
  />
));
Input.displayName = 'Input';

/**
 * Input with Label and Error
 */
const InputField = React.forwardRef(({
  label,
  error,
  helperText,
  required,
  id,
  className,
  ...props
}, ref) => {
  const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;

  return (
    <div className={cn('space-y-2', className)}>
      {label && (
        <label
          htmlFor={inputId}
          className={cn(
            'text-sm font-medium leading-none',
            'peer-disabled:cursor-not-allowed peer-disabled:opacity-70'
          )}
        >
          {label}
          {required && <span className="text-red-500 ml-0.5">*</span>}
        </label>
      )}
      <Input
        ref={ref}
        id={inputId}
        error={error}
        aria-describedby={error ? `${inputId}-error` : helperText ? `${inputId}-helper` : undefined}
        {...props}
      />
      {error && (
        <p id={`${inputId}-error`} className="text-xs text-red-500">
          {error}
        </p>
      )}
      {!error && helperText && (
        <p id={`${inputId}-helper`} className="text-xs text-muted-foreground">
          {helperText}
        </p>
      )}
    </div>
  );
});
InputField.displayName = 'InputField';

/**
 * Search Input with Icon
 */
const SearchInput = React.forwardRef(({
  className,
  ...props
}, ref) => (
  <div className="relative">
    <svg
      className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground"
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <circle cx="11" cy="11" r="8" />
      <path d="m21 21-4.3-4.3" />
    </svg>
    <Input
      ref={ref}
      type="search"
      className={cn('pl-9', className)}
      {...props}
    />
  </div>
));
SearchInput.displayName = 'SearchInput';

export { Input, InputField, SearchInput };
export default Input;
