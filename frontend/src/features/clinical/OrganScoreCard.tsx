import { Activity, Heart, ShieldAlert, Zap, Thermometer, Droplets, Stethoscope, Wind, HelpCircle } from 'lucide-react';
import { IOrganScore, OrganStatus } from '@/types/clinical';

interface OrganScoreCardProps {
  score: IOrganScore;
}

const SYSTEM_ICONS: Record<string, any> = {
  hematological: Droplets,
  renal: Stethoscope,
  hepatic: Activity,
  cardiovascular: Heart,
  metabolic: Zap,
  respiratory: Wind,
  inflammatory: ShieldAlert,
  electrolyte: Thermometer,
};

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string; border: string; bar: string }> = {
  OPTIMAL: {
    label: 'Optimal Function',
    color: 'text-emerald-700',
    bg: 'bg-emerald-50',
    border: 'border-emerald-200',
    bar: 'bg-emerald-500',
  },
  MILD_STRAIN: {
    label: 'Mild Strain',
    color: 'text-amber-700',
    bg: 'bg-amber-50',
    border: 'border-amber-200',
    bar: 'bg-amber-500',
  },
  MODERATE_IMPAIRMENT: {
    label: 'Moderate Impairment',
    color: 'text-orange-700',
    bg: 'bg-orange-50',
    border: 'border-orange-200',
    bar: 'bg-orange-500',
  },
  SEVERE_DYSFUNCTION: {
    label: 'Critical Concern',
    color: 'text-red-700',
    bg: 'bg-red-50',
    border: 'border-red-200',
    bar: 'bg-red-500',
  },
  INSUFFICIENT_DATA: {
    label: 'Insufficient Data',
    color: 'text-slate-500',
    bg: 'bg-slate-100',
    border: 'border-slate-200',
    bar: 'bg-slate-300',
  },
};

export default function OrganScoreCard({ score }: OrganScoreCardProps) {
  const Icon = SYSTEM_ICONS[score.organ_system] || Activity;
  const isInsufficient = score.score === null || score.status === ('INSUFFICIENT_DATA' as any);
  const cfg = isInsufficient ? STATUS_CONFIG.INSUFFICIENT_DATA : (STATUS_CONFIG[score.status] || STATUS_CONFIG.OPTIMAL);

  let biomarkers: string[] = [];
  try {
    if (score.contributing_biomarkers) {
      biomarkers = JSON.parse(score.contributing_biomarkers);
    }
  } catch {
    biomarkers = [];
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className={`flex h-9 w-9 items-center justify-center rounded-lg ${cfg.bg} ${cfg.color}`}>
            <Icon className="h-5 w-5" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-900 capitalize">
              {score.organ_system.replace('_', ' ')} System
            </h4>
            <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${cfg.bg} ${cfg.color} ${cfg.border}`}>
              {cfg.label}
            </span>
          </div>
        </div>

        <span className="text-xl font-bold text-slate-900 font-mono">
          {score.score !== null && score.score !== undefined ? `${score.score.toFixed(0)}%` : '—'}
        </span>
      </div>

      {/* Progress Gauge */}
      <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
        <div
          className={`h-full transition-all duration-500 rounded-full ${cfg.bar}`}
          style={{ width: score.score !== null && score.score !== undefined ? `${Math.max(5, score.score)}%` : '0%' }}
        />
      </div>

      <p className="text-xs text-slate-500 leading-relaxed">{score.rationale || 'Evaluated from patient labs and vitals.'}</p>

      {biomarkers.length > 0 && (
        <div className="flex flex-wrap gap-1 pt-1">
          {biomarkers.map((bm, i) => (
            <span key={i} className="text-[10px] font-mono px-2 py-0.5 bg-slate-50 text-slate-600 rounded border border-slate-200">
              {bm}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
