import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { CalendarClock, User, ArrowRight } from 'lucide-react';
import PageLayout from '@/components/common/PageLayout';
import EmptyState from '@/components/common/EmptyState';
import Loader from '@/components/common/Loader';
import PatientTimelineView from '@/features/timeline/PatientTimelineView';
import { patientsApi } from '@/services/api/patients';
import { IPatientListItem } from '@/types/patients';

export default function TimelinePage() {
  const navigate = useNavigate();
  const [patients, setPatients] = useState<IPatientListItem[]>([]);
  const [selectedPatientId, setSelectedPatientId] = useState<string>('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    patientsApi
      .list({ page_size: 100 })
      .then((res) => {
        if (res.data?.items && res.data.items.length > 0) {
          setPatients(res.data.items);
          setSelectedPatientId(res.data.items[0].id);
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const selectedPatient = patients.find((p) => p.id === selectedPatientId);

  return (
    <PageLayout
      title="Clinical Timeline Intelligence"
      description="Longitudinal clinical event reconstruction sorted by clinical event dates across patient history."
      action={
        patients.length > 0 ? (
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Select Patient:</span>
            <select
              value={selectedPatientId}
              onChange={(e) => setSelectedPatientId(e.target.value)}
              className="h-9 px-3 rounded-lg border border-slate-200 text-xs font-semibold text-slate-800 bg-white outline-none focus:ring-1 focus:ring-primary shadow-xs"
            >
              {patients.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.first_name} {p.last_name} ({p.mrn})
                </option>
              ))}
            </select>

            {selectedPatient && (
              <button
                onClick={() => navigate(`/patients/${selectedPatient.id}`)}
                className="flex items-center gap-1 px-3 py-2 text-xs font-medium text-primary bg-primary/10 hover:bg-primary/20 rounded-lg transition-colors border border-primary/20"
              >
                <span>View Full Record</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
        ) : null
      }
    >
      {loading ? (
        <div className="py-16">
          <Loader label="Fetching clinician's patient directory..." />
        </div>
      ) : patients.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center shadow-sm">
          <EmptyState
            icon={CalendarClock}
            title="No Patients Available"
            description="Create a patient record in the Patients workspace and upload medical documents to populate clinical timelines."
          />
        </div>
      ) : selectedPatientId ? (
        <PatientTimelineView patientId={selectedPatientId} />
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center shadow-sm">
          <EmptyState
            icon={User}
            title="Select a Patient"
            description="Choose a patient from the dropdown above to view their longitudinal event timeline."
          />
        </div>
      )}
    </PageLayout>
  );
}
