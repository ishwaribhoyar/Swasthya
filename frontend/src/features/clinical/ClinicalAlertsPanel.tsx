import { useState } from 'react';
import { ShieldAlert, Check } from 'lucide-react';
import { IClinicalAlert, AlertSeverity } from '@/types/clinical';

interface ClinicalAlertsPanelProps {
  alerts: IClinicalAlert[];
  onAcknowledge: (alertId: string) => Promise<void>;
}

const SEVERITY_BADGES: Record<AlertSeverity, { bg: string; color: string; border: string }> = {
  CRITICAL: { bg: 'bg-red-50', color: 'text-red-700', border: 'border-red-200' },
  HIGH: { bg: 'bg-amber-50', color: 'text-amber-700', border: 'border-amber-200' },
  MODERATE: { bg: 'bg-blue-50', color: 'text-blue-700', border: 'border-blue-200' },
  INFORMATIONAL: { bg: 'bg-slate-50', color: 'text-slate-700', border: 'border-slate-200' },
};

export default function ClinicalAlertsPanel({ alerts, onAcknowledge }: ClinicalAlertsPanelProps) {
  const [ackingId, setAckingId] = useState<string | null>(null);

  if (alerts.length === 0) return null;

  const handleAck = async (id: string) => {
    try {
      setAckingId(id);
      await onAcknowledge(id);
    } finally {
      setAckingId(null);
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ShieldAlert className="h-5 w-5 text-red-500" />
          <h3 className="text-base font-semibold text-slate-900">Active Clinical Severity Alerts</h3>
        </div>
        <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-100 text-red-800 border border-red-200">
          {alerts.filter((a) => !a.is_acknowledged).length} Unacknowledged
        </span>
      </div>

      <div className="space-y-3">
        {alerts.map((alert) => {
          const badge = SEVERITY_BADGES[alert.severity] || SEVERITY_BADGES.MODERATE;

          return (
            <div
              key={alert.id}
              className={`p-4 rounded-xl border transition-all ${badge.bg} ${badge.border} ${
                alert.is_acknowledged ? 'opacity-60' : ''
              }`}
            >
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${badge.bg} ${badge.color} border ${badge.border}`}>
                      {alert.severity}
                    </span>
                    <h4 className="text-sm font-bold text-slate-900">{alert.title}</h4>
                  </div>
                  <p className="text-xs text-slate-700 leading-relaxed">{alert.message}</p>
                </div>

                {!alert.is_acknowledged ? (
                  <button
                    onClick={() => handleAck(alert.id)}
                    disabled={ackingId === alert.id}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-200 hover:bg-slate-50 rounded-lg shadow-2xs transition-colors shrink-0"
                  >
                    <Check className="h-3.5 w-3.5 text-emerald-600" />
                    <span>{ackingId === alert.id ? 'Acknowledging...' : 'Acknowledge'}</span>
                  </button>
                ) : (
                  <span className="text-xs font-medium text-emerald-700 flex items-center gap-1 shrink-0">
                    <Check className="h-3.5 w-3.5" /> Acknowledged
                  </span>
                )}
              </div>

              {alert.action_recommendation && (
                <div className="mt-3 p-2.5 rounded-lg bg-white/80 border border-slate-200 text-xs text-slate-800 space-y-1">
                  <span className="font-semibold text-slate-900 block text-[11px]">Recommended Clinical Action:</span>
                  <p className="text-slate-600 text-[11px] leading-relaxed">{alert.action_recommendation}</p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
