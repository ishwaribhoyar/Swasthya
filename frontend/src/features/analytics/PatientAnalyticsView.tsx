import { useState, useEffect, useCallback } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Activity,
  AlertTriangle,
  Info,
  Droplets,
  CheckCircle2,
  HelpCircle,
  RotateCcw,
} from 'lucide-react';
import Loader from '@/components/common/Loader';
import EmptyState from '@/components/common/EmptyState';
import { LineTrendChart } from '@/components/charts';
import { analyticsApi, IAnalyticsOverview } from '@/services/api/analytics';
import { clinicalApi } from '@/services/api/clinical';
import SourceEvidenceDrawer from '@/features/ingestion/SourceEvidenceDrawer';
import { ExternalLink } from 'lucide-react';

interface PatientAnalyticsViewProps {
  patientId: string;
}

export default function PatientAnalyticsView({ patientId }: PatientAnalyticsViewProps) {
  const [analytics, setAnalytics] = useState<IAnalyticsOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [reanalyzing, setReanalyzing] = useState(false);
  const [selectedParameter, setSelectedParameter] = useState<string | null>(null);
  const [sourceDocId, setSourceDocId] = useState<string | null>(null);

  const fetchAnalytics = useCallback(async () => {
    try {
      setLoading(true);
      const res = await analyticsApi.getPatientTrends(patientId);
      if (res.data) {
        setAnalytics(res.data);
        const trList = res.data.parameter_trends || [];
        if (trList.length > 0 && !selectedParameter) {
          setSelectedParameter(trList[0].normalized_name);
        }
      }

    } catch (err) {
      console.error('Failed to fetch patient analytics trends:', err);
    } finally {
      setLoading(false);
    }
  }, [patientId, selectedParameter]);

  const handleReanalyze = async () => {
    try {
      setReanalyzing(true);
      await clinicalApi.analyze(patientId);
      await fetchAnalytics();
    } catch (err) {
      console.error('Re-analysis failed:', err);
    } finally {
      setReanalyzing(false);
    }
  };


  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  const getDirectionBadge = (dir: string) => {
    switch (dir) {
      case 'INCREASING':
      case 'RAPIDLY_INCREASING':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-50 text-amber-800 border border-amber-200">
            <TrendingUp className="h-3.5 w-3.5 text-amber-600" /> {dir.replace('_', ' ')}
          </span>
        );
      case 'DECREASING':
      case 'RAPIDLY_DECREASING':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-50 text-blue-800 border border-blue-200">
            <TrendingDown className="h-3.5 w-3.5 text-blue-600" /> {dir.replace('_', ' ')}
          </span>
        );
      case 'STABLE':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" /> STABLE
          </span>
        );
      case 'INSUFFICIENT_DATA':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200">
            <HelpCircle className="h-3.5 w-3.5" /> Insufficient Data
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-purple-50 text-purple-800 border border-purple-200">
            <Activity className="h-3.5 w-3.5 text-purple-600" /> {dir.replace('_', ' ')}
          </span>
        );
    }
  };

  if (loading) {
    return (
      <div className="py-16">
        <Loader label="Evaluating longitudinal parameter trends & anomaly analytics..." />
      </div>
    );
  }

  const trends = analytics?.parameter_trends || [];

  const activeAnomalies = analytics?.active_anomalies || [];

  if (!analytics || trends.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-12 text-center shadow-sm">
        <EmptyState
          icon={Activity}
          title="No Longitudinal Trend Data Available"
          description="Upload multiple lab reports or vitals sheets over time to construct time-series trend curves and anomaly intelligence."
        />
      </div>
    );
  }

  const activeTrend = trends.find((t) => t.normalized_name === selectedParameter) || trends[0];

  return (
    <div className="space-y-6">
      {/* Active Anomalies & Overview Banner */}
      {activeAnomalies.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
          <div>
            <h4 className="text-sm font-bold text-amber-900">Clinical Anomalies Detected</h4>
            <div className="flex flex-wrap gap-2 mt-2">
              {activeAnomalies.map((anom, aIdx) => (
                <span
                  key={aIdx}
                  className="inline-flex items-center px-2.5 py-0.5 rounded text-xs font-semibold bg-white text-amber-800 border border-amber-300 shadow-2xs"
                >
                  {anom}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Parameter Selector Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
            Tracked Longitudinal Parameters ({trends.length}):
          </span>
          <button
            onClick={handleReanalyze}
            disabled={reanalyzing}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-blue-700 bg-blue-50 border border-blue-200 hover:bg-blue-100 rounded-lg transition-colors shadow-2xs disabled:opacity-50"
          >
            <RotateCcw className={`h-3.5 w-3.5 ${reanalyzing ? 'animate-spin' : ''}`} />
            <span>{reanalyzing ? 'Re-analyzing...' : 'Re-analyze Patient Intelligence'}</span>
          </button>
        </div>

        <div className="flex flex-wrap gap-2">
          {trends.map((t) => (
            <button
              key={t.normalized_name}
              onClick={() => setSelectedParameter(t.normalized_name)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all border ${
                t.normalized_name === activeTrend.normalized_name
                  ? 'bg-primary text-white font-semibold border-primary shadow-xs'
                  : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
              }`}
            >
              {t.parameter_name}
              <span className="ml-1.5 opacity-80 font-mono">
                ({t.observation_count})
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Active Parameter Trend Card */}
      {activeTrend && (
        <div className="space-y-6">
          {/* Trend Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-1">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">Latest Measurement</span>
              <div className="text-xl font-bold font-mono text-slate-900">
                {activeTrend.latest_value} {activeTrend.unit}
              </div>
              <span className="text-xs text-slate-500 block font-mono">{activeTrend.latest_date}</span>
            </div>

            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-1">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">Trend Classification</span>
              <div>{getDirectionBadge(activeTrend.direction)}</div>
              <span className="text-xs text-slate-500 block">
                Confidence: {((activeTrend.confidence ?? 1) * 100).toFixed(0)}%
              </span>
            </div>

            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-1">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">Longitudinal Shift</span>
              <div
                className={`text-lg font-bold font-mono ${
                  (activeTrend.absolute_change ?? 0) > 0
                    ? 'text-amber-600'
                    : (activeTrend.absolute_change ?? 0) < 0
                    ? 'text-blue-600'
                    : 'text-slate-700'
                }`}
              >
                {(activeTrend.absolute_change ?? 0) > 0 ? `+${activeTrend.absolute_change}` : activeTrend.absolute_change ?? 0}{' '}
                {activeTrend.unit} ({(activeTrend.percentage_change ?? 0).toFixed(1)}%)
              </div>
              <span className="text-xs text-slate-500 block">Across {activeTrend.observation_count ?? 0} points</span>
            </div>

            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-1">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">Rate of Change</span>
              <div className="text-lg font-bold font-mono text-slate-800">
                {(activeTrend.rate_of_change_per_day ?? 0).toFixed(3)} {activeTrend.unit}/day
              </div>
              <span className="text-xs text-slate-500 block">Time Span: {activeTrend.time_span_days ?? 0} days</span>
            </div>
          </div>

          {/* Recharts Longitudinal Time-Series Chart */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
            <h3 className="text-base font-semibold text-slate-900 mb-4 flex items-center gap-2">
              <Activity className="h-5 w-5 text-primary" />
              <span>{activeTrend.parameter_name} Time-Series Trend Curve</span>
            </h3>

            {(activeTrend.points || []).length < 2 ? (
              <div className="p-8 text-center bg-slate-50 rounded-lg border border-slate-200 space-y-2">
                <Info className="h-6 w-6 text-slate-400 mx-auto" />
                <p className="text-xs text-slate-600 font-medium">
                  Single measurement available ({activeTrend.latest_value} {activeTrend.unit} on {activeTrend.latest_date}).
                  A minimum of 2 observations is required to generate a longitudinal trend curve.
                </p>
              </div>
            ) : (
              <LineTrendChart
                data={activeTrend.points || []}
                title={`${activeTrend.parameter_name} (${activeTrend.unit})`}
                xKey="date"
                yKey="value"
                unit={activeTrend.unit}
                color="#1D6FA4"
              />
            )}
          </div>

          {/* Parameter History Measurements Table */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4">
            <h3 className="text-base font-semibold text-slate-900 flex items-center gap-2">
              <Droplets className="h-5 w-5 text-blue-500" />
              <span>{activeTrend.parameter_name} Measurement History</span>
            </h3>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-sm">
                <thead>
                  <tr className="border-b bg-slate-50 text-slate-500 font-medium text-xs uppercase tracking-wider">
                    <th className="py-3 px-4">Event Date</th>
                    <th className="py-3 px-4">Observed Value</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Source</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {(activeTrend.points || []).map((pt, pIdx) => (
                    <tr key={pIdx} className="hover:bg-slate-50/80 transition-colors">
                      <td className="py-3.5 px-4 font-mono text-xs font-semibold text-slate-700">{pt.date}</td>
                      <td className="py-3.5 px-4 font-mono font-bold text-slate-900">
                        {pt.value} {pt.unit}
                      </td>
                      <td className="py-3.5 px-4">
                        <span
                          className={`px-2.5 py-0.5 rounded-full text-xs font-bold font-mono border ${
                            pt.status === 'NORMAL'
                              ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                              : pt.status.includes('CRITICAL')
                              ? 'bg-red-50 text-red-700 border-red-200'
                              : 'bg-amber-50 text-amber-700 border-amber-200'
                          }`}
                        >
                          {pt.status}
                        </span>
                      </td>
                      <td className="py-3.5 px-4">
                        {pt.source_record_id ? (
                          <button
                            onClick={() => setSourceDocId(pt.source_record_id)}
                            className="flex items-center gap-1 text-[11px] font-semibold text-primary hover:text-primary/70 transition-colors"
                            title="View original source document for this measurement"
                          >
                            <ExternalLink className="h-3 w-3" />
                            View Source
                          </button>
                        ) : (
                          <span className="text-[11px] text-slate-400 italic">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      <SourceEvidenceDrawer
        documentId={sourceDocId}
        isOpen={!!sourceDocId}
        onClose={() => setSourceDocId(null)}
      />
    </div>
  );
}
