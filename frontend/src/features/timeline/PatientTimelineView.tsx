import { useState, useEffect, useCallback } from 'react';
import {
  Calendar,
  Search,
  FlaskConical,
  Pill,
  HeartPulse,
  Stethoscope,
  AlertTriangle,
  RefreshCw,
  Eye,
  TrendingUp,
  TrendingDown,
  Minus,
  FileX,
  Activity,
  BarChart3,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import Loader from '@/components/common/Loader';
import EmptyState from '@/components/common/EmptyState';
import SourceEvidenceDrawer from '@/features/ingestion/SourceEvidenceDrawer';
import {
  timelineApi,
  IVisitGroup,
  IClinicalEncounter,
  IClinicalObservation,
  ITimelineStats,
} from '@/services/api/timeline';

interface PatientTimelineViewProps {
  patientId: string;
}

// ─── Status badge helpers ────────────────────────────────────────────────────

function getStatusColor(status: string) {
  switch (status?.toUpperCase()) {
    case 'CRITICAL_HIGH':
    case 'CRITICAL_LOW':
      return { bg: 'bg-red-100', text: 'text-red-700', border: 'border-red-300', label: 'Critical' };
    case 'HIGH':
      return { bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-300', label: 'High' };
    case 'LOW':
      return { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-300', label: 'Low' };
    case 'NORMAL':
      return { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200', label: 'Normal' };
    default:
      return { bg: 'bg-slate-50', text: 'text-slate-500', border: 'border-slate-200', label: status || '—' };
  }
}

function StatusArrow({ status }: { status: string }) {
  switch (status?.toUpperCase()) {
    case 'HIGH':
    case 'CRITICAL_HIGH':
      return <TrendingUp className="h-3.5 w-3.5 text-amber-600 shrink-0" />;
    case 'LOW':
    case 'CRITICAL_LOW':
      return <TrendingDown className="h-3.5 w-3.5 text-blue-600 shrink-0" />;
    case 'NORMAL':
      return <Minus className="h-3.5 w-3.5 text-emerald-600 shrink-0" />;
    default:
      return null;
  }
}

function getCategoryBadge(type: string) {
  switch (type?.toUpperCase()) {
    case 'LAB_REPORT':
    case 'LAB':
      return { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200', icon: FlaskConical };
    case 'PRESCRIPTION':
      return { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200', icon: Pill };
    case 'VITALS':
      return { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200', icon: HeartPulse };
    default:
      return { bg: 'bg-purple-50', text: 'text-purple-700', border: 'border-purple-200', icon: Stethoscope };
  }
}

// ─── Observation table ────────────────────────────────────────────────────────

function ObservationTable({ observations }: { observations: IClinicalObservation[] }) {
  if (!observations.length) return null;

  return (
    <div className="space-y-3">
      {/* Summary chips for quick scan */}
      <div className="flex flex-wrap gap-1.5">
        {observations.map((obs, i) => {
          const sc = getStatusColor(obs.status);
          return (
            <div
              key={i}
              className={`inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium border ${sc.bg} ${sc.text} ${sc.border}`}
            >
              <StatusArrow status={obs.status} />
              <span className="font-semibold">{obs.name}:</span>
              <span className="font-bold font-mono">{obs.value_str}</span>
              {(obs.status === 'HIGH' || obs.status === 'CRITICAL_HIGH' || obs.status === 'LOW' || obs.status === 'CRITICAL_LOW') && (
                <span className={`text-[9px] font-bold uppercase tracking-wide px-1 py-0.5 rounded ${sc.bg} ${sc.text}`}>
                  {sc.label}
                </span>
              )}
            </div>
          );
        })}
      </div>

      {/* Detailed table if >= 4 observations */}
      {observations.length >= 4 && (
        <div className="overflow-x-auto rounded-lg border border-slate-200">
          <table className="w-full text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200">
                <th className="text-left px-3 py-2 font-semibold text-slate-600 uppercase tracking-wider">Parameter</th>
                <th className="text-right px-3 py-2 font-semibold text-slate-600 uppercase tracking-wider">Result</th>
                <th className="text-center px-3 py-2 font-semibold text-slate-600 uppercase tracking-wider">Status</th>
                <th className="text-right px-3 py-2 font-semibold text-slate-600 uppercase tracking-wider hidden sm:table-cell">Reference</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {observations.map((obs, i) => {
                const sc = getStatusColor(obs.status);
                return (
                  <tr key={i} className={`${sc.bg} bg-opacity-30 hover:bg-opacity-50 transition-colors`}>
                    <td className="px-3 py-2 font-medium text-slate-800">{obs.name}</td>
                    <td className="px-3 py-2 text-right font-bold font-mono text-slate-900">{obs.value_str}</td>
                    <td className="px-3 py-2 text-center">
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold border ${sc.bg} ${sc.text} ${sc.border}`}>
                        <StatusArrow status={obs.status} />
                        {sc.label}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-right text-slate-400 hidden sm:table-cell">
                      {obs.reference_range || '—'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ─── Single encounter card ────────────────────────────────────────────────────

function EncounterCard({
  encounter,
  onViewSource,
}: {
  encounter: IClinicalEncounter;
  onViewSource: (docId: string) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const badge = getCategoryBadge(encounter.event_type);
  const BadgeIcon = badge.icon;
  const confPercent = Math.round((encounter.confidence <= 1 ? encounter.confidence * 100 : encounter.confidence));
  const hasObs = encounter.observations.length > 0;

  if (encounter.processing_incomplete) {
    return (
      <div className="rounded-xl border border-amber-200 bg-amber-50/60 p-4 space-y-2">
        <div className="flex items-start gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-100 border border-amber-200 shrink-0 mt-0.5">
            <FileX className="h-4 w-4 text-amber-600" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h4 className="text-sm font-semibold text-amber-900">{encounter.title}</h4>
              <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded border bg-amber-100 text-amber-700 border-amber-300">
                Processing Incomplete
              </span>
            </div>
            <p className="text-xs text-amber-700 mt-1">
              {encounter.processing_reason || 'This document could not be reliably converted into clinical observations.'}
            </p>
          </div>
          {encounter.record_id && (
            <button
              onClick={() => onViewSource(encounter.record_id!)}
              className="flex items-center gap-1 text-xs font-medium text-amber-700 hover:text-amber-900 bg-amber-100 hover:bg-amber-200 px-2.5 py-1.5 rounded-md border border-amber-300 transition-colors shrink-0"
            >
              <Eye className="h-3.5 w-3.5" />
              <span>View Original</span>
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm hover:shadow-md transition-shadow overflow-hidden">
      {/* Card Header */}
      <div className="flex items-start justify-between gap-4 p-4 border-b border-slate-100">
        <div className="flex items-start gap-3 flex-1 min-w-0">
          <div className={`flex h-9 w-9 items-center justify-center rounded-lg border shrink-0 ${badge.bg} ${badge.border}`}>
            <BadgeIcon className={`h-4 w-4 ${badge.text}`} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h4 className="text-sm font-bold text-slate-900 truncate max-w-xs">{encounter.title}</h4>
              <span className={`px-2 py-0.5 text-[10px] uppercase font-bold rounded border shrink-0 ${badge.bg} ${badge.text} ${badge.border}`}>
                {encounter.event_type.replace('_', ' ')}
              </span>
              {hasObs && (
                <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-slate-100 text-slate-600 border border-slate-200 shrink-0">
                  {encounter.observations.length} observation{encounter.observations.length !== 1 ? 's' : ''}
                </span>
              )}
            </div>
            {/* Date provenance — collapsed by default */}
            <div className="flex items-center gap-1.5 mt-1 text-[11px] text-slate-400">
              <span className="font-mono uppercase tracking-wide">{encounter.date_priority_source}</span>
              <span>·</span>
              <span>{confPercent}% confidence</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {encounter.record_id && (
            <button
              onClick={() => onViewSource(encounter.record_id!)}
              className="flex items-center gap-1 text-xs font-medium text-primary hover:text-primary/80 bg-primary/5 hover:bg-primary/10 px-2.5 py-1.5 rounded-md border border-primary/20 transition-colors"
            >
              <Eye className="h-3.5 w-3.5" />
              <span>View Source</span>
            </button>
          )}
          {(hasObs || encounter.summary) && (
            <button
              onClick={() => setExpanded((e) => !e)}
              className="flex items-center gap-1 text-xs font-medium text-slate-500 hover:text-slate-700 bg-slate-50 hover:bg-slate-100 px-2.5 py-1.5 rounded-md border border-slate-200 transition-colors"
            >
              {expanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
              <span>{expanded ? 'Less' : 'Details'}</span>
            </button>
          )}
        </div>
      </div>

      {/* Observations preview (always visible if <= 6) */}
      {hasObs && (
        <div className="p-4 space-y-3">
          <ObservationTable
            observations={
              expanded || encounter.observations.length <= 6
                ? encounter.observations
                : encounter.observations.slice(0, 6)
            }
          />
          {!expanded && encounter.observations.length > 6 && (
            <button
              onClick={() => setExpanded(true)}
              className="text-xs text-primary hover:underline"
            >
              + {encounter.observations.length - 6} more observations
            </button>
          )}
        </div>
      )}

      {/* Summary (expandable) */}
      {expanded && encounter.summary && (
        <div className="px-4 pb-4">
          <p className="text-xs text-slate-600 leading-relaxed bg-slate-50 p-3 rounded-lg border border-slate-100">
            {encounter.summary}
          </p>
        </div>
      )}

      {/* Empty state for no observations */}
      {!hasObs && !encounter.summary && (
        <div className="px-4 pb-4 pt-2">
          <p className="text-xs text-slate-400 italic">
            No structured clinical observations extracted from this document.
          </p>
        </div>
      )}
    </div>
  );
}

// ─── Timeline statistics header ───────────────────────────────────────────────

function TimelineStatsHeader({ stats }: { stats: ITimelineStats | null }) {
  if (!stats || stats.total_events === 0) return null;
  return (
    <div className="bg-gradient-to-r from-primary/5 via-blue-50 to-purple-50 rounded-xl border border-primary/15 p-4 shadow-sm">
      <div className="flex items-center gap-2 mb-3">
        <Activity className="h-4 w-4 text-primary" />
        <span className="text-sm font-bold text-slate-800">Clinical Timeline Intelligence</span>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: 'Total Records', value: stats.total_events, icon: BarChart3 },
          { label: 'Laboratory', value: stats.lab_count, icon: FlaskConical },
          { label: 'Vitals', value: stats.vitals_count, icon: HeartPulse },
          { label: 'Prescriptions', value: stats.prescription_count, icon: Pill },
        ].map(({ label, value, icon: Icon }) => (
          <div key={label} className="bg-white/70 rounded-lg p-3 border border-white/80 text-center">
            <Icon className="h-4 w-4 text-slate-400 mx-auto mb-1" />
            <p className="text-xl font-bold text-slate-900">{value}</p>
            <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wide">{label}</p>
          </div>
        ))}
      </div>
      {stats.first_record && stats.latest_record && (
        <p className="text-xs text-slate-500 mt-3 text-center font-medium">
          <span className="font-bold text-slate-700">{stats.first_record}</span>
          <span className="mx-2 text-slate-400">→</span>
          <span className="font-bold text-slate-700">{stats.latest_record}</span>
        </p>
      )}
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

export default function PatientTimelineView({ patientId }: PatientTimelineViewProps) {
  const [visitGroups, setVisitGroups] = useState<IVisitGroup[]>([]);
  const [stats, setStats] = useState<ITimelineStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [docTypeFilter, setDocTypeFilter] = useState('');
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);

  const fetchTimeline = useCallback(async () => {
    try {
      setLoading(true);
      const [timelineRes, statsRes] = await Promise.all([
        timelineApi.getPatientTimeline(patientId, {
          search: search || undefined,
          doc_type: docTypeFilter || undefined,
        }),
        timelineApi.getTimelineStats(patientId),
      ]);
      if (timelineRes.data) setVisitGroups(timelineRes.data);
      if (statsRes.data) setStats(statsRes.data);
    } catch (err) {
      console.error('Failed to fetch patient timeline:', err);
    } finally {
      setLoading(false);
    }
  }, [patientId, search, docTypeFilter]);

  useEffect(() => {
    fetchTimeline();
  }, [fetchTimeline]);

  const filters = [
    { label: 'All Events', value: '', active: 'bg-primary text-white', inactive: 'bg-slate-100 text-slate-600 hover:bg-slate-200' },
    { label: 'Labs', value: 'LAB', active: 'bg-blue-600 text-white', inactive: 'bg-slate-100 text-slate-600 hover:bg-blue-50 hover:text-blue-700' },
    { label: 'Prescriptions', value: 'PRESCRIPTION', active: 'bg-emerald-600 text-white', inactive: 'bg-slate-100 text-slate-600 hover:bg-emerald-50 hover:text-emerald-700' },
    { label: 'Vitals', value: 'VITALS', active: 'bg-red-600 text-white', inactive: 'bg-slate-100 text-slate-600 hover:bg-red-50 hover:text-red-700' },
    { label: 'Notes', value: 'NOTE', active: 'bg-purple-600 text-white', inactive: 'bg-slate-100 text-slate-600 hover:bg-purple-50 hover:text-purple-700' },
  ];

  const totalIncomplete = visitGroups.reduce((sum, g) => sum + g.incomplete_count, 0);

  return (
    <div className="space-y-5">
      {/* Timeline Intelligence Stats Header */}
      <TimelineStatsHeader stats={stats} />

      {/* Search & Filter Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex flex-col md:flex-row gap-4 items-stretch md:items-center justify-between">
        <div className="relative flex-1 max-w-lg">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by parameter, medicine, or condition…"
            className="w-full h-9 pl-9 pr-4 rounded-md border border-slate-200 text-sm focus:border-primary focus:ring-1 focus:ring-primary outline-none bg-slate-50 focus:bg-white transition-colors"
          />
        </div>

        <div className="flex items-center gap-2 overflow-x-auto pb-1 md:pb-0 shrink-0">
          {filters.map(({ label, value, active, inactive }) => (
            <button
              key={value}
              onClick={() => setDocTypeFilter(value)}
              className={`px-3 py-1.5 text-xs font-semibold rounded-full transition-colors whitespace-nowrap border ${
                docTypeFilter === value
                  ? `${active} border-transparent`
                  : `${inactive} border-transparent`
              }`}
            >
              {label}
            </button>
          ))}
          <button
            onClick={fetchTimeline}
            className="ml-1 p-1.5 text-slate-400 hover:text-primary hover:bg-primary/5 rounded-md transition-colors"
            title="Refresh timeline"
          >
            <RefreshCw className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* Incomplete documents notice */}
      {totalIncomplete > 0 && !loading && (
        <div className="flex items-center gap-3 bg-amber-50 border border-amber-200 rounded-xl p-3 text-sm">
          <AlertTriangle className="h-4 w-4 text-amber-500 shrink-0" />
          <span className="text-amber-800 font-medium">
            {totalIncomplete} document{totalIncomplete !== 1 ? 's' : ''} could not be fully processed — shown below with details.
          </span>
        </div>
      )}

      {/* Timeline Stream */}
      {loading ? (
        <div className="py-16">
          <Loader label="Reconstructing longitudinal clinical history…" />
        </div>
      ) : visitGroups.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center shadow-sm">
          <EmptyState
            icon={Calendar}
            title="No Clinical Events Recorded"
            description={
              search || docTypeFilter
                ? 'No clinical events matched your search filters.'
                : 'Upload medical records in the Medical Records tab to build a structured longitudinal timeline.'
            }
          />
        </div>
      ) : (
        <div className="relative border-l-2 border-slate-200 ml-4 md:ml-6 space-y-8 pl-6 md:pl-8 py-2">
          {visitGroups.map((group, gIdx) => (
            <div key={gIdx} className="relative">
              {/* Timeline node */}
              <div className="absolute -left-[31px] md:-left-[39px] top-1.5 flex h-6 w-6 items-center justify-center rounded-full bg-white border-2 border-primary text-primary shadow-sm">
                <Calendar className="h-3 w-3" />
              </div>

              {/* Date label */}
              <div className="mb-3">
                <div className="flex items-baseline gap-3 flex-wrap">
                  <h3 className="text-base font-bold text-slate-900">{group.display_date}</h3>
                  <span className="text-xs text-slate-400 font-medium">{group.day_label.split(',')[0]}</span>
                  <div className="flex items-center gap-2">
                    {group.observation_count > 0 && (
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20">
                        {group.observation_count} observations
                      </span>
                    )}
                    {group.incomplete_count > 0 && (
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 border border-amber-200">
                        {group.incomplete_count} incomplete
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Encounter cards for this date */}
              <div className="space-y-3">
                {group.encounters.map((encounter) => (
                  <EncounterCard
                    key={encounter.id}
                    encounter={encounter}
                    onViewSource={setSelectedDocId}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Document Viewer Modal */}
      <SourceEvidenceDrawer
        documentId={selectedDocId}
        isOpen={!!selectedDocId}
        onClose={() => setSelectedDocId(null)}
      />
    </div>
  );
}
