import { useState } from 'react';
import { X, UserPlus, AlertCircle } from 'lucide-react';
import { IPatientCreate, BloodGroup, Gender } from '@/types/patients';

interface CreatePatientModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: IPatientCreate) => Promise<void>;
}

export default function CreatePatientModal({ isOpen, onClose, onSubmit }: CreatePatientModalProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState<IPatientCreate>({
    first_name: '',
    last_name: '',
    date_of_birth: '',
    gender: 'male',
    phone: '',
    email: '',
    blood_group: undefined,
    emergency_contact_name: '',
    emergency_contact_phone: '',
    address: '',
    allergies: '',
    chronic_conditions: '',
    notes: '',
  });

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.first_name || !formData.last_name || !formData.date_of_birth) {
      setError('First name, last name, and date of birth are required.');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const payload: IPatientCreate = {
        first_name: formData.first_name.trim(),
        last_name: formData.last_name.trim(),
        date_of_birth: formData.date_of_birth,
        gender: formData.gender,
        phone: formData.phone?.trim() || undefined,
        email: formData.email?.trim() || undefined,
        blood_group: formData.blood_group || undefined,
        emergency_contact_name: formData.emergency_contact_name?.trim() || undefined,
        emergency_contact_phone: formData.emergency_contact_phone?.trim() || undefined,
        address: formData.address?.trim() || undefined,
        allergies: formData.allergies?.trim() || undefined,
        chronic_conditions: formData.chronic_conditions?.trim() || undefined,
        notes: formData.notes?.trim() || undefined,
      };

      await onSubmit(payload);
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Failed to register patient.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4 overflow-y-auto">
      <div className="w-full max-w-2xl rounded-xl bg-white shadow-xl border border-slate-200 overflow-hidden my-8">
        <div className="flex items-center justify-between border-b px-6 py-4 bg-slate-50">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <UserPlus className="h-4 w-4" />
            </div>
            <h2 className="text-lg font-semibold text-slate-900">Register New Patient</h2>
          </div>
          <button onClick={onClose} className="rounded-lg p-1 text-slate-400 hover:bg-slate-200 hover:text-slate-600">
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6 max-h-[80vh] overflow-y-auto">
          {error && (
            <div className="flex items-center gap-2 rounded-lg bg-red-50 p-3 text-sm text-red-700 border border-red-200">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Demographics Section */}
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">Demographic Details</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">First Name *</label>
                <input
                  type="text"
                  required
                  value={formData.first_name}
                  onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                  placeholder="e.g. Eleanor"
                  className="w-full h-9 px-3 rounded-md border border-slate-200 text-sm focus:ring-2 focus:ring-primary/50 outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Last Name *</label>
                <input
                  type="text"
                  required
                  value={formData.last_name}
                  onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                  placeholder="e.g. Vance"
                  className="w-full h-9 px-3 rounded-md border border-slate-200 text-sm focus:ring-2 focus:ring-primary/50 outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Date of Birth *</label>
                <input
                  type="date"
                  required
                  value={formData.date_of_birth}
                  onChange={(e) => setFormData({ ...formData, date_of_birth: e.target.value })}
                  className="w-full h-9 px-3 rounded-md border border-slate-200 text-sm focus:ring-2 focus:ring-primary/50 outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Gender *</label>
                <select
                  value={formData.gender}
                  onChange={(e) => setFormData({ ...formData, gender: e.target.value as Gender })}
                  className="w-full h-9 px-3 rounded-md border border-slate-200 text-sm focus:ring-2 focus:ring-primary/50 outline-none bg-white"
                >
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Phone Number</label>
                <input
                  type="tel"
                  value={formData.phone || ''}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  placeholder="+1 (555) 019-2834"
                  className="w-full h-9 px-3 rounded-md border border-slate-200 text-sm focus:ring-2 focus:ring-primary/50 outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Blood Group</label>
                <select
                  value={formData.blood_group || ''}
                  onChange={(e) => setFormData({ ...formData, blood_group: (e.target.value || undefined) as BloodGroup })}
                  className="w-full h-9 px-3 rounded-md border border-slate-200 text-sm focus:ring-2 focus:ring-primary/50 outline-none bg-white"
                >
                  <option value="">Select Blood Group</option>
                  <option value="A+">A+</option>
                  <option value="A-">A-</option>
                  <option value="B+">B+</option>
                  <option value="B-">B-</option>
                  <option value="AB+">AB+</option>
                  <option value="AB-">AB-</option>
                  <option value="O+">O+</option>
                  <option value="O-">O-</option>
                </select>
              </div>
            </div>
          </div>

          {/* Contact & Address */}
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">Emergency Contact & Address</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Emergency Contact Name</label>
                <input
                  type="text"
                  value={formData.emergency_contact_name || ''}
                  onChange={(e) => setFormData({ ...formData, emergency_contact_name: e.target.value })}
                  placeholder="Contact Name"
                  className="w-full h-9 px-3 rounded-md border border-slate-200 text-sm focus:ring-2 focus:ring-primary/50 outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Emergency Contact Phone</label>
                <input
                  type="tel"
                  value={formData.emergency_contact_phone || ''}
                  onChange={(e) => setFormData({ ...formData, emergency_contact_phone: e.target.value })}
                  placeholder="Contact Phone"
                  className="w-full h-9 px-3 rounded-md border border-slate-200 text-sm focus:ring-2 focus:ring-primary/50 outline-none"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-xs font-medium text-slate-700 mb-1">Home Address</label>
                <input
                  type="text"
                  value={formData.address || ''}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  placeholder="Full street address..."
                  className="w-full h-9 px-3 rounded-md border border-slate-200 text-sm focus:ring-2 focus:ring-primary/50 outline-none"
                />
              </div>
            </div>
          </div>

          {/* Clinical Profile */}
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">Clinical Profile</h3>
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Known Allergies</label>
                <input
                  type="text"
                  value={formData.allergies || ''}
                  onChange={(e) => setFormData({ ...formData, allergies: e.target.value })}
                  placeholder="e.g. Penicillin, Latex, Peanuts"
                  className="w-full h-9 px-3 rounded-md border border-slate-200 text-sm focus:ring-2 focus:ring-primary/50 outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Chronic Conditions</label>
                <input
                  type="text"
                  value={formData.chronic_conditions || ''}
                  onChange={(e) => setFormData({ ...formData, chronic_conditions: e.target.value })}
                  placeholder="e.g. Type 2 Diabetes, Hypertension"
                  className="w-full h-9 px-3 rounded-md border border-slate-200 text-sm focus:ring-2 focus:ring-primary/50 outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Clinical Notes</label>
                <textarea
                  rows={3}
                  value={formData.notes || ''}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  placeholder="Initial intake notes or clinician observations..."
                  className="w-full p-3 rounded-md border border-slate-200 text-sm focus:ring-2 focus:ring-primary/50 outline-none"
                />
              </div>
            </div>
          </div>

          <div className="flex justify-end gap-3 border-t pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 rounded-md transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2 text-sm font-medium text-white bg-primary hover:bg-primary/90 rounded-md transition-colors shadow-sm disabled:opacity-50"
            >
              {loading ? 'Registering...' : 'Register Patient'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
