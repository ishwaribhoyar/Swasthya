import { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Bell, Search, User, Bot, Sparkles, UserCheck, Loader2 } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { patientsApi } from '@/services/api/patients';
import { IPatientListItem } from '@/types/patients';
import { AICopilotDrawer } from '@/features/assistant/AICopilotDrawer';

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [isCopilotOpen, setIsCopilotOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<IPatientListItem[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  const searchRef = useRef<HTMLDivElement>(null);

  // Extract patient ID from route URL if currently on /patients/:id
  const patientMatch = location.pathname.match(/\/patients\/([a-zA-Z0-9-]+)/);
  const activePatientId = patientMatch && patientMatch[1] !== 'new' ? patientMatch[1] : null;

  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleOutsideClick);
    return () => document.removeEventListener('mousedown', handleOutsideClick);
  }, []);

  useEffect(() => {
    const timer = setTimeout(async () => {
      const q = searchQuery.trim();
      if (!q) {
        setSearchResults([]);
        setIsDropdownOpen(false);
        return;
      }

      setIsSearching(true);
      try {
        const res = await patientsApi.search(q);
        if (res.data) {
          setSearchResults(res.data);
          setIsDropdownOpen(true);
        }
      } catch (err) {
        console.error('Global search error:', err);
      } finally {
        setIsSearching(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  const handleSelectPatient = (patientId: string) => {
    setIsDropdownOpen(false);
    setSearchQuery('');
    navigate(`/patients/${patientId}`);
  };

  return (
    <>
      <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b bg-white px-6 shadow-sm">
        <div className="flex items-center gap-4 flex-1">
          <div ref={searchRef} className="relative w-80">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onFocus={() => searchQuery.trim() && setIsDropdownOpen(true)}
              placeholder="Global search (Name, MRN)..."
              className="h-9 w-full rounded-md border border-slate-200 bg-slate-50 pl-9 pr-8 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
            />
            {isSearching && (
              <Loader2 className="absolute right-2.5 top-2.5 h-4 w-4 text-slate-400 animate-spin" />
            )}

            {/* Instant Search Results Dropdown */}
            {isDropdownOpen && (
              <div className="absolute top-11 left-0 w-full bg-white rounded-lg border border-slate-200 shadow-lg overflow-hidden z-50">
                <div className="p-2 border-b bg-slate-50 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                  Patient Search Results ({searchResults.length})
                </div>

                {searchResults.length === 0 ? (
                  <div className="p-4 text-xs text-slate-500 text-center">
                    No matching patient records found.
                  </div>
                ) : (
                  <div className="max-h-64 overflow-y-auto divide-y divide-slate-100">
                    {searchResults.map((p) => (
                      <button
                        key={p.id}
                        onClick={() => handleSelectPatient(p.id)}
                        className="w-full p-2.5 text-left hover:bg-blue-50/50 transition-colors flex items-center justify-between group"
                      >
                        <div>
                          <div className="text-xs font-bold text-slate-900 group-hover:text-blue-700">
                            {p.first_name} {p.last_name}
                          </div>
                          <div className="text-[11px] text-slate-500">
                            MRN: <span className="font-mono text-slate-700">{p.mrn}</span> · {p.gender} ({p.age}y)
                          </div>
                        </div>
                        <UserCheck className="h-4 w-4 text-slate-400 group-hover:text-blue-600" />
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* AI Copilot Trigger Button */}
          <button
            onClick={() => setIsCopilotOpen(true)}
            className="flex items-center gap-2 px-3 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 rounded-lg text-xs font-semibold transition-colors shadow-2xs"
          >
            <Bot className="w-4 h-4 text-blue-600" />
            <span>AI Copilot</span>
            <Sparkles className="w-3 h-3 text-blue-500 animate-pulse" />
          </button>

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

      {/* Global AI Copilot Slide-over Drawer */}
      <AICopilotDrawer
        isOpen={isCopilotOpen}
        onClose={() => setIsCopilotOpen(false)}
        activePatientId={activePatientId}
      />
    </>
  );
}
