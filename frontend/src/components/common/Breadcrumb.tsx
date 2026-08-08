import { ChevronRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { IBreadcrumb } from '@/types/common';

interface BreadcrumbProps {
  items: IBreadcrumb[];
}

export default function Breadcrumb({ items }: BreadcrumbProps) {
  return (
    <nav className="flex" aria-label="Breadcrumb">
      <ol className="inline-flex items-center space-x-1 md:space-x-2 text-sm text-slate-500">
        {items.map((item, index) => {
          const isLast = index === items.length - 1;
          
          return (
            <li key={item.label} className="inline-flex items-center">
              {index > 0 && <ChevronRight className="h-4 w-4 mx-1 text-slate-400" />}
              {isLast || !item.href ? (
                <span className="font-medium text-slate-900" aria-current="page">
                  {item.label}
                </span>
              ) : (
                <Link
                  to={item.href}
                  className="inline-flex items-center hover:text-primary transition-colors"
                >
                  {item.label}
                </Link>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
