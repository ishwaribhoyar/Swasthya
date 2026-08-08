import { 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  Area,
  ComposedChart
} from 'recharts';
import { COLORS } from '@/theme/colors';

interface LineTrendChartProps {
  data: any[];
  title: string;
  xKey: string;
  yKey: string;
  color?: string;
  unit?: string;
}

export default function LineTrendChart({ 
  data, 
  title, 
  xKey, 
  yKey, 
  color = COLORS.primary,
  unit = ''
}: LineTrendChartProps) {
  // Format numeric values cleanly
  const formattedData = data.map(d => ({
    ...d,
    displayValue: typeof d[yKey] === 'number' ? Number(d[yKey].toFixed(2)) : d[yKey]
  }));

  return (
    <div className="w-full bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wide">{title}</h3>
        <span className="text-xs font-mono font-medium text-slate-500 bg-slate-100 px-2.5 py-1 rounded-md">
          {formattedData.length} Measurements
        </span>
      </div>

      <div className="w-full h-[320px] pt-2">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={formattedData} margin={{ top: 10, right: 30, bottom: 25, left: 10 }}>
            <defs>
              <linearGradient id={`colorGradient-${yKey}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={color} stopOpacity={0.15} />
                <stop offset="95%" stopColor={color} stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
            <XAxis 
              dataKey={xKey} 
              axisLine={{ stroke: '#cbd5e1' }}
              tickLine={false} 
              tick={{ fontSize: 11, fill: '#64748b', fontWeight: 500 }} 
              dy={10} 
            />
            <YAxis 
              axisLine={false} 
              tickLine={false} 
              domain={['auto', 'auto']}
              tick={{ fontSize: 11, fill: '#64748b', fontWeight: 500 }} 
              dx={-5}
            />
            <Tooltip 
              content={({ active, payload, label }) => {
                if (active && payload && payload.length) {
                  const dataPoint = payload[0].payload;
                  return (
                    <div className="bg-slate-900 text-white p-3 rounded-lg shadow-xl text-xs space-y-1 font-sans border border-slate-700">
                      <p className="font-semibold text-slate-300">{label}</p>
                      <p className="text-base font-bold text-sky-400 font-mono">
                        {dataPoint.displayValue} {dataPoint.unit || unit}
                      </p>
                      {dataPoint.status && (
                        <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          dataPoint.status === 'CRITICAL' ? 'bg-red-500/20 text-red-300 border border-red-500/30' :
                          dataPoint.status === 'HIGH' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' :
                          'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                        }`}>
                          Status: {dataPoint.status}
                        </span>
                      )}
                    </div>
                  );
                }
                return null;
              }}
            />
            <Area 
              type="monotone" 
              dataKey="displayValue" 
              fill={`url(#colorGradient-${yKey})`} 
              stroke="none" 
            />
            <Line 
              type="monotone" 
              dataKey="displayValue" 
              stroke={color} 
              strokeWidth={3} 
              dot={{ r: 5, fill: '#ffffff', stroke: color, strokeWidth: 3 }} 
              activeDot={{ r: 7, fill: color, stroke: '#ffffff', strokeWidth: 2 }} 
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
