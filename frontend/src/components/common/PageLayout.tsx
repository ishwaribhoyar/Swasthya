import React from 'react';
import Breadcrumb from './Breadcrumb';
import { IBreadcrumb } from '@/types/common';

interface PageLayoutProps {
  title: string;
  description?: string;
  breadcrumbs?: IBreadcrumb[];
  action?: React.ReactNode;
  children: React.ReactNode;
}

export default function PageLayout({ title, description, breadcrumbs, action, children }: PageLayoutProps) {
  return (
    <div className="flex flex-col space-y-6">
      <div className="flex flex-col space-y-2 md:flex-row md:items-start md:justify-between md:space-y-0">
        <div>
          {breadcrumbs && breadcrumbs.length > 0 && (
            <div className="mb-2">
              <Breadcrumb items={breadcrumbs} />
            </div>
          )}
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">{title}</h1>
          {description && (
            <p className="text-sm text-slate-500 mt-1">{description}</p>
          )}
        </div>
        {action && (
          <div className="flex items-center space-x-2">
            {action}
          </div>
        )}
      </div>
      <div className="flex-1">
        {children}
      </div>
    </div>
  );
}
