/**
 * GlassCard Component
 *
 * A glassmorphism card component with blur effects.
 * Perfect for overlays, modals, and premium UI elements.
 *
 * @example
 * <GlassCard>
 *   <p>Content with glass effect</p>
 * </GlassCard>
 * <GlassCard variant="neo">Premium variant</GlassCard>
 */

import React from 'react';
import { cn } from '../hooks/utils';

/**
 * GlassCard Component
 *
 * @param {Object} props - Component props
 * @param {string} [props.variant='default'] - Card variant: 'default' or 'neo'
 * @param {boolean} [props.shimmer=false] - Enable shimmer effect on hover
 * @param {string} [props.className] - Additional CSS classes
 * @param {React.ReactNode} props.children - Card content
 */
const GlassCard = React.forwardRef(({
  variant = 'default',
  shimmer = false,
  className,
  children,
  ...props
}, ref) => (
  <div
    ref={ref}
    className={cn(
      'relative overflow-hidden rounded-xl shadow-sm backdrop-blur-md transition-all duration-300',
      // Border styling
      'border border-black/5 dark:border-white/10',
      // Default variant: White Glass (Light) vs Black Glass (Dark)
      variant === 'default' && 'bg-white/60 dark:bg-white/5 hover:bg-white/80 dark:hover:bg-white/10',
      // Neo variant: Gradient effect
      variant === 'neo' && 'bg-gradient-to-br from-white/80 to-white/40 dark:from-white/10 dark:to-transparent border-t-white/50 dark:border-t-white/20',
      // Shimmer group class
      shimmer && 'group',
      className
    )}
    {...props}
  >
    {/* Glossy reflection effect (shown on hover with shimmer) */}
    {shimmer && (
      <div
        className="pointer-events-none absolute -inset-full top-0 block h-full w-1/2 -skew-x-12 bg-gradient-to-r from-transparent to-white opacity-0 blur-md group-hover:opacity-40 dark:group-hover:opacity-10 group-hover:animate-shimmer"
        aria-hidden="true"
      />
    )}
    {children}
  </div>
));
GlassCard.displayName = 'GlassCard';

export { GlassCard };
export default GlassCard;
