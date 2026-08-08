import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  UserPlus,
  Search,
  Users,
  UserCheck,
  Archive,
  Calendar,
  ChevronLeft,
  ChevronRight,
  Eye,
  Edit,
  RotateCcw,
  AlertCircle,
  FolderOpen,
} from 'lucide-react';

import PageLayout from '@/components/common/PageLayout';
import EmptyState from '@/components/common/EmptyState';
import Loader from '@/components/common/Loader';
import { patientsApi } from '@/services/api/patients';
import { IPatientListItem, IPatientStatistics, IPatientCreate } from '@/types/patients';

import CreatePatientModal from './CreatePatientModal';
import EditPatientModal from './EditPatientModal';
import ArchiveConfirmModal from './ArchiveConfirmModal';
import RestoreConfirmModal from './RestoreConfirmModal';

export default function PatientsPage() {
  const navigate = useNavigate();

  // State
  const [patients, setPatients] = useState<IPatientListItem[]>([]);
  const [stats, setStats] = useState<IPatientStatistics | null>(null);
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters & Query state
  const [search, setSearch] = useState('');
  const [genderFilter, setGenderFilter] = useState('');
  const [bloodGroupFilter, setBloodGroupFilter] = useState('');
  const [sortBy, setSortBy] = useState('newest');
  const [includeArchived, setIncludeArchived] = useState(false);
  const [page, setPage] = useState(1);
  const pageSize = 15;

  // Modals state
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [editingPatient, setEditingPatient] = useState<any | null>(null);
  const [archivingPatient, setArchivingPatient] = useState<IPatientListItem | null>(null);
  const [restoringPatient, setRestoringPatient] = useState<IPatientListItem | null>(null);

  // Fetch data function
  const fetchPatients = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [listRes, statsRes] = await Promise.all([
        patientsApi.list({
          search: search || undefined,
          gender: genderFilter || undefined,
          blood_group: bloodGroupFilter || undefined,
          include_archived: includeArchived,
          sort_by: sortBy,
          page,
          page_size: pageSize,
        }),
        patientsApi.getStatistics(),
      ]);

      if (listRes.data) {
        setPatients(listRes.data.items);
        setTotalCount(listRes.data.total);
        setTotalPages(listRes.data.pages || listRes.data.totalPages || 1);
      }

      if (statsRes.data) {
        setStats(statsRes.data);
      }
    } catch (err: any) {
      console.error('Error fetching patients:', err);
      setError(err?.message || 'Failed to load patient records from server.');
    } finally {
      setLoading(false);
    }
  }, [search, genderFilter, bloodGroupFilter, includeArchived, sortBy, page]);

  useEffect(() => {
    fetchPatients();
  }, [fetchPatients]);

  // Handlers
  const handleCreatePatient = async (data: IPatientCreate) => {
    await patientsApi.create(data);
    fetchPatients();
  };

  const handleEditPatientSubmit = async (id: string, updates: any) => {
    await patientsApi.update(id, updates);
    fetchPatients();
  };

  const handleArchiveConfirm = async () => {
    if (archivingPatient) {
      await patientsApi.archive(archivingPatient.id);
      fetchPatients();
    }
  };

  const handleRestoreConfirm = async () => {
    if (restoringPatient) {
      await patientsApi.restore(restoringPatient.id);
      fetchPatients();
    }
  };

  return (
    <PageLayout
      title="Patient Records"
      description="Manage clinician patient records, search history, and clinical profiles."
      action={
        <button
          onClick={() => setIsCreateOpen(true)}
          className="flex items-center gap-2 bg-primary hover:bg-primary/90 text-white px-4 py-2 rounded-lg font-medium text-sm transition-colors shadow-sm"
        >
          <UserPlus className="h-4 w-4" />
          <span>Register New Patient</span>
        </button>
      }
    >
      <div className="space-y-6">
        {/* Statistics Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Users className="h-6 w-6" />
            </div>
            <div>
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Total Patients</p>
              <h3 className="text-2xl font-bold text-slate-900">{stats?.total_patients ?? 0}</h3>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600">
              <UserCheck className="h-6 w-6" />
            </div>
            <div>
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Active Records</p>
              <h3 className="text-2xl font-bold text-slate-900">{stats?.active_patients ?? 0}</h3>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
              <Calendar className="h-6 w-6" />
            </div>
            <div>
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">New This Month</p>
              <h3 className="text-2xl font-bold text-slate-900">{stats?.new_this_month ?? 0}</h3>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-amber-50 text-amber-600">
              <Archive className="h-6 w-6" />
            </div>
            <div>
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Archived Records</p>
              <h3 className="text-2xl font-bold text-slate-900">{stats?.archived_patients ?? 0}</h3>
            </div>
          </div>
        </div>

        {/* Filter and Control Bar */}
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm space-y-4">
          <div className="flex flex-col md:flex-row gap-4 justify-between items-stretch md:items-center">
            {/* Search */}
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
              <input
                type="text"
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(1);
                }}
                placeholder="Search by MRN, Name, Phone, Email..."
                className="w-full h-9 pl-9 pr-4 rounded-md border border-slate-200 text-sm focus:border-primary focus:ring-1 focus:ring-primary outline-none"
              />
            </div>

            {/* Filter controls */}
            <div className="flex flex-wrap items-center gap-3">
              {/* Gender */}
              <select
                value={genderFilter}
                onChange={(e) => {
                  setGenderFilter(e.target.value);
                  setPage(1);
                }}
                className="h-9 px-3 rounded-md border border-slate-200 text-xs font-medium text-slate-700 bg-white outline-none focus:ring-1 focus:ring-primary"
              >
                <option value="">All Genders</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>

              {/* Blood Group */}
              <select
                value={bloodGroupFilter}
                onChange={(e) => {
                  setBloodGroupFilter(e.target.value);
                  setPage(1);
                }}
                className="h-9 px-3 rounded-md border border-slate-200 text-xs font-medium text-slate-700 bg-white outline-none focus:ring-1 focus:ring-primary"
              >
                <option value="">All Blood Groups</option>
                <option value="A+">A+</option>
                <option value="A-">A-</option>
                <option value="B+">B+</option>
                <option value="B-">B-</option>
                <option value="AB+">AB+</option>
                <option value="AB-">AB-</option>
                <option value="O+">O+</option>
                <option value="O-">O-</option>
              </select>

              {/* Sort By */}
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="h-9 px-3 rounded-md border border-slate-200 text-xs font-medium text-slate-700 bg-white outline-none focus:ring-1 focus:ring-primary"
              >
                <option value="newest">Sort: Newest First</option>
                <option value="oldest">Sort: Oldest First</option>
                <option value="first_name">Sort: First Name</option>
                <option value="last_name">Sort: Last Name</option>
                <option value="mrn">Sort: MRN</option>
                <option value="updated_at">Sort: Recently Updated</option>
              </select>

              {/* Include Archived Toggle */}
              <label className="flex items-center gap-2 text-xs font-medium text-slate-600 cursor-pointer select-none bg-slate-50 px-3 py-2 rounded-md border border-slate-200">
                <input
                  type="checkbox"
                  checked={includeArchived}
                  onChange={(e) => {
                    setIncludeArchived(e.target.checked);
                    setPage(1);
                  }}
                  className="rounded text-primary focus:ring-primary"
                />
                <span>Include Archived</span>
              </label>
            </div>
          </div>
        </div>

        {/* Patient Table / Content Area */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden min-h-[350px]">
          {loading ? (
            <div className="py-16">
              <Loader label="Loading patient records from SQLite..." />
            </div>
          ) : error ? (
            <div className="p-8 text-center text-red-600 flex flex-col items-center gap-2">
              <AlertCircle className="h-8 w-8" />
              <p className="text-sm font-medium">{error}</p>
            </div>
          ) : patients.length === 0 ? (
            <EmptyState
              icon={FolderOpen}
              title={search ? 'No matching patients found' : 'No patients registered yet'}
              description={
                search
                  ? `No patient records match "${search}". Try adjusting your search or filters.`
                  : 'Start by registering your first patient to begin managing clinical records.'
              }
              action={
                search ? undefined : (
                  <button
                    onClick={() => setIsCreateOpen(true)}
                    className="flex items-center gap-2 bg-primary hover:bg-primary/90 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                  >
                    <UserPlus className="h-4 w-4" />
                    <span>Register First Patient</span>
                  </button>
                )
              }
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-sm">
                <thead>
                  <tr className="border-b bg-slate-50 text-slate-500 font-medium text-xs uppercase tracking-wider">
                    <th className="py-3 px-4">Patient MRN</th>
                    <th className="py-3 px-4">Full Name</th>
                    <th className="py-3 px-4">Age / Gender</th>
                    <th className="py-3 px-4">Last Visit</th>
                    <th className="py-3 px-4">Risk Status</th>
                    <th className="py-3 px-4">Blood Group</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {patients.map((patient) => (
                    <tr
                      key={patient.id}
                      className={`hover:bg-slate-50/80 transition-colors ${
                        !patient.is_active ? 'bg-slate-50/50 text-slate-400' : ''
                      }`}
                    >
                      <td className="py-3.5 px-4 font-mono font-semibold text-primary">
                        {patient.mrn}
                      </td>
                      <td className="py-3.5 px-4 font-medium text-slate-900">
                        {patient.first_name} {patient.last_name}
                      </td>
                      <td className="py-3.5 px-4 capitalize text-slate-600">
                        {patient.age} yrs • {patient.gender}
                      </td>
                      <td className="py-3.5 px-4 text-xs text-slate-500">
                        {patient.last_document_at
                          ? new Date(patient.last_document_at).toLocaleDateString(undefined, {
                              year: 'numeric',
                              month: 'short',
                              day: 'numeric',
                            })
                          : <span className="italic text-slate-400">No records yet</span>}
                      </td>
                      <td className="py-3.5 px-4">
                        {patient.risk_status === 'CRITICAL' ? (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-red-50 text-red-700 border border-red-200">
                            CRITICAL
                          </span>
                        ) : patient.risk_status === 'HIGH' ? (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-orange-50 text-orange-700 border border-orange-200">
                            HIGH
                          </span>
                        ) : patient.last_document_at ? (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                            NORMAL
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-500 border border-slate-200">
                            No Data
                          </span>
                        )}
                      </td>
                      <td className="py-3.5 px-4">
                        {patient.blood_group ? (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-red-50 text-red-700 border border-red-200">
                            {patient.blood_group}
                          </span>
                        ) : (
                          '—'
                        )}
                      </td>
                      <td className="py-3.5 px-4">
                        {patient.is_active ? (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500"></span>
                            Active
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200">
                            <span className="h-1.5 w-1.5 rounded-full bg-amber-500"></span>
                            Archived
                          </span>
                        )}
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => navigate(`/patients/${patient.id}`)}
                            title="View Patient Workspace"
                            className="p-1.5 rounded-md text-slate-500 hover:text-primary hover:bg-primary/10 transition-colors"
                          >
                            <Eye className="h-4 w-4" />
                          </button>

                          <button
                            onClick={async () => {
                              const full = await patientsApi.getById(patient.id);
                              if (full.data) setEditingPatient(full.data);
                            }}
                            title="Edit Patient"
                            className="p-1.5 rounded-md text-slate-500 hover:text-blue-600 hover:bg-blue-50 transition-colors"
                          >
                            <Edit className="h-4 w-4" />
                          </button>

                          {patient.is_active ? (
                            <button
                              onClick={() => setArchivingPatient(patient)}
                              title="Archive Patient"
                              className="p-1.5 rounded-md text-slate-500 hover:text-amber-600 hover:bg-amber-50 transition-colors"
                            >
                              <Archive className="h-4 w-4" />
                            </button>
                          ) : (
                            <button
                              onClick={() => setRestoringPatient(patient)}
                              title="Restore Patient"
                              className="p-1.5 rounded-md text-slate-500 hover:text-emerald-600 hover:bg-emerald-50 transition-colors"
                            >
                              <RotateCcw className="h-4 w-4" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination Footer */}
          {!loading && patients.length > 0 && (
            <div className="flex items-center justify-between border-t px-4 py-3 bg-slate-50">
              <div className="text-xs text-slate-500">
                Showing <strong className="text-slate-700">{patients.length}</strong> of{' '}
                <strong className="text-slate-700">{totalCount}</strong> patients
              </div>

              <div className="flex items-center gap-2">
                <button
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-md border border-slate-200 bg-white hover:bg-slate-50 text-slate-600 disabled:opacity-50"
                >
                  <ChevronLeft className="h-3.5 w-3.5" />
                  <span>Previous</span>
                </button>
                <span className="text-xs text-slate-600 font-medium px-2">
                  Page {page} of {totalPages}
                </span>
                <button
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => p + 1)}
                  className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-md border border-slate-200 bg-white hover:bg-slate-50 text-slate-600 disabled:opacity-50"
                >
                  <span>Next</span>
                  <ChevronRight className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Modals */}
      <CreatePatientModal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onSubmit={handleCreatePatient}
      />

      <EditPatientModal
        patient={editingPatient}
        isOpen={!!editingPatient}
        onClose={() => setEditingPatient(null)}
        onSubmit={handleEditPatientSubmit}
      />

      <ArchiveConfirmModal
        isOpen={!!archivingPatient}
        patientName={archivingPatient ? `${archivingPatient.first_name} ${archivingPatient.last_name}` : ''}
        mrn={archivingPatient?.mrn || ''}
        onClose={() => setArchivingPatient(null)}
        onConfirm={handleArchiveConfirm}
      />

      <RestoreConfirmModal
        isOpen={!!restoringPatient}
        patientName={restoringPatient ? `${restoringPatient.first_name} ${restoringPatient.last_name}` : ''}
        mrn={restoringPatient?.mrn || ''}
        onClose={() => setRestoringPatient(null)}
        onConfirm={handleRestoreConfirm}
      />
    </PageLayout>
  );
}
