import { Bell, Search, User } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';

export default function Navbar() {
  const { user, logout } = useAuth();

  return (
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b bg-white px-6 shadow-sm">
      <div className="flex items-center gap-4 flex-1">
        <div className="relative w-64">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search patients, records..."
            className="h-9 w-full rounded-md border border-slate-200 bg-slate-50 pl-9 pr-4 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
          />
        </div>
      </div>

      <div className="flex items-center gap-4">
        <button className="relative rounded-full p-2 hover:bg-slate-100">
          <Bell className="h-5 w-5 text-slate-600" />
          <span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-red-500"></span>
        </button>
        
        <div className="flex items-center gap-3 border-l pl-4">
          <div className="flex flex-col items-end">
            <span className="text-sm font-medium">{user?.firstName} {user?.lastName}</span>
            <span className="text-xs text-slate-500">{user?.email}</span>
          </div>
          <button 
            onClick={logout}
            title="Sign out"
            className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/10 text-primary hover:bg-primary/20"
          >
            <User className="h-5 w-5" />
          </button>
        </div>
      </div>
    </header>
  );
}
