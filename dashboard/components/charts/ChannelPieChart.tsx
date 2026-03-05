'use client';

import { 
  PieChart, 
  Pie, 
  Cell, 
  ResponsiveContainer, 
  Legend, 
  Tooltip 
} from 'recharts';

interface ChannelPieChartProps {
  data: { channel: string; count: number }[];
}

const COLORS = ['#2563eb', '#10b981', '#a855f7', '#f59e0b', '#ef4444'];

export default function ChannelPieChart({ data }: ChannelPieChartProps) {
  const chartData = data.map(item => ({
    name: item.channel.charAt(0).toUpperCase() + item.channel.slice(1).replace('_', ' '),
    value: item.count
  }));

  return (
    <div className="h-[300px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={80}
            paddingAngle={5}
            dataKey="value"
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip 
            contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
          />
          <Legend verticalAlign="bottom" height={36}/>
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
