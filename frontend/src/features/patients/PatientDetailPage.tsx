import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  FileText,
  Edit,
  Archive,
  RotateCcw,
  ArrowLeft,
  ShieldAlert,
  AlertTriangle,
  FileSearch,
  Bot,
  Search,
  Eye,
  Activity,

  Trash2,
  CheckCircle2,
  AlertCircle,
  Stethoscope,

} from 'lucide-react';

import PageLayout from '@/components/common/PageLayout';
import Loader from '@/components/common/Loader';
import EmptyState from '@/components/common/EmptyState';
import { patientsApi } from '@/services/api/patients';
import { ingestionApi } from '@/services/api/ingestion';
import { clinicalApi } from '@/services/api/clinical';
import { IPatient } from '@/types/patients';
import { IDocumentListItem, IBatchUploadSummary } from '@/types/ingestion';
import { IClinicalOverview } from '@/types/clinical';

import EditPatientModal from './EditPatientModal';
import ArchiveConfirmModal from './ArchiveConfirmModal';
import RestoreConfirmModal from './RestoreConfirmModal';

import DocumentUploadDropzone from '@/features/ingestion/DocumentUploadDropzone';
import BatchUploadSummaryBanner from '@/features/ingestion/BatchUploadSummaryBanner';
import PipelineTimelineModal from '@/features/ingestion/PipelineTimelineModal';
import DocumentViewerModal from '@/features/ingestion/DocumentViewerModal';

import OrganScoreCard from '@/features/clinical/OrganScoreCard';
import ClinicalAlertsPanel from '@/features/clinical/ClinicalAlertsPanel';
import PatientTimelineView from '@/features/timeline/PatientTimelineView';
import PatientAnalyticsView from '@/features/analytics/PatientAnalyticsView';


