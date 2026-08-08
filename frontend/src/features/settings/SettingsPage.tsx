import { useState } from 'react';
import { CheckCircle2, AlertCircle, User, Mail } from 'lucide-react';


import PageLayout from '@/components/common/PageLayout';
import { useAuth } from '@/hooks/useAuth';
import client from '@/services/api/client';

export default function SettingsPage() {
  const { user } = useAuth();
  const [activeSection, setActiveSection] = useState('profile');
  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'success' | 'error'>('idle');

  // Profile form state — initialised from JWT user object
  const [firstName, setFirstName] = useState(user?.firstName || '');
  const [lastName, setLastName] = useState(user?.lastName || '');

  const sections = [
    { id: 'profile', label: 'Profile' },
    { id: 'security', label: 'Security' },
    { id: 'notifications', label: 'Notifications' },
    { id: 'preferences', label: 'Preferences' },
  ];

  const handleSaveProfile = async () => {
    if (!firstName.trim() || !lastName.trim()) return;
    try {
      setSaving(true);
      setSaveStatus('idle');
      await client.patch('/auth/me', {
        first_name: firstName.trim(),
        last_name: lastName.trim(),
      });
      setSaveStatus('success');
      setTimeout(() => setSaveStatus('idle'), 3000);
    } catch (err) {
      setSaveStatus('error');
      setTimeout(() => setSaveStatus('idle'), 4000);
    } finally {
      setSaving(false);
    }
  };

  return (
    <PageLayout title="Settings" description="Manage your clinician profile and practice preferences.">
      <div className="flex flex-col md:flex-row gap-6">
        {/* Sidebar nav */}
        <div className="w-full md:w-56 flex-shrink-0">
          <nav className="flex flex-col space-y-1">
            {sections.map((section) => (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                className={`text-left px-4 py-2.5 text-sm font-medium rounded-md transition-colors ${
                  activeSection === section.id
                    ? 'bg-primary/10 text-primary'
                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                }`}
              >
                {section.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Content panel */}
        <div className="flex-1 bg-white rounded-xl border border-slate-200 shadow-sm p-6 min-h-[400px]">
          {activeSection === 'profile' && (
            <>
              <h3 className="text-lg font-semibold text-slate-900 mb-6">Clinician Profile</h3>

              {saveStatus === 'success' && (
                <div className="mb-4 flex items-center gap-2 text-sm text-emerald-700 bg-emerald-50 border border-emerald-200 px-4 py-3 rounded-lg">
                  <CheckCircle2 className="h-4 w-4 shrink-0" />
                  Profile updated successfully.
                </div>
              )}
              {saveStatus === 'error' && (
                <div className="mb-4 flex items-center gap-2 text-sm text-red-700 bg-red-50 border border-red-200 px-4 py-3 rounded-lg">
                  <AlertCircle className="h-4 w-4 shrink-0" />
                  Failed to save profile. Please try again.
                </div>
              )}

              <div className="space-y-5 max-w-lg">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">
                      First Name
                    </label>
                    <div className="relative">
                      <User className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                      <input
                        type="text"
                        value={firstName}
                        onChange={(e) => setFirstName(e.target.value)}
                        className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-md text-slate-900 text-sm focus:ring-2 focus:ring-primary/30 focus:border-primary outline-none"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">
                      Last Name
                    </label>
                    <div className="relative">
                      <User className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                      <input
                        type="text"
                        value={lastName}
                        onChange={(e) => setLastName(e.target.value)}
                        className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-md text-slate-900 text-sm focus:ring-2 focus:ring-primary/30 focus:border-primary outline-none"
                      />
                    </div>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1.5">
                    Email Address
                  </label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                    <input
                      type="email"
                      disabled
                      value={user?.email || ''}
                      className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-md bg-slate-50 text-slate-500 font-medium text-sm cursor-not-allowed"
                    />
                  </div>
                  <p className="text-xs text-slate-400 mt-1">Email cannot be changed after registration.</p>
                </div>

                <div className="pt-2">
                  <button
                    onClick={handleSaveProfile}
                    disabled={saving || !firstName.trim() || !lastName.trim()}
                    className="flex items-center gap-2 bg-primary text-white px-5 py-2 rounded-md font-medium text-sm hover:bg-primary/90 transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {saving ? (
                      <>
                        <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                        </svg>
                        Saving...
                      </>
                    ) : (
                      'Save Profile Changes'
                    )}
                  </button>
                </div>
              </div>
            </>
          )}

          {activeSection === 'security' && (
            <>
              <h3 className="text-lg font-semibold text-slate-900 mb-6">Security Settings</h3>
              <div className="space-y-4 max-w-lg">
                <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800">
                  Password change functionality is available in Phase 6. JWT tokens expire in 60 minutes.
                </div>
              </div>
            </>
          )}

          {(activeSection === 'notifications' || activeSection === 'preferences') && (
            <>
              <h3 className="text-lg font-semibold text-slate-900 mb-6">
                {activeSection.charAt(0).toUpperCase() + activeSection.slice(1)}
              </h3>
              <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-600">
                These settings will be configurable in a future phase.
              </div>
            </>
          )}
        </div>
      </div>
    </PageLayout>
  );
}
