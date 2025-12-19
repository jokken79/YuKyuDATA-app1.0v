/**
 * Dashboard Example
 *
 * Shows how to use the theme components to build a dashboard.
 * This example demonstrates cards, stats, tables, and navigation.
 */

import React from 'react';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  GlassCard,
  Badge,
  Button,
  Progress,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  SkeletonStatsCard,
} from '../components';
import { formatYen, getProfitBgColor, cn } from '../hooks/utils';

/**
 * Stats Card Component
 * Displays a metric with icon and trend indicator.
 */
const StatsCard = ({ title, value, subtitle, icon: Icon, trend, variant = 'default' }) => {
  const variantStyles = {
    default: 'glass-card',
    success: 'bg-emerald-500/10 border border-emerald-500/20',
    warning: 'bg-amber-500/10 border border-amber-500/20',
    gradient: 'bg-gradient-to-br from-primary via-blue-600 to-indigo-600 text-white border-0',
  };

  const iconStyles = {
    default: 'bg-cyan-500/10 text-cyan-400',
    success: 'bg-emerald-500/10 text-emerald-400',
    warning: 'bg-amber-500/10 text-amber-400',
    gradient: 'bg-white/20 text-white',
  };

  return (
    <GlassCard
      variant={variant === 'gradient' ? 'neo' : 'default'}
      className={cn(
        'relative overflow-hidden p-6 transition-all duration-300 hover:shadow-lg hover:-translate-y-1',
        variantStyles[variant]
      )}
    >
      {/* Background decoration */}
      {Icon && (
        <div className="absolute top-0 right-0 w-32 h-32 -mr-8 -mt-8 opacity-10">
          <Icon className="w-full h-full" />
        </div>
      )}

      <div className="relative flex items-start justify-between">
        <div className="space-y-2">
          <p className={cn(
            'text-sm font-medium',
            variant === 'gradient' ? 'text-white/80' : 'text-muted-foreground'
          )}>
            {title}
          </p>
          <p className="text-3xl font-bold tracking-tight">
            {value}
          </p>
          {(subtitle || trend) && (
            <div className="flex items-center gap-2">
              {trend && (
                <span className={cn(
                  'text-sm font-medium',
                  trend > 0 ? 'text-emerald-500' : 'text-red-500'
                )}>
                  {trend > 0 ? '+' : ''}{trend}%
                </span>
              )}
              {subtitle && (
                <span className={cn(
                  'text-sm',
                  variant === 'gradient' ? 'text-white/70' : 'text-muted-foreground'
                )}>
                  {subtitle}
                </span>
              )}
            </div>
          )}
        </div>

        {Icon && (
          <div className={cn('rounded-xl p-3', iconStyles[variant])}>
            <Icon className="w-6 h-6" />
          </div>
        )}
      </div>
    </GlassCard>
  );
};

/**
 * Dashboard Example Component
 */
export default function DashboardExample() {
  // Sample data
  const employees = [
    { id: 'E001', name: 'Yamada Taro', rate: 1200, billing: 1500, margin: 20 },
    { id: 'E002', name: 'Suzuki Hanako', rate: 1100, billing: 1400, margin: 21.4 },
    { id: 'E003', name: 'Tanaka Jiro', rate: 1000, billing: 1250, margin: 20 },
  ];

  const isLoading = false;

  return (
    <div className="min-h-screen bg-background">
      {/* Stats Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 mb-8">
        {isLoading ? (
          <>
            <SkeletonStatsCard />
            <SkeletonStatsCard />
            <SkeletonStatsCard />
            <SkeletonStatsCard />
          </>
        ) : (
          <>
            <StatsCard
              title="Total Employees"
              value="156"
              subtitle="Active"
              trend={5.2}
              variant="gradient"
            />
            <StatsCard
              title="Monthly Revenue"
              value={formatYen(12500000)}
              subtitle="This month"
              trend={8.1}
              variant="success"
            />
            <StatsCard
              title="Profit Margin"
              value="18.5%"
              subtitle="Average"
              trend={-2.3}
              variant="warning"
            />
            <StatsCard
              title="Pending Payroll"
              value="23"
              subtitle="Records"
            />
          </>
        )}
      </div>

      {/* Main Content Grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Employee Table */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Employee Overview</CardTitle>
                <CardDescription>Recent employee performance</CardDescription>
              </div>
              <Button variant="outline" size="sm">View All</Button>
            </div>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Hourly Rate</TableHead>
                  <TableHead>Billing Rate</TableHead>
                  <TableHead>Margin</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {employees.map((emp) => (
                  <TableRow key={emp.id}>
                    <TableCell className="font-mono">{emp.id}</TableCell>
                    <TableCell className="font-medium">{emp.name}</TableCell>
                    <TableCell>{formatYen(emp.rate)}</TableCell>
                    <TableCell>{formatYen(emp.billing)}</TableCell>
                    <TableCell>
                      <Badge className={getProfitBgColor(emp.margin)}>
                        {emp.margin}%
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* Side Panel */}
        <div className="space-y-6">
          {/* Progress Card */}
          <Card>
            <CardHeader>
              <CardTitle>Monthly Target</CardTitle>
              <CardDescription>Progress toward revenue goal</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Progress value={75} showLabel variant="neon" />
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Current</span>
                <span className="font-medium">{formatYen(12500000)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Target</span>
                <span className="font-medium">{formatYen(16000000)}</span>
              </div>
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button variant="default" className="w-full justify-start">
                Upload Payroll
              </Button>
              <Button variant="outline" className="w-full justify-start">
                Generate Report
              </Button>
              <Button variant="ghost" className="w-full justify-start">
                View Settings
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
