import { Outlet } from 'react-router-dom';
import { motion } from 'framer-motion';
import Sidebar from '@/components/common/Sidebar';
import Navbar from '@/components/common/Navbar';
import { useGlobalContext } from '@/contexts/GlobalContext';
import { cn } from '@/utils/helpers';

export default function AppLayout() {
  const { isSidebarOpen } = useGlobalContext();

  return (
    <div className="min-h-screen flex bg-background">
      <Sidebar />
      <div className={cn(
        "flex-1 flex flex-col min-h-screen transition-all duration-300",
        isSidebarOpen ? "ml-64" : "ml-20"
      )}>
        <Navbar />
        <main className="flex-1 p-6 md:p-8 overflow-x-hidden">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3 }}
            className="h-full"
          >
            <Outlet />
          </motion.div>
        </main>
      </div>
    </div>
  );
}
