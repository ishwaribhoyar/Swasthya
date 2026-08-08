import { AlertCircle, RefreshCw } from 'lucide-react';
import { motion } from 'framer-motion';

interface ErrorComponentProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export default function ErrorComponent({ title = 'Error', message, onRetry }: ErrorComponentProps) {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col items-center justify-center p-8 text-center bg-red-50 rounded-xl border border-red-100"
    >
      <div className="h-12 w-12 rounded-full bg-red-100 flex items-center justify-center mb-4">
        <AlertCircle className="h-6 w-6 text-red-600" />
      </div>
      <h3 className="text-lg font-semibold text-slate-900 mb-2">{title}</h3>
      <p className="text-sm text-slate-600 mb-6 max-w-md">{message}</p>
      
      {onRetry && (
        <button
          onClick={onRetry}
          className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-md text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors shadow-sm"
        >
          <RefreshCw className="h-4 w-4" />
          Try Again
        </button>
      )}
    </motion.div>
  );
}
