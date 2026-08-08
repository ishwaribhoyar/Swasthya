import { Search, X } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useDebounce } from '@/hooks/useDebounce';
import { cn } from '@/utils/helpers';

interface SearchBarProps {
  onSearch: (value: string) => void;
  placeholder?: string;
  fullWidth?: boolean;
}

export default function SearchBar({ onSearch, placeholder = 'Search...', fullWidth = false }: SearchBarProps) {
  const [value, setValue] = useState('');
  const debouncedValue = useDebounce(value, 300);

  useEffect(() => {
    onSearch(debouncedValue);
  }, [debouncedValue, onSearch]);

  return (
    <div className={cn("relative", fullWidth ? "w-full" : "w-64")}>
      <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder={placeholder}
        className="h-9 w-full rounded-md border border-slate-200 bg-white pl-9 pr-8 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary shadow-sm"
      />
      {value && (
        <button
          onClick={() => setValue('')}
          className="absolute right-2 top-2.5 text-slate-400 hover:text-slate-600"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}
