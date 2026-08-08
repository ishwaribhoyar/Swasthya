import { NavLink } from 'react-router-dom';
import { motion } from 'framer-motion';
import { LayoutDashboard, Users, Activity, PieChart, Bot, Settings, Menu, Sparkles, ExternalLink } from 'lucide-react';
import { useGlobalContext } from '@/contexts/GlobalContext';
import { ROUTES } from '@/utils/constants';
import { cn } from '@/utils/helpers';

interface NavItem {
  icon: any;
  label: string;
  path?: string;
  href?: string;
  isExternal?: boolean;
}

const navItems: NavItem[] = [
  { icon: LayoutDashboard, label: 'Dashboard', path: ROUTES.DASHBOARD },
  { icon: Users, label: 'Patients', path: ROUTES.PATIENTS },
  { icon: Activity, label: 'Timeline', path: ROUTES.TIMELINE },
  { icon: PieChart, label: 'Analytics', path: ROUTES.ANALYTICS },
  { icon: Bot, label: 'AI Assistant', path: ROUTES.ASSISTANT },
  { 
    icon: Sparkles, 
    label: 'Medical Intelligence', 
    href: 'https://charging-lend-scoff.ngrok-free.dev', 
    isExternal: true 
  },
  { icon: Settings, label: 'Settings', path: ROUTES.SETTINGS },
];

export default function Sidebar() {
  const { isSidebarOpen, toggleSidebar } = useGlobalContext();

  return (
    <motion.aside 
      animate={{ width: isSidebarOpen ? 256 : 80 }}
      className="fixed left-0 top-0 z-40 h-screen border-r bg-white"
    >
      <div className="flex h-16 items-center justify-between px-4 border-b">
        {isSidebarOpen && (
          <div className="flex items-center gap-2 overflow-hidden whitespace-nowrap">
            <span className="text-2xl">🏥</span>
            <span className="text-xl font-bold text-primary">Swasthya</span>
          </div>
        )}
        <button 
          onClick={toggleSidebar}
          className="p-2 rounded-md hover:bg-slate-100 text-slate-500 mx-auto"
        >
          <Menu size={20} />
        </button>
      </div>
      
      <nav className="p-4 space-y-2">
        {navItems.map((item) => {
          if (item.isExternal && item.href) {
            return (
              <a
                key={item.href}
                href={item.href}
                target="_blank"
                rel="noopener noreferrer"
                title={item.label}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 transition-colors text-slate-600 hover:bg-slate-50 hover:text-slate-900 group",
                  !isSidebarOpen && "justify-center px-0"
                )}
              >
                <item.icon size={20} className="shrink-0 text-indigo-600 group-hover:text-indigo-700" />
                {isSidebarOpen && (
                  <span className="flex items-center justify-between w-full font-medium">
                    {item.label}
                    <ExternalLink size={14} className="text-slate-400 group-hover:text-slate-600 ml-1" />
                  </span>
                )}
              </a>
            );
          }

          return (
            <NavLink
              key={item.path!}
              to={item.path!}
              className={({ isActive }) => cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 transition-colors",
                isActive 
                  ? "bg-primary/10 text-primary font-medium" 
                  : "text-slate-600 hover:bg-slate-50 hover:text-slate-900",
                !isSidebarOpen && "justify-center px-0"
              )}
            >
              <item.icon size={20} className="shrink-0" />
              {isSidebarOpen && <span>{item.label}</span>}
            </NavLink>
          );
        })}
      </nav>
    </motion.aside>
  );
}
