/**
 * Navigation Components
 *
 * Sidebar and header navigation components with glass effects.
 * Includes mobile responsive behavior.
 *
 * @example
 * <Sidebar items={navItems} />
 * <Header onMenuClick={() => {}} />
 */

import React, { useState } from 'react';
import { cn } from '../hooks/utils';

/**
 * Navigation Item
 */
const NavItem = ({
  href,
  icon: Icon,
  label,
  description,
  isActive = false,
  isCollapsed = false,
  onClick,
  className,
}) => {
  const Component = href ? 'a' : 'button';

  return (
    <Component
      href={href}
      onClick={onClick}
      className={cn(
        'group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-300',
        isActive
          ? 'bg-neon-blue/10 text-neon-blue border border-neon-blue/20 shadow-[0_0_15px_rgba(0,242,234,0.1)]'
          : 'text-muted-foreground hover:bg-black/5 dark:hover:bg-white/5 hover:text-foreground',
        className
      )}
      aria-current={isActive ? 'page' : undefined}
    >
      {Icon && (
        <Icon
          className={cn(
            'h-5 w-5 shrink-0 transition-transform duration-300',
            !isActive && 'group-hover:scale-110 group-hover:text-primary'
          )}
          aria-hidden="true"
        />
      )}
      {!isCollapsed && (
        <div className="flex flex-col overflow-hidden">
          <span className="whitespace-nowrap">{label}</span>
          {!isActive && description && (
            <span className="text-xs text-muted-foreground whitespace-nowrap group-hover:text-muted-foreground/80 transition-colors">
              {description}
            </span>
          )}
        </div>
      )}
      {isActive && !isCollapsed && (
        <div className="ml-auto h-1.5 w-1.5 rounded-full bg-neon-blue shadow-[0_0_10px_#00f2ea]" />
      )}
    </Component>
  );
};

/**
 * Sidebar Component
 */
const Sidebar = ({
  items = [],
  bottomItems = [],
  currentPath,
  collapsible = true,
  defaultCollapsed = false,
  className,
}) => {
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed);

  return (
    <aside
      className={cn(
        'fixed left-0 top-16 z-40 h-[calc(100vh-4rem)] border-r border-black/5 dark:border-white/10',
        'glass bg-white/70 dark:bg-black/40 backdrop-blur-xl',
        'hidden md:flex flex-col transition-all duration-300',
        isCollapsed ? 'w-20' : 'w-[280px]',
        className
      )}
    >
      <div className="flex flex-1 flex-col gap-2 p-4">
        {/* Main Navigation */}
        <nav className="flex flex-1 flex-col gap-1" aria-label="Main navigation">
          {items.map((item, index) => (
            <NavItem
              key={item.href || index}
              {...item}
              isActive={currentPath === item.href}
              isCollapsed={isCollapsed}
            />
          ))}
        </nav>

        {/* Bottom Navigation */}
        {bottomItems.length > 0 && (
          <div className="border-t border-border pt-4 mt-auto">
            {bottomItems.map((item, index) => (
              <NavItem
                key={item.href || index}
                {...item}
                isActive={currentPath === item.href}
                isCollapsed={isCollapsed}
              />
            ))}
          </div>
        )}

        {/* Collapse Toggle */}
        {collapsible && (
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="w-full mt-2 flex items-center justify-center gap-2 rounded-lg px-3 py-2.5 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
            aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            aria-expanded={!isCollapsed}
          >
            <svg
              className={cn('h-4 w-4 transition-transform', isCollapsed && 'rotate-180')}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            {!isCollapsed && <span>Collapse</span>}
          </button>
        )}
      </div>
    </aside>
  );
};

/**
 * Header Component
 */
const Header = ({
  logo,
  title,
  subtitle,
  rightContent,
  onMenuClick,
  className,
}) => (
  <header
    className={cn(
      'fixed top-0 left-0 right-0 z-50 w-full border-b border-black/5 dark:border-white/10',
      'glass bg-white/70 dark:bg-black/40 backdrop-blur-xl',
      className
    )}
  >
    <div className="flex h-16 items-center justify-between px-4 md:px-6">
      {/* Left side - Logo & Title */}
      <div className="flex items-center gap-4">
        {/* Mobile menu button */}
        <button
          onClick={onMenuClick}
          className="md:hidden rounded-lg p-2 text-muted-foreground hover:text-foreground hover:bg-muted"
          aria-label="Open menu"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        <div className="flex items-center gap-3">
          {logo}
          <div className="hidden sm:block">
            {title && (
              <h1 className="text-xl font-bold bg-gradient-to-r from-neon-blue to-neon-purple bg-clip-text text-transparent">
                {title}
              </h1>
            )}
            {subtitle && (
              <p className="text-xs text-muted-foreground">{subtitle}</p>
            )}
          </div>
        </div>
      </div>

      {/* Right side content */}
      {rightContent && (
        <div className="flex items-center gap-2">
          {rightContent}
        </div>
      )}
    </div>
  </header>
);

/**
 * Mobile Navigation Drawer
 */
const MobileNav = ({
  isOpen,
  onClose,
  items = [],
  currentPath,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-40 md:hidden">
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black/80 backdrop-blur-sm animate-fade-in"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer */}
      <aside className="fixed left-0 top-16 z-50 h-[calc(100vh-4rem)] w-72 border-r border-border bg-background p-4 animate-slide-in-left">
        <nav className="flex flex-col gap-1">
          {items.map((item, index) => (
            <NavItem
              key={item.href || index}
              {...item}
              isActive={currentPath === item.href}
              onClick={() => {
                item.onClick?.();
                onClose();
              }}
            />
          ))}
        </nav>
      </aside>
    </div>
  );
};

export { Sidebar, Header, NavItem, MobileNav };
export default Sidebar;
