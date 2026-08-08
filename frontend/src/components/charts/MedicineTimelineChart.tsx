import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { COLORS } from '@/theme/colors';

interface MedicineTimelineChartProps {
  data: any[];
  title: string;
}

export default function MedicineTimelineChart({ data, title }: MedicineTimelineChartProps) {
  return (
    <div className="w-full h-full min-h-[300px] flex flex-col bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-700 mb-4">{title}</h3>
      <div className="flex-1">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 5, right: 5, bottom: 5, left: -20 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
            <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} dy={10} />
            <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} />
            <Tooltip cursor={{ fill: '#f8fafc' }} contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0' }} />
            <Legend iconType="circle" />
            <Bar dataKey="taken" name="Taken" fill={COLORS.secondary} radius={[4, 4, 0, 0]} />
            <Bar dataKey="missed" name="Missed" fill={COLORS.error} radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
