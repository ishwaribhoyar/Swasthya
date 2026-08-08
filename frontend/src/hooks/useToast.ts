/**
 * useToast
 *
 * Application-level toast notification hook.
 * Manages a queue of toast messages with automatic dismissal after 3 seconds.
 * Supports three variants: default, success, and destructive (error).
 *
 * Phase 2: will be replaced with a Radix UI Toast integration when
 * the full shadcn/ui toast component is wired into the app shell.
 */
import { useState } from 'react';

export interface Toast {
  id: string;
  title?: string;
  description?: string;
  variant?: 'default' | 'destructive' | 'success';
}

export const useToast = () => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const toast = ({ title, description, variant = 'default' }: Omit<Toast, 'id'>) => {
    const id = Math.random().toString(36).substr(2, 9);
    setToasts((prev) => [...prev, { id, title, description, variant }]);
    
    // Auto dismiss after 3 seconds
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3000);
  };

  return { toast, toasts };
};
