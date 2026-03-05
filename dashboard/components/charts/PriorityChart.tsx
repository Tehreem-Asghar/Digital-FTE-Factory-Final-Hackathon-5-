'use client';

import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  Cell
} from 'recharts';

interface PriorityChartProps {
  data: { priority: string; count: number }[];
}

const PRIORITY_COLORS: Record<string, string> = {
  high: '#ef4444',
  medium: '#f59e0b',
  low: '#10b981'
};

export default function PriorityChart({ data }: PriorityChartProps) {
  const chartData = data.map(item => ({
    name: item.priority.charAt(0).toUpperCase() + item.priority.slice(1),
    count: item.count,
    rawPriority: item.priority.toLowerCase()
  }));

  return (
    <div className="h-[300px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart 
          layout="vertical" 
          data={chartData} 
          margin={{ top: 20, right: 30, left: 20, bottom: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e2e8f0" />
          <XAxis 
            type="number"
            axisLine={false} 
            tickLine={false} 
            tick={{ fill: '#64748b', fontSize: 14, fontWeight: 600 }}
          />
          <YAxis 
            type="category"
            dataKey="name" 
            axisLine={false} 
            tickLine={false} 
            tick={{ fill: '#64748b', fontSize: 14, fontWeight: 600 }}
          />
          <Tooltip 
            cursor={{ fill: '#f8fafc' }}
            contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
          />
          <Bar dataKey="count" barSize={32} radius={[0, 4, 4, 0]}>
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={PRIORITY_COLORS[entry.rawPriority] || '#cbd5e1'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
