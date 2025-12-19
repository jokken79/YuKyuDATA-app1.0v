/**
 * Badge Component
 *
 * A small status indicator component with multiple variants.
 * Used for labels, tags, and status indicators.
 *
 * @example
 * <Badge variant="success">Active</Badge>
 * <Badge variant="warning">Pending</Badge>
 */

import React from 'react';
import { cn } from '../hooks/utils';

// Badge variants
const badgeVariants = {
  default: 'border-transparent bg-primary text-primary-foreground hover:bg-primary/80',
  secondary: 'border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80',
  destructive: 'border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80',
  outline: 'text-foreground border-border',
  success: 'border-transparent bg-emerald-500/10 text-emerald-500 border-emerald-500/20',
  warning: 'border-transparent bg-amber-500/10 text-amber-500 border-amber-500/20',
  danger: 'border-transparent bg-red-500/10 text-red-500 border-red-500/20',
  info: 'border-transparent bg-blue-500/10 text-blue-500 border-blue-500/20',
};

/**
 * Badge Component
 *
 * @param {Object} props - Component props
 * @param {string} [props.variant='default'] - Badge variant
 * @param {string} [props.className] - Additional CSS classes
 * @param {React.ReactNode} props.children - Badge content
 */
const Badge = React.forwardRef(({
  variant = 'default',
  className,
  children,
  ...props
}, ref) => (
  <div
    ref={ref}
    className={cn(
      'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold',
      'transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
      badgeVariants[variant],
      className
    )}
    {...props}
  >
    {children}
  </div>
));
Badge.displayName = 'Badge';

/**
 * Status Badge with Dot Indicator
 */
const StatusBadge = ({ status, children, className, ...props }) => {
  const statusColors = {
    active: 'bg-emerald-500',
    inactive: 'bg-slate-400',
    pending: 'bg-amber-500',
    error: 'bg-red-500',
  };

  return (
    <Badge variant="outline" className={cn('gap-1.5', className)} {...props}>
      <span className={cn('w-1.5 h-1.5 rounded-full', statusColors[status] || statusColors.inactive)} />
      {children}
    </Badge>
  );
};

/**
 * Count Badge (for notifications)
 */
const CountBadge = ({ count, max = 99, className, ...props }) => {
  const displayCount = count > max ? `${max}+` : count;

  if (count <= 0) return null;

  return (
    <span
      className={cn(
        'inline-flex items-center justify-center min-w-[1.25rem] h-5 px-1.5 rounded-full',
        'text-xs font-bold text-white bg-red-500',
        'shadow-lg shadow-red-500/50',
        className
      )}
      {...props}
    >
      {displayCount}
    </span>
  );
};

export { Badge, StatusBadge, CountBadge, badgeVariants };
export default Badge;
