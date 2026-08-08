import { useState, useEffect, useCallback } from 'react';
import {
  Calendar,
  Search,
  Filter,
  Eye,
  Clock,
  FlaskConical,
  Pill,
  HeartPulse,
  Stethoscope,
} from 'lucide-react';
import Loader from '@/components/common/Loader';
import EmptyState from '@/components/common/EmptyState';
import DocumentViewerModal from '@/features/ingestion/DocumentViewerModal';
import { timelineApi, IVisitGroup } from '@/services/api/timeline';


interface PatientTimelineViewProps {
  patientId: string;
}

export default function PatientTimelineView({ patientId }: PatientTimelineViewProps) {
  const [visitGroups, setVisitGroups] = useState<IVisitGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [docTypeFilter, setDocTypeFilter] = useState('');
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);

  const fetchTimeline = useCallback(async () => {
    try {
      setLoading(true);
      const res = await timelineApi.getPatientTimeline(patientId, {
        search: search || undefined,
        doc_type: docTypeFilter || undefined,
      });
      if (res.data) {
        setVisitGroups(res.data);
      }
    } catch (err) {
      console.error('Failed to fetch patient timeline:', err);
    } finally {
      setLoading(false);
    }
  }, [patientId, search, docTypeFilter]);

  useEffect(() => {
    fetchTimeline();
  }, [fetchTimeline]);

  const getEventIcon = (docType: string) => {
    switch (docType.toUpperCase()) {
      case 'LAB':
      case 'LAB_REPORT':
        return <FlaskConical className="h-4 w-4 text-blue-600" />;
      case 'PRESCRIPTION':
        return <Pill className="h-4 w-4 text-emerald-600" />;
      case 'VITALS':
        return <HeartPulse className="h-4 w-4 text-red-600" />;
      default:
        return <Stethoscope className="h-4 w-4 text-purple-600" />;
    }
  };

  const getCategoryBadgeClass = (category: string) => {
    switch (category.toUpperCase()) {
      case 'LAB':
      case 'LAB_REPORT':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'PRESCRIPTION':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'VITALS':
        return 'bg-red-50 text-red-700 border-red-200';
      default:
        return 'bg-purple-50 text-purple-700 border-purple-200';
    }
  };

  return (
    <div className="space-y-6">
      {/* Search & Filter Header */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex flex-col md:flex-row gap-4 items-stretch md:items-center justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search timeline by parameter, medicine, date, or diagnostic text..."
            className="w-full h-9 pl-9 pr-4 rounded-md border border-slate-200 text-sm focus:border-primary focus:ring-1 focus:ring-primary outline-none"
          />
        </div>

        <div className="flex items-center gap-2 overflow-x-auto pb-1 md:pb-0">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-1 shrink-0">
            <Filter className="h-3.5 w-3.5" /> Category:
          </span>

          <button
            onClick={() => setDocTypeFilter('')}
            className={`px-3 py-1 text-xs font-medium rounded-full transition-colors ${
              docTypeFilter === ''
                ? 'bg-primary text-white font-semibold'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            All Events
          </button>

          <button
            onClick={() => setDocTypeFilter('LAB')}
            className={`px-3 py-1 text-xs font-medium rounded-full transition-colors ${
              docTypeFilter === 'LAB'
                ? 'bg-blue-600 text-white font-semibold'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            Labs
          </button>

          <button
            onClick={() => setDocTypeFilter('PRESCRIPTION')}
            className={`px-3 py-1 text-xs font-medium rounded-full transition-colors ${
              docTypeFilter === 'PRESCRIPTION'
                ? 'bg-emerald-600 text-white font-semibold'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            Prescriptions
          </button>

          <button
            onClick={() => setDocTypeFilter('VITALS')}
            className={`px-3 py-1 text-xs font-medium rounded-full transition-colors ${
              docTypeFilter === 'VITALS'
                ? 'bg-red-600 text-white font-semibold'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            Vitals
          </button>

          <button
            onClick={() => setDocTypeFilter('NOTE')}
            className={`px-3 py-1 text-xs font-medium rounded-full transition-colors ${
              docTypeFilter === 'NOTE'
                ? 'bg-purple-600 text-white font-semibold'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            Clinical Notes
          </button>
        </div>
      </div>

      {/* Timeline Stream Area */}
      {loading ? (
        <div className="py-16">
          <Loader label="Reconstructing longitudinal clinical event history..." />
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
            <div key={gIdx} className="relative group">
              {/* Timeline Node Dot */}
              <div className="absolute -left-[31px] md:-left-[39px] top-1.5 flex h-6 w-6 items-center justify-center rounded-full bg-white border-2 border-primary text-primary shadow-xs">
                <Calendar className="h-3 w-3" />
              </div>

              {/* Visit Encounter Card */}
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden space-y-4 p-5 hover:shadow-md transition-shadow">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-100 pb-3 gap-2">
                  <div>
                    <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                      <span>{group.visit_title}</span>
                    </h3>
                    <p className="text-xs text-slate-500 font-medium mt-0.5">
                      {group.event_count} {group.event_count === 1 ? 'Clinical Event' : 'Clinical Events'} Encapsulated
                    </p>
                  </div>

                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-bold bg-slate-100 text-slate-700 border border-slate-200 self-start sm:self-auto">
                    <Clock className="h-3.5 w-3.5 text-slate-500" />
                    {group.visit_date}
                  </span>
                </div>

                {/* Sub-events inside this visit group */}
                <div className="space-y-4 divide-y divide-slate-100">
                  {group.events.map((event) => (
                    <div key={event.id} className="pt-3 first:pt-0 space-y-3">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex items-start gap-3">
                          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-50 border border-slate-200 shrink-0 mt-0.5">
                            {getEventIcon(event.document_type)}
                          </div>
                          <div>
                            <div className="flex items-center gap-2 flex-wrap">
                              <h4 className="text-sm font-semibold text-slate-900">{event.title}</h4>
                              <span className={`px-2 py-0.5 text-[10px] uppercase font-bold rounded border ${getCategoryBadgeClass(event.document_type)}`}>
                                {event.document_type}
                              </span>
                            </div>

                            {/* Date Provenance Tag */}
                            <div className="flex items-center gap-2 mt-1 text-xs text-slate-500 font-medium">
                              <span>Clinical Date Priority:</span>
                              <span className="font-mono text-slate-700 font-semibold">{event.event_date_type}</span>
                              <span>•</span>
                              <span>Confidence: {(event.event_date_confidence * 100).toFixed(0)}%</span>
                            </div>
                          </div>
                        </div>

                        {/* Source Document Viewer Button */}
                        <button
                          onClick={() => setSelectedDocId(event.source_record_id)}
                          className="flex items-center gap-1 text-xs font-medium text-primary hover:text-primary/80 bg-primary/5 hover:bg-primary/10 px-2.5 py-1.5 rounded-md border border-primary/20 transition-colors shrink-0"
                        >
                          <Eye className="h-3.5 w-3.5" />
                          <span>View Source</span>
                        </button>
                      </div>

                      {/* Event Clinical Summary */}
                      <p className="text-xs text-slate-700 leading-relaxed bg-slate-50/80 p-3 rounded-lg border border-slate-100 font-sans">
                        {event.summary}
                      </p>

                      {/* Extracted Parameters / Entities Metadata List */}
                      {event.metadata_json && event.metadata_json.parameters && (
                        <div className="space-y-1.5">
                          <span className="text-[10px] uppercase tracking-wider font-bold text-slate-400 block">
                            Extracted Measurements & LOINC Codes:
                          </span>
                          <div className="flex flex-wrap gap-2">
                            {event.metadata_json.parameters.map((p: any, pIdx: number) => (
                              <span
                                key={pIdx}
                                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono font-medium bg-white border border-slate-200 text-slate-800 shadow-2xs"
                              >
                                <span className="font-semibold text-slate-900">{p.name}:</span>
                                <span className="font-bold text-primary">{p.value} {p.unit}</span>
                                {p.status && p.status !== 'NORMAL' && (
                                  <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-amber-100 text-amber-800 border border-amber-200">
                                    {p.status}
                                  </span>
                                )}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Document Viewer Modal */}
      <DocumentViewerModal
        documentId={selectedDocId}
        isOpen={!!selectedDocId}
        onClose={() => setSelectedDocId(null)}
      />
    </div>
  );
}
