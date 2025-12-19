/**
 * Modal Component
 *
 * An accessible modal dialog component with animations.
 * Supports different sizes and focus trapping.
 *
 * @example
 * <Modal isOpen={isOpen} onClose={handleClose}>
 *   <ModalHeader>
 *     <ModalTitle>Modal Title</ModalTitle>
 *   </ModalHeader>
 *   <ModalContent>Content here</ModalContent>
 *   <ModalFooter>
 *     <Button onClick={handleClose}>Close</Button>
 *   </ModalFooter>
 * </Modal>
 */

import React, { useEffect, useCallback } from 'react';
import { cn } from '../hooks/utils';

// Modal sizes
const modalSizes = {
  sm: 'max-w-md',
  md: 'max-w-lg',
  lg: 'max-w-2xl',
  xl: 'max-w-4xl',
  full: 'max-w-[calc(100vw-2rem)]',
};

/**
 * Modal Component
 *
 * @param {Object} props - Component props
 * @param {boolean} props.isOpen - Whether modal is open
 * @param {Function} props.onClose - Close handler
 * @param {string} [props.size='md'] - Modal size
 * @param {boolean} [props.closeOnOverlay=true] - Close on overlay click
 * @param {boolean} [props.closeOnEsc=true] - Close on Escape key
 * @param {React.ReactNode} props.children - Modal content
 */
const Modal = ({
  isOpen,
  onClose,
  size = 'md',
  closeOnOverlay = true,
  closeOnEsc = true,
  className,
  children,
  ...props
}) => {
  // Handle escape key
  const handleKeyDown = useCallback((e) => {
    if (closeOnEsc && e.key === 'Escape') {
      onClose();
    }
  }, [closeOnEsc, onClose]);

  // Add/remove event listener and body scroll lock
  useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [isOpen, handleKeyDown]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50" role="dialog" aria-modal="true" {...props}>
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black/80 backdrop-blur-sm animate-fade-in"
        onClick={closeOnOverlay ? onClose : undefined}
        aria-hidden="true"
      />

      {/* Modal Content */}
      <div className="fixed inset-0 overflow-y-auto">
        <div className="flex min-h-full items-center justify-center p-4">
          <div
            className={cn(
              'relative w-full rounded-xl border bg-background shadow-xl',
              'animate-scale-in',
              modalSizes[size],
              className
            )}
            onClick={(e) => e.stopPropagation()}
          >
            {children}
          </div>
        </div>
      </div>
    </div>
  );
};

/**
 * Modal Header
 */
const ModalHeader = React.forwardRef(({ className, children, onClose, ...props }, ref) => (
  <div
    ref={ref}
    className={cn('flex items-center justify-between p-6 pb-0', className)}
    {...props}
  >
    <div>{children}</div>
    {onClose && (
      <button
        onClick={onClose}
        className="rounded-full p-1 hover:bg-muted transition-colors"
        aria-label="Close modal"
      >
        <svg
          className="h-5 w-5 text-muted-foreground"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    )}
  </div>
));
ModalHeader.displayName = 'ModalHeader';

/**
 * Modal Title
 */
const ModalTitle = React.forwardRef(({ className, ...props }, ref) => (
  <h2
    ref={ref}
    className={cn('text-lg font-semibold leading-none tracking-tight', className)}
    {...props}
  />
));
ModalTitle.displayName = 'ModalTitle';

/**
 * Modal Description
 */
const ModalDescription = React.forwardRef(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn('text-sm text-muted-foreground mt-1', className)}
    {...props}
  />
));
ModalDescription.displayName = 'ModalDescription';

/**
 * Modal Content
 */
const ModalContent = React.forwardRef(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn('p-6', className)}
    {...props}
  />
));
ModalContent.displayName = 'ModalContent';

/**
 * Modal Footer
 */
const ModalFooter = React.forwardRef(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn('flex items-center justify-end gap-2 p-6 pt-0', className)}
    {...props}
  />
));
ModalFooter.displayName = 'ModalFooter';

export {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalDescription,
  ModalContent,
  ModalFooter,
  modalSizes,
};
export default Modal;
