import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Activity, User, ArrowRight } from 'lucide-react';
import PageLayout from '@/components/common/PageLayout';
import EmptyState from '@/components/common/EmptyState';
import Loader from '@/components/common/Loader';
import PatientAnalyticsView from '@/features/analytics/PatientAnalyticsView';
import { patientsApi } from '@/services/api/patients';
import { IPatientListItem } from '@/types/patients';

export default function AnalyticsPage() {
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
      title="Longitudinal Trend & Anomaly Analytics"
      description="Time-series parameter trend curves, deterministic rate of change metrics, and clinical anomaly intelligence."
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
                <span>View Patient Workspace</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
        ) : null
      }
    >
      {loading ? (
        <div className="py-16">
          <Loader label="Loading patient directory for longitudinal trend analysis..." />
        </div>
      ) : patients.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center shadow-sm">
          <EmptyState
            icon={Activity}
            title="No Patient Records Available"
            description="Register a patient and upload medical records to generate time-series trend curves."
          />
        </div>
      ) : selectedPatientId ? (
        <PatientAnalyticsView patientId={selectedPatientId} />
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center shadow-sm">
          <EmptyState
            icon={User}
            title="Select a Patient"
            description="Choose a patient from the selector above to analyze their longitudinal parameter trends."
          />
        </div>
      )}
    </PageLayout>
  );
}
