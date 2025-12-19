/**
 * Progress Component
 *
 * A progress indicator component for showing completion status.
 * Supports different styles and sizes.
 *
 * @example
 * <Progress value={75} />
 * <Progress value={50} variant="success" showLabel />
 */

import React from 'react';
import { cn } from '../hooks/utils';

// Progress variants
const progressVariants = {
  default: 'bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500',
  primary: 'bg-primary',
  success: 'bg-emerald-500',
  warning: 'bg-amber-500',
  danger: 'bg-red-500',
  neon: 'bg-gradient-to-r from-neon-blue to-neon-purple',
};

/**
 * Progress Component
 *
 * @param {Object} props - Component props
 * @param {number} props.value - Progress value (0-100)
 * @param {string} [props.variant='default'] - Progress variant
 * @param {string} [props.size='default'] - Progress size
 * @param {boolean} [props.showLabel=false] - Show percentage label
 * @param {string} [props.className] - Additional CSS classes
 */
const Progress = React.forwardRef(({
  value = 0,
  variant = 'default',
  size = 'default',
  showLabel = false,
  className,
  ...props
}, ref) => {
  const clampedValue = Math.min(100, Math.max(0, value));

  const sizes = {
    sm: 'h-2',
    default: 'h-3',
    lg: 'h-4',
  };

  return (
    <div className={cn('space-y-1', className)}>
      {showLabel && (
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Progress</span>
          <span className="font-medium">{clampedValue}%</span>
        </div>
      )}
      <div
        ref={ref}
        role="progressbar"
        aria-valuenow={clampedValue}
        aria-valuemin={0}
        aria-valuemax={100}
        className={cn(
          'relative w-full overflow-hidden rounded-full bg-secondary',
          sizes[size]
        )}
        {...props}
      >
        <div
          className={cn(
            'h-full w-full flex-1 transition-all duration-500 ease-out',
            progressVariants[variant]
          )}
          style={{ transform: `translateX(-${100 - clampedValue}%)` }}
        />
      </div>
    </div>
  );
});
Progress.displayName = 'Progress';

/**
 * Circular Progress
 */
const CircularProgress = ({
  value = 0,
  size = 120,
  strokeWidth = 8,
  variant = 'default',
  showLabel = true,
  className,
}) => {
  const clampedValue = Math.min(100, Math.max(0, value));
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (clampedValue / 100) * circumference;

  const colors = {
    default: '#6366f1',
    primary: 'hsl(var(--primary))',
    success: '#10b981',
    warning: '#f59e0b',
    danger: '#ef4444',
    neon: '#00f2ea',
  };

  return (
    <div className={cn('relative inline-flex', className)}>
      <svg width={size} height={size} className="transform -rotate-90">
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="hsl(var(--secondary))"
          strokeWidth={strokeWidth}
        />
        {/* Progress circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={colors[variant]}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-500 ease-out"
        />
      </svg>
      {showLabel && (
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-lg font-semibold">{clampedValue}%</span>
        </div>
      )}
    </div>
  );
};

/**
 * Step Progress
 */
const StepProgress = ({
  steps = [],
  currentStep = 0,
  className,
}) => (
  <div className={cn('flex items-center', className)}>
    {steps.map((step, index) => (
      <React.Fragment key={index}>
        {/* Step indicator */}
        <div className="flex items-center">
          <div
            className={cn(
              'flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium transition-colors',
              index < currentStep
                ? 'bg-primary text-primary-foreground'
                : index === currentStep
                  ? 'bg-primary text-primary-foreground ring-4 ring-primary/20'
                  : 'bg-muted text-muted-foreground'
            )}
          >
            {index < currentStep ? (
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            ) : (
              index + 1
            )}
          </div>
          <span className="ml-2 text-sm font-medium hidden sm:block">{step}</span>
        </div>

        {/* Connector line */}
        {index < steps.length - 1 && (
          <div
            className={cn(
              'mx-4 h-0.5 flex-1 transition-colors',
              index < currentStep ? 'bg-primary' : 'bg-muted'
            )}
          />
        )}
      </React.Fragment>
    ))}
  </div>
);

export { Progress, CircularProgress, StepProgress, progressVariants };
export default Progress;
