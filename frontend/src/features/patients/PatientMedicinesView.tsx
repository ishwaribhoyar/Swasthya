import { useState, useEffect } from 'react';
import { Pill, Clock, Calendar, CheckCircle2, AlertCircle, FileText } from 'lucide-react';


import Loader from '@/components/common/Loader';
import EmptyState from '@/components/common/EmptyState';
import { medicineApi, IMedicineSummary, IPrescription } from '@/services/api/medicine';

interface PatientMedicinesViewProps {
  patientId: string;
}

export default function PatientMedicinesView({ patientId }: PatientMedicinesViewProps) {
  const [summaries, setSummaries] = useState<IMedicineSummary[]>([]);
  const [prescriptions, setPrescriptions] = useState<IPrescription[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMedicines = async () => {
      try {
        setLoading(true);
        setError(null);
        const [sumRes, rxRes] = await Promise.all([
          medicineApi.getMedicineSummary(patientId),
          medicineApi.getPrescriptions(patientId),
        ]);
        if (sumRes.data) setSummaries(sumRes.data);
        if (rxRes.data) setPrescriptions(rxRes.data);
      } catch (err: any) {
        console.error('Failed to load medicine intelligence:', err);
        setError(err?.message || 'Failed to load medication history.');
      } finally {
        setLoading(false);
      }
    };
    fetchMedicines();
  }, [patientId]);

  if (loading) {
    return (
      <div className="py-12">
        <Loader label="Fetching patient medication history and active prescriptions..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700 flex items-center gap-2">
        <AlertCircle className="h-4 w-4 shrink-0" />
        {error}
      </div>
    );
  }

  if (summaries.length === 0 && prescriptions.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
        <EmptyState
          icon={Pill}
          title="No prescription history found"
          description="Upload a medical prescription or consultation note to automatically parse and track patient medications."
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ── Summary Stats ───────────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
            <Pill className="h-6 w-6" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Unique Medicines</p>
            <h4 className="text-2xl font-bold text-slate-900">{summaries.length}</h4>
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="p-3 bg-blue-50 text-blue-600 rounded-lg">
            <FileText className="h-6 w-6" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Prescription Events</p>
            <h4 className="text-2xl font-bold text-slate-900">{prescriptions.length}</h4>
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="p-3 bg-purple-50 text-purple-600 rounded-lg">
            <CheckCircle2 className="h-6 w-6" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Medication Status</p>
            <h4 className="text-2xl font-bold text-emerald-600">Active Regimen</h4>
          </div>
        </div>
      </div>

      {/* ── Active Medicines Summary List ──────────────────────────── */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
        <h3 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
          <Pill className="h-5 w-5 text-emerald-600" />
          Medication Regimen & Frequency
        </h3>

        <div className="divide-y divide-slate-100">
          {summaries.map((med) => (
            <div key={med.medicine_name} className="py-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-2">
                  <h4 className="text-base font-semibold text-slate-900">{med.medicine_name}</h4>
                  {med.latest_strength && (
                    <span className="px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-700">
                      {med.latest_strength}
                    </span>
                  )}
                  <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                    {med.status}
                  </span>
                </div>
                <div className="mt-1 text-xs text-slate-500 flex items-center gap-4 flex-wrap">
                  {med.latest_dose && <span>Dose: <strong>{med.latest_dose}</strong></span>}
                  {med.latest_frequency && <span>Frequency: <strong>{med.latest_frequency}</strong></span>}
                  {med.latest_route && <span>Route: <strong>{med.latest_route}</strong></span>}
                </div>
              </div>

              <div className="text-right">
                <span className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 bg-blue-50 text-blue-700 rounded-md">
                  Prescribed {med.times_prescribed} time{med.times_prescribed > 1 ? 's' : ''}
                </span>
                <p className="text-xs text-slate-400 mt-1">
                  Latest: {new Date(med.latest_prescribed_date).toLocaleDateString()}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Prescription Documents Timeline ───────────────────────── */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
        <h3 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
          <Calendar className="h-5 w-5 text-blue-600" />
          Chronological Prescription Records
        </h3>

        <div className="space-y-4">
          {prescriptions.map((rx) => (
            <div key={rx.id} className="p-4 rounded-lg border border-slate-100 bg-slate-50/50 hover:bg-slate-50 transition-colors">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-semibold text-slate-800 flex items-center gap-2">
                  <Clock className="h-4 w-4 text-slate-400" />
                  Prescription Date: {new Date(rx.prescription_date).toLocaleDateString()}
                </span>
                {rx.prescribed_by && (
                  <span className="text-xs text-slate-500">By: {rx.prescribed_by}</span>
                )}
              </div>

              <div className="space-y-2 mt-3">
                {rx.medicines.map((m) => (
                  <div key={m.id} className="bg-white p-3 rounded-md border border-slate-200 text-xs flex items-center justify-between">
                    <div>
                      <span className="font-bold text-slate-900 text-sm">{m.medicine_name}</span>
                      {m.strength && <span className="ml-2 text-slate-600 font-medium">({m.strength})</span>}
                      <p className="text-slate-500 mt-0.5">
                        {m.dose} · {m.frequency} {m.duration_days ? `for ${m.duration_days} days` : ''}
                      </p>
                    </div>
                    {m.instructions && (
                      <span className="text-slate-400 italic text-[11px] max-w-xs truncate">{m.instructions}</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
