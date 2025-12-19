/**
 * Skeleton Component
 *
 * Loading placeholder components for content that is being fetched.
 * Provides visual feedback while data is loading.
 *
 * @example
 * <Skeleton className="h-4 w-[200px]" />
 * <SkeletonCard />
 * <SkeletonTable rows={5} />
 */

import React from 'react';
import { cn } from '../hooks/utils';

/**
 * Base Skeleton Component
 *
 * @param {Object} props - Component props
 * @param {string} [props.className] - Additional CSS classes
 */
const Skeleton = ({ className, ...props }) => (
  <div
    className={cn('animate-pulse rounded-md bg-muted', className)}
    aria-hidden="true"
    {...props}
  />
);

/**
 * Skeleton Text Line
 */
const SkeletonText = ({ lines = 1, className }) => (
  <div className={cn('space-y-2', className)}>
    {Array.from({ length: lines }).map((_, i) => (
      <Skeleton
        key={i}
        className={cn(
          'h-4',
          i === lines - 1 && lines > 1 ? 'w-3/4' : 'w-full'
        )}
      />
    ))}
  </div>
);

/**
 * Skeleton Circle (for avatars)
 */
const SkeletonCircle = ({ size = 'md', className }) => {
  const sizes = {
    sm: 'h-8 w-8',
    md: 'h-10 w-10',
    lg: 'h-12 w-12',
    xl: 'h-16 w-16',
  };

  return <Skeleton className={cn('rounded-full', sizes[size], className)} />;
};

/**
 * Skeleton Card
 */
const SkeletonCard = ({ className }) => (
  <div className={cn('rounded-xl border bg-card p-6 space-y-4', className)}>
    <div className="flex items-center gap-4">
      <SkeletonCircle />
      <div className="space-y-2 flex-1">
        <Skeleton className="h-4 w-1/4" />
        <Skeleton className="h-3 w-1/2" />
      </div>
    </div>
    <SkeletonText lines={3} />
    <div className="flex gap-2">
      <Skeleton className="h-9 w-20" />
      <Skeleton className="h-9 w-20" />
    </div>
  </div>
);

/**
 * Skeleton Table Row
 */
const SkeletonTableRow = ({ columns = 5 }) => (
  <tr className="border-b">
    {Array.from({ length: columns }).map((_, i) => (
      <td key={i} className="px-4 py-3">
        <Skeleton className="h-4 w-full" />
      </td>
    ))}
  </tr>
);

/**
 * Skeleton Table
 */
const SkeletonTable = ({ rows = 5, columns = 5, className }) => (
  <div className={cn('rounded-lg border overflow-hidden', className)}>
    <table className="w-full">
      <thead>
        <tr className="border-b bg-muted/50">
          {Array.from({ length: columns }).map((_, i) => (
            <th key={i} className="px-4 py-3 text-left">
              <Skeleton className="h-4 w-20" />
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {Array.from({ length: rows }).map((_, i) => (
          <SkeletonTableRow key={i} columns={columns} />
        ))}
      </tbody>
    </table>
  </div>
);

/**
 * Skeleton Stats Card
 */
const SkeletonStatsCard = ({ className }) => (
  <div className={cn('rounded-xl border bg-card p-6', className)}>
    <div className="flex items-start justify-between">
      <div className="space-y-2 flex-1">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-8 w-32" />
        <Skeleton className="h-3 w-20" />
      </div>
      <Skeleton className="h-12 w-12 rounded-xl" />
    </div>
  </div>
);

/**
 * Skeleton List Item
 */
const SkeletonListItem = ({ className }) => (
  <div className={cn('flex items-center gap-4 p-4', className)}>
    <SkeletonCircle />
    <div className="space-y-2 flex-1">
      <Skeleton className="h-4 w-1/3" />
      <Skeleton className="h-3 w-1/2" />
    </div>
    <Skeleton className="h-8 w-8 rounded" />
  </div>
);

/**
 * Skeleton Chart
 */
const SkeletonChart = ({ height = 300, className }) => (
  <div className={cn('rounded-xl border bg-card p-6', className)}>
    <div className="flex items-center justify-between mb-6">
      <Skeleton className="h-5 w-32" />
      <div className="flex gap-2">
        <Skeleton className="h-8 w-20" />
        <Skeleton className="h-8 w-20" />
      </div>
    </div>
    <Skeleton className="w-full rounded-lg" style={{ height }} />
  </div>
);

export {
  Skeleton,
  SkeletonText,
  SkeletonCircle,
  SkeletonCard,
  SkeletonTable,
  SkeletonTableRow,
  SkeletonStatsCard,
  SkeletonListItem,
  SkeletonChart,
};
export default Skeleton;
