import { ComposedChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { COLORS } from '@/theme/colors';

interface BloodPressureChartProps {
  data: any[];
  title: string;
}

export default function BloodPressureChart({ data, title }: BloodPressureChartProps) {
  return (
    <div className="w-full h-full min-h-[300px] flex flex-col bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-700 mb-4">{title}</h3>
      <div className="flex-1">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
            <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} dy={10} />
            <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} domain={['dataMin - 10', 'dataMax + 10']} />
            <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0' }} />
            <Legend iconType="circle" />
            <Line type="monotone" dataKey="systolic" name="Systolic" stroke={COLORS.error} strokeWidth={2} dot={{ r: 3 }} />
            <Line type="monotone" dataKey="diastolic" name="Diastolic" stroke={COLORS.primary} strokeWidth={2} dot={{ r: 3 }} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
