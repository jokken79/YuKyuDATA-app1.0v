/**
 * Alert Component
 *
 * A notification/alert component for displaying messages.
 * Supports different variants for different message types.
 *
 * @example
 * <Alert variant="success">
 *   <AlertTitle>Success!</AlertTitle>
 *   <AlertDescription>Your changes have been saved.</AlertDescription>
 * </Alert>
 */

import React from 'react';
import { cn } from '../hooks/utils';

// Alert variants
const alertVariants = {
  default: 'bg-background text-foreground border-border',
  info: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
  success: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20',
  warning: 'bg-amber-500/10 text-amber-500 border-amber-500/20',
  destructive: 'bg-red-500/10 text-red-500 border-red-500/20',
};

// Alert icons
const alertIcons = {
  default: null,
  info: (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  success: (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  warning: (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>
  ),
  destructive: (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
};

/**
 * Alert Component
 *
 * @param {Object} props - Component props
 * @param {string} [props.variant='default'] - Alert variant
 * @param {boolean} [props.dismissible=false] - Show dismiss button
 * @param {Function} [props.onDismiss] - Dismiss handler
 * @param {React.ReactNode} props.children - Alert content
 */
const Alert = React.forwardRef(({
  variant = 'default',
  dismissible = false,
  onDismiss,
  className,
  children,
  ...props
}, ref) => (
  <div
    ref={ref}
    role="alert"
    className={cn(
      'relative w-full rounded-lg border p-4',
      alertVariants[variant],
      className
    )}
    {...props}
  >
    <div className="flex gap-3">
      {/* Icon */}
      {alertIcons[variant] && (
        <div className="shrink-0" aria-hidden="true">
          {alertIcons[variant]}
        </div>
      )}

      {/* Content */}
      <div className="flex-1">{children}</div>

      {/* Dismiss button */}
      {dismissible && (
        <button
          onClick={onDismiss}
          className="shrink-0 rounded-full p-1 hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
          aria-label="Dismiss"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}
    </div>
  </div>
));
Alert.displayName = 'Alert';

/**
 * Alert Title
 */
const AlertTitle = React.forwardRef(({ className, ...props }, ref) => (
  <h5
    ref={ref}
    className={cn('font-medium leading-none tracking-tight', className)}
    {...props}
  />
));
AlertTitle.displayName = 'AlertTitle';

/**
 * Alert Description
 */
const AlertDescription = React.forwardRef(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn('text-sm mt-1 [&_p]:leading-relaxed', className)}
    {...props}
  />
));
AlertDescription.displayName = 'AlertDescription';

export { Alert, AlertTitle, AlertDescription, alertVariants };
export default Alert;