export default function PatientDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [patient, setPatient] = useState<IPatient | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [activeTab, setActiveTab] = useState<'overview' | 'records' | 'timeline' | 'analytics' | 'copilot' | 'settings'>('overview');

  // Documents State
  const [documents, setDocuments] = useState<IDocumentListItem[]>([]);
  const [docsLoading, setDocsLoading] = useState(false);
  const [docSearch, setDocSearch] = useState('');
  const [docCategory, setDocCategory] = useState('');
  const [docStatus, setDocStatus] = useState('');
  const [docSort, setDocSort] = useState('newest');
  const [batchSummary, setBatchSummary] = useState<IBatchUploadSummary | null>(null);

  // Clinical Intelligence State
  const [clinicalOverview, setClinicalOverview] = useState<IClinicalOverview | null>(null);
  const [clinicalLoading, setClinicalLoading] = useState(false);

  // Modals state
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isArchiveOpen, setIsArchiveOpen] = useState(false);
  const [isRestoreOpen, setIsRestoreOpen] = useState(false);
  const [viewingDocId, setViewingDocId] = useState<string | null>(null);
  const [timelineDoc, setTimelineDoc] = useState<{ id: string; name: string } | null>(null);

  const fetchPatient = async () => {
    if (!id) return;
    try {
      setLoading(true);
      setError(null);
      const res = await patientsApi.getById(id);
      if (res.data) setPatient(res.data);
    } catch (err: any) {
      console.error('Error fetching patient details:', err);
      setError(err?.message || 'Failed to load patient record.');
    } finally {
      setLoading(false);
    }
  };

  const fetchDocuments = useCallback(async () => {
    if (!id) return;
    try {
      setDocsLoading(true);
      const res = await ingestionApi.listDocuments(id, {
        search: docSearch || undefined,
        category: docCategory || undefined,
        status: docStatus || undefined,
        sort_by: docSort,
      });
      if (res.data) setDocuments(res.data);
    } catch (err) {
      console.error('Failed to load documents:', err);
    } finally {
      setDocsLoading(false);
    }
  }, [id, docSearch, docCategory, docStatus, docSort]);

  const fetchClinicalOverview = useCallback(async () => {
    if (!id) return;
    try {
      setClinicalLoading(true);
      const res = await clinicalApi.getOverview(id);
      if (res.data) setClinicalOverview(res.data);
    } catch (err) {
      console.error('Failed to load clinical overview:', err);
    } finally {
      setClinicalLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchPatient();
  }, [id]);

  useEffect(() => {
    if (activeTab === 'records' && id) {
      fetchDocuments();
    } else if (activeTab === 'analytics' && id) {
      fetchClinicalOverview();
    }
  }, [activeTab, id, fetchDocuments, fetchClinicalOverview]);

  const handleEditSubmit = async (patientId: string, updates: any) => {
    await patientsApi.update(patientId, updates);
    fetchPatient();
  };

  const handleArchiveConfirm = async () => {
    if (patient) {
      await patientsApi.archive(patient.id);
      fetchPatient();
    }
  };

  const handleRestoreConfirm = async () => {
    if (patient) {
      await patientsApi.restore(patient.id);
      fetchPatient();
    }
  };

  const handleBatchUpload = async (files: File[]) => {
    if (!id) return;
    setDocsLoading(true);
    try {
      const res = await ingestionApi.uploadBatch(id, files);
      if (res.data) {
        setBatchSummary(res.data);
        fetchDocuments();
        // Trigger Clinical Engine Analysis
        await clinicalApi.analyze(id);
        fetchClinicalOverview();
      }
    } finally {
      setDocsLoading(false);
    }
  };

  const handleDeleteDoc = async (docId: string) => {
    if (confirm('Delete this document?')) {
      await ingestionApi.deleteDocument(docId);
      fetchDocuments();
      if (id) {
        await clinicalApi.analyze(id);
        fetchClinicalOverview();
      }
    }
  };

  const handleAcknowledgeAlert = async (alertId: string) => {
    if (!id) return;
    await clinicalApi.acknowledgeAlert(alertId);
    fetchClinicalOverview();
  };

  if (loading) {
    return (
      <PageLayout title="Patient Record" description="Loading patient workspace...">
        <div className="py-20">
          <Loader label="Fetching patient demographics and clinical history..." />
        </div>
      </PageLayout>
    );
  }

  if (error || !patient) {
    return (
      <PageLayout title="Patient Not Found" description="The requested patient record could not be loaded.">
        <div className="bg-white rounded-xl border border-slate-200 p-8 text-center space-y-4">
          <AlertTriangle className="h-12 w-12 text-amber-500 mx-auto" />
          <h3 className="text-lg font-semibold text-slate-900">{error || 'Patient Record Not Found'}</h3>
          <p className="text-sm text-slate-500 max-w-md mx-auto">
            The patient record may have been moved or you do not have permission to view it.
          </p>
          <button
            onClick={() => navigate('/patients')}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-primary rounded-lg hover:bg-primary/90 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>Return to Patients List</span>
          </button>
        </div>
      </PageLayout>
    );
  }

  const registeredMonth = new Date(patient.created_at).toLocaleDateString(undefined, {
    month: 'short',
    year: 'numeric',
  });

  return (
    <PageLayout
      title={`${patient.first_name} ${patient.last_name}`}
      description={`${patient.mrn} • ${patient.age} Years • ${patient.gender}`}
      action={
        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate('/patients')}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-600 bg-white border border-slate-200 hover:bg-slate-50 rounded-lg transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>Back</span>
          </button>

          <button
            onClick={() => setIsEditOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-200 hover:bg-slate-50 rounded-lg transition-colors"
          >
            <Edit className="h-4 w-4 text-blue-600" />
            <span>Edit Profile</span>
          </button>

          {patient.is_active ? (
            <button
              onClick={() => setIsArchiveOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-amber-700 bg-amber-50 border border-amber-200 hover:bg-amber-100 rounded-lg transition-colors"
            >
              <Archive className="h-4 w-4" />
              <span>Archive</span>
            </button>
          ) : (
            <button
              onClick={() => setIsRestoreOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-emerald-700 bg-emerald-50 border border-emerald-200 hover:bg-emerald-100 rounded-lg transition-colors"
            >
              <RotateCcw className="h-4 w-4" />
              <span>Restore Patient</span>
            </button>
          )}
        </div>
      }
    >
      <div className="space-y-6">
        {/* Top Identity Header Card */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10 text-primary font-bold text-xl">
              {patient.first_name[0]}{patient.last_name[0]}
            </div>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold text-slate-900">
                  {patient.first_name} {patient.last_name}
                </h1>
                <span className="px-2.5 py-0.5 rounded text-xs font-mono font-bold bg-primary/10 text-primary border border-primary/20">
                  {patient.mrn}
                </span>
                {!patient.is_active && (
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-50 text-amber-800 border border-amber-200">
                    Archived Record
                  </span>
                )}
              </div>

              <p className="text-sm font-medium text-slate-600 mt-1 capitalize">
                {patient.age} Years • {patient.gender}
                {patient.blood_group ? ` • Blood Group ${patient.blood_group}` : ''}
                {` • Registered ${registeredMonth}`}
              </p>
            </div>
          </div>

          <div className="flex flex-wrap gap-4 text-xs text-slate-600 bg-slate-50 p-3 rounded-lg border border-slate-200">
            <div>
              <span className="text-slate-400 block font-medium uppercase text-[10px]">Phone</span>
              <span className="font-semibold text-slate-800">{patient.phone || '—'}</span>
            </div>
            <div className="border-l border-slate-200 pl-4">
              <span className="text-slate-400 block font-medium uppercase text-[10px]">Email</span>
              <span className="font-semibold text-slate-800">{patient.email || '—'}</span>
            </div>
            <div className="border-l border-slate-200 pl-4">
              <span className="text-slate-400 block font-medium uppercase text-[10px]">Emergency Contact</span>
              <span className="font-semibold text-slate-800">
                {patient.emergency_contact_name
                  ? `${patient.emergency_contact_name} (${patient.emergency_contact_phone || 'No Phone'})`
                  : '—'}
              </span>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="border-b border-slate-200">
          <nav className="flex space-x-6 overflow-x-auto">
            <button
              onClick={() => setActiveTab('overview')}
              className={`py-3 px-1 border-b-2 font-medium text-sm transition-colors whitespace-nowrap ${
                activeTab === 'overview'
                  ? 'border-primary text-primary font-semibold'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              Overview
            </button>

            <button
              onClick={() => setActiveTab('records')}
              className={`py-3 px-1 border-b-2 font-medium text-sm transition-colors whitespace-nowrap flex items-center gap-2 ${
                activeTab === 'records'
                  ? 'border-primary text-primary font-semibold'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              <span>Medical Records</span>
              <span className="px-2 py-0.5 text-[10px] font-semibold bg-emerald-100 text-emerald-800 rounded-full border border-emerald-300">
                Active Phase 3
              </span>
            </button>

            <button
              onClick={() => setActiveTab('analytics')}
              className={`py-3 px-1 border-b-2 font-medium text-sm transition-colors whitespace-nowrap flex items-center gap-2 ${
                activeTab === 'analytics'
                  ? 'border-primary text-primary font-semibold'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              <span>Clinical Analytics</span>
              <span className="px-2 py-0.5 text-[10px] font-semibold bg-emerald-100 text-emerald-800 rounded-full border border-emerald-300">
                Active Phase 4
              </span>
            </button>

            <button
              onClick={() => setActiveTab('timeline')}
              className={`py-3 px-1 border-b-2 font-medium text-sm transition-colors whitespace-nowrap flex items-center gap-2 ${
                activeTab === 'timeline'
                  ? 'border-primary text-primary font-semibold'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              <span>Clinical Timeline</span>
              <span className="px-2 py-0.5 text-[10px] font-semibold bg-slate-100 text-slate-500 rounded-full border border-slate-200">
                Available Phase 6
              </span>
            </button>

            <button
              onClick={() => setActiveTab('copilot')}
              className={`py-3 px-1 border-b-2 font-medium text-sm transition-colors whitespace-nowrap flex items-center gap-2 ${
                activeTab === 'copilot'
                  ? 'border-primary text-primary font-semibold'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              <span>AI Copilot</span>
              <span className="px-2 py-0.5 text-[10px] font-semibold bg-slate-100 text-slate-500 rounded-full border border-slate-200">
                Available Phase 7
              </span>
            </button>

            <button
              onClick={() => setActiveTab('settings')}
              className={`py-3 px-1 border-b-2 font-medium text-sm transition-colors whitespace-nowrap ${
                activeTab === 'settings'
                  ? 'border-primary text-primary font-semibold'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              Record Settings
            </button>
          </nav>
        </div>

        {/* Tab Content Areas */}
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4">
                <h3 className="text-base font-semibold text-slate-900 flex items-center gap-2">
                  <ShieldAlert className="h-5 w-5 text-red-500" />
                  <span>Allergies & Medical Alerts</span>
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 rounded-lg bg-red-50/50 border border-red-100">
                    <span className="text-xs font-semibold text-red-700 uppercase tracking-wider block mb-1">
                      Known Allergies
                    </span>
                    <p className="text-sm font-medium text-slate-800">
                      {patient.allergies || 'No known allergies reported.'}
                    </p>
                  </div>

                  <div className="p-4 rounded-lg bg-amber-50/50 border border-amber-100">
                    <span className="text-xs font-semibold text-amber-700 uppercase tracking-wider block mb-1">
                      Chronic Conditions
                    </span>
                    <p className="text-sm font-medium text-slate-800">
                      {patient.chronic_conditions || 'No chronic medical conditions recorded.'}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-3">
                <h3 className="text-base font-semibold text-slate-900 flex items-center gap-2">
                  <FileText className="h-5 w-5 text-primary" />
                  <span>Clinician Notes & Observations</span>
                </h3>
                <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 text-sm text-slate-700 leading-relaxed min-h-[100px]">
                  {patient.notes || 'No clinical notes added yet for this patient.'}
                </div>
              </div>
            </div>

            <div className="space-y-6">
              <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4">
                <h3 className="text-base font-semibold text-slate-900">Demographics & Address</h3>
                <div className="space-y-3 text-sm">
                  <div>
                    <span className="text-xs text-slate-400 block font-medium">Home Address</span>
                    <span className="text-slate-800 font-medium">{patient.address || 'No address registered.'}</span>
                  </div>
                  <div className="border-t pt-3">
                    <span className="text-xs text-slate-400 block font-medium">Registration Date</span>
                    <span className="text-slate-800 font-medium">
                      {new Date(patient.created_at).toLocaleDateString(undefined, {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                      })}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Phase 3 Workspace: Medical Records */}
        {activeTab === 'records' && (
          <div className="space-y-6">
            <DocumentUploadDropzone onUpload={handleBatchUpload} loading={docsLoading} />
            <BatchUploadSummaryBanner summary={batchSummary} onClose={() => setBatchSummary(null)} />

            <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex flex-col md:flex-row gap-4 justify-between items-stretch md:items-center">
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <input
                  type="text"
                  value={docSearch}
                  onChange={(e) => setDocSearch(e.target.value)}
                  placeholder="Search uploaded documents by name or extracted content..."
                  className="w-full h-9 pl-9 pr-4 rounded-md border border-slate-200 text-sm focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                />
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <select
                  value={docCategory}
                  onChange={(e) => setDocCategory(e.target.value)}
                  className="h-9 px-3 rounded-md border border-slate-200 text-xs font-medium text-slate-700 bg-white outline-none focus:ring-1 focus:ring-primary"
                >
                  <option value="">All Categories</option>
                  <option value="lab">Lab Reports</option>
                  <option value="prescription">Prescriptions</option>
                  <option value="vitals">Vitals Sheets</option>
                  <option value="summary">Discharge Summaries</option>
                  <option value="note">Clinical Notes</option>
                </select>

                <select
                  value={docStatus}
                  onChange={(e) => setDocStatus(e.target.value)}
                  className="h-9 px-3 rounded-md border border-slate-200 text-xs font-medium text-slate-700 bg-white outline-none focus:ring-1 focus:ring-primary"
                >
                  <option value="">All Statuses</option>
                  <option value="completed">Completed</option>
                  <option value="duplicate">Duplicate</option>
                  <option value="failed">Failed</option>
                </select>

                <select
                  value={docSort}
                  onChange={(e) => setDocSort(e.target.value)}
                  className="h-9 px-3 rounded-md border border-slate-200 text-xs font-medium text-slate-700 bg-white outline-none focus:ring-1 focus:ring-primary"
                >
                  <option value="newest">Sort: Newest First</option>
                  <option value="oldest">Sort: Oldest First</option>
                  <option value="filename">Sort: Filename</option>
                  <option value="processing_time">Sort: Processing Time</option>
                </select>
              </div>
            </div>

            <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden min-h-[300px]">
              {docsLoading ? (
                <div className="py-12">
                  <Loader label="Processing document intelligence pipeline..." />
                </div>
              ) : documents.length === 0 ? (
                <EmptyState
                  icon={FileSearch}
                  title="No Medical Documents Ingested"
                  description="Drag & drop up to 10 medical files above (Lab reports, Prescriptions, PDFs, Images) to run automatic ingestion and OCR."
                />
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse text-sm">
                    <thead>
                      <tr className="border-b bg-slate-50 text-slate-500 font-medium text-xs uppercase tracking-wider">
                        <th className="py-3 px-4">Filename</th>
                        <th className="py-3 px-4">Category</th>
                        <th className="py-3 px-4">Engine Source</th>
                        <th className="py-3 px-4">Confidence</th>
                        <th className="py-3 px-4">Duration</th>
                        <th className="py-3 px-4">Status</th>
                        <th className="py-3 px-4 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {documents.map((doc) => (
                        <tr key={doc.id} className="hover:bg-slate-50/80 transition-colors">
                          <td className="py-3.5 px-4 font-medium text-slate-900 flex items-center gap-2">
                            <FileText className="h-4 w-4 text-primary shrink-0" />
                            <span className="truncate max-w-xs">{doc.original_filename}</span>
                          </td>

                          <td className="py-3.5 px-4 uppercase font-semibold text-xs text-slate-600">
                            <span className="px-2 py-0.5 rounded bg-slate-100 border border-slate-200">
                              {doc.doc_category}
                            </span>
                          </td>

                          <td className="py-3.5 px-4 font-mono text-xs text-slate-600">
                            {doc.parse_source || 'pymupdf_fallback'}
                          </td>

                          <td className="py-3.5 px-4">
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                              {(doc.confidence_score * 100).toFixed(1)}%
                            </span>
                          </td>

                          <td className="py-3.5 px-4 text-xs font-mono text-slate-500">
                            {doc.processing_time_ms}ms
                          </td>

                          <td className="py-3.5 px-4">
                            {doc.status === 'completed' && (
                              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                                <CheckCircle2 className="h-3 w-3" /> Completed
                              </span>
                            )}
                            {doc.status === 'duplicate' && (
                              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200">
                                <AlertTriangle className="h-3 w-3" /> Duplicate
                              </span>
                            )}
                            {doc.status === 'failed' && (
                              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-50 text-red-700 border border-red-200">
                                <AlertCircle className="h-3 w-3" /> Failed
                              </span>
                            )}
                          </td>

                          <td className="py-3.5 px-4 text-right">
                            <div className="flex items-center justify-end gap-2">
                              <button
                                onClick={() => setViewingDocId(doc.id)}
                                title="View Extracted Text & Layout"
                                className="p-1.5 rounded-md text-slate-500 hover:text-primary hover:bg-primary/10 transition-colors"
                              >
                                <Eye className="h-4 w-4" />
                              </button>
                              <button
                                onClick={() => setTimelineDoc({ id: doc.id, name: doc.original_filename })}
                                title="View Pipeline Execution Timeline"
                                className="p-1.5 rounded-md text-slate-500 hover:text-blue-600 hover:bg-blue-50 transition-colors"
                              >
                                <Activity className="h-4 w-4" />
                              </button>
                              {doc.status === 'failed' && (
                                <button
                                  onClick={async () => {
                                    try {
                                      await ingestionApi.retryDocument(doc.id);
                                      fetchDocuments();
                                    } catch (e) {
                                      console.error('Retry failed:', e);
                                    }
                                  }}
                                  title="Retry Processing"
                                  className="p-1.5 rounded-md text-slate-500 hover:text-emerald-600 hover:bg-emerald-50 transition-colors"
                                >
                                  <RotateCcw className="h-4 w-4" />
                                </button>
                              )}
                              <button
                                onClick={() => handleDeleteDoc(doc.id)}
                                title="Delete Document"
                                className="p-1.5 rounded-md text-slate-500 hover:text-red-600 hover:bg-red-50 transition-colors"
                              >
                                <Trash2 className="h-4 w-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Phase 4 Active Workspace: Clinical Analytics */}
        {activeTab === 'analytics' && (
          <div className="space-y-6">
            {clinicalLoading ? (
              <div className="py-12">
                <Loader label="Evaluating 8-organ system health scores and severity alerts..." />
              </div>
            ) : (
              <>
                {clinicalOverview && clinicalOverview.alerts.length > 0 && (
                  <ClinicalAlertsPanel alerts={clinicalOverview.alerts} onAcknowledge={handleAcknowledgeAlert} />
                )}

                {clinicalOverview && clinicalOverview.organ_scores.length > 0 && (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <h3 className="text-base font-semibold text-slate-900 flex items-center gap-2">
                        <Stethoscope className="h-5 w-5 text-primary" />
                        <span>8-Organ System Health Scoring Grid</span>
                      </h3>
                      <button
                        onClick={() => id && clinicalApi.analyze(id).then(fetchClinicalOverview)}
                        className="text-xs text-primary font-medium hover:underline flex items-center gap-1"
                      >
                        <span>Re-analyze Patient</span>
                      </button>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                      {clinicalOverview.organ_scores.map((score) => (
                        <OrganScoreCard key={score.id} score={score} />
                      ))}
                    </div>
                  </div>
                )}

                {/* Longitudinal Parameter Trend Curves & Analytics */}
                <div className="pt-2">
                  <PatientAnalyticsView patientId={patient.id} />
                </div>
              </>
            )}
          </div>
        )}



        {/* Phase 4 Active Workspace: Clinical Event Timeline */}
        {activeTab === 'timeline' && (
          <PatientTimelineView patientId={patient.id} />
        )}


        {activeTab === 'copilot' && (
          <div className="bg-white rounded-xl border border-slate-200 p-8 text-center">
            <EmptyState
              icon={Bot}
              title="AI Clinical Copilot Initializing"
              description="AI-driven diagnostic assistance and record synthesis will be active for this patient in Phase 7."
            />
          </div>
        )}

        {activeTab === 'settings' && (
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm max-w-xl space-y-4">
            <h3 className="text-base font-semibold text-slate-900">Record Management Options</h3>
            <div className="border-t pt-4 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-medium text-slate-800">Archive Patient Record</h4>
                  <p className="text-xs text-slate-500">Hide patient from active lists without deleting clinical history.</p>
                </div>
                {patient.is_active ? (
                  <button
                    onClick={() => setIsArchiveOpen(true)}
                    className="px-3 py-1.5 text-xs font-medium text-amber-700 bg-amber-50 border border-amber-200 rounded-md hover:bg-amber-100"
                  >
                    Archive
                  </button>
                ) : (
                  <button
                    onClick={() => setIsRestoreOpen(true)}
                    className="px-3 py-1.5 text-xs font-medium text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-md hover:bg-emerald-100"
                  >
                    Restore
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Modals */}
      <EditPatientModal
        patient={patient}
        isOpen={isEditOpen}
        onClose={() => setIsEditOpen(false)}
        onSubmit={handleEditSubmit}
      />

      <ArchiveConfirmModal
        isOpen={isArchiveOpen}
        patientName={`${patient.first_name} ${patient.last_name}`}
        mrn={patient.mrn}
        onClose={() => setIsArchiveOpen(false)}
        onConfirm={handleArchiveConfirm}
      />

      <RestoreConfirmModal
        isOpen={isRestoreOpen}
        patientName={`${patient.first_name} ${patient.last_name}`}
        mrn={patient.mrn}
        onClose={() => setIsRestoreOpen(false)}
        onConfirm={handleRestoreConfirm}
      />

      <DocumentViewerModal
        documentId={viewingDocId}
        isOpen={!!viewingDocId}
        onClose={() => setViewingDocId(null)}
      />

      <PipelineTimelineModal
        documentId={timelineDoc?.id || null}
        filename={timelineDoc?.name || ''}
        isOpen={!!timelineDoc}
        onClose={() => setTimelineDoc(null)}
      />
    </PageLayout>
  );
}
