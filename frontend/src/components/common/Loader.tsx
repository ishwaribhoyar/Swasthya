import { motion } from 'framer-motion';
import { Loader2 } from 'lucide-react';
import { cn } from '@/utils/helpers';

interface LoaderProps {
  fullScreen?: boolean;
  size?: 'sm' | 'md' | 'lg';
  text?: string;
  label?: string;
  className?: string;
}

export default function Loader({ fullScreen = false, size = 'md', text, label, className }: LoaderProps) {
  const displayText = text || label;

  const sizeMap = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
  };

  const content = (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className={cn("flex flex-col items-center justify-center gap-3 text-primary", className)}
    >
      <Loader2 className={cn("animate-spin", sizeMap[size])} />
      {displayText && <p className="text-sm font-medium text-slate-500">{displayText}</p>}
    </motion.div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-white/80 backdrop-blur-sm">
        {content}
      </div>
    );
  }

  return content;
}
