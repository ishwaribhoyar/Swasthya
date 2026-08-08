import { NavLink } from 'react-router-dom';
import { motion } from 'framer-motion';
import { LayoutDashboard, Users, Activity, PieChart, Bot, Settings, Menu } from 'lucide-react';
import { useGlobalContext } from '@/contexts/GlobalContext';
import { ROUTES } from '@/utils/constants';
import { cn } from '@/utils/helpers';

const navItems = [
  { icon: LayoutDashboard, label: 'Dashboard', path: ROUTES.DASHBOARD },
  { icon: Users, label: 'Patients', path: ROUTES.PATIENTS },
  { icon: Activity, label: 'Timeline', path: ROUTES.TIMELINE },
  { icon: PieChart, label: 'Analytics', path: ROUTES.ANALYTICS },
  { icon: Bot, label: 'AI Assistant', path: ROUTES.ASSISTANT },
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
            <span className="text-xl font-bold text-primary">ClinIQ</span>
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
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
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
        ))}
      </nav>
    </motion.aside>
  );
}
