'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import ChannelPieChart from '@/components/charts/ChannelPieChart';
import StatusBarChart from '@/components/charts/StatusBarChart';
import PriorityChart from '@/components/charts/PriorityChart';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  LineChart, 
  Line,
  AreaChart,
  Area
} from 'recharts';

export default function AnalyticsPage() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadStats() {
      try {
        const data = await api.getDashboardStats();
        setStats(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadStats();
  }, []);

  if (loading) return (
    <div className="flex flex-col items-center justify-center py-20 animate-fade-in">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
      <p className="text-xl font-bold text-slate-500 tracking-tight">Loading Analytics...</p>
    </div>
  );

  // Mock data for trends since backend doesn't provide time-series yet
  const responseTimeData = [
    { name: 'Mon', time: 45 },
    { name: 'Tue', time: 52 },
    { name: 'Wed', time: 38 },
    { name: 'Thu', time: 65 },
    { name: 'Fri', time: 48 },
    { name: 'Sat', time: 35 },
    { name: 'Sun', time: 28 },
  ];

  const volumeData = [
    { name: 'Mon', tickets: 12 },
    { name: 'Tue', tickets: 19 },
    { name: 'Wed', tickets: 15 },
    { name: 'Thu', tickets: 22 },
    { name: 'Fri', tickets: 30 },
    { name: 'Sat', tickets: 10 },
    { name: 'Sun', tickets: 8 },
  ];

  return (
    <div className="space-y-6 sm:space-y-8 lg:space-y-10 animate-fade-in">
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">Analytics & Insights</h1>
        <p className="text-base sm:text-lg text-slate-500 mt-1">Deep dive into agent performance and ticket trends</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 sm:gap-8 lg:gap-10">
        <div className="bg-white p-4 sm:p-6 lg:p-8 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-all">
          <h2 className="text-lg sm:text-xl font-bold text-slate-900 mb-4 sm:mb-8">Average Response Time (min)</h2>
          <div className="h-[280px] sm:h-[350px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={responseTimeData}>
                <defs>
                  <linearGradient id="colorTime" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#2563eb" stopOpacity={0.1}/>
                    <stop offset="95%" stopColor="#2563eb" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 12, fontWeight: 600}} dy={10} />
                <YAxis axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 12, fontWeight: 600}} dx={-10} />
                <Tooltip
                  contentStyle={{borderRadius: '16px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)'}}
                  itemStyle={{fontWeight: 'bold', color: '#1e40af'}}
                />
                <Area type="monotone" dataKey="time" stroke="#2563eb" fillOpacity={1} fill="url(#colorTime)" strokeWidth={3} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white p-4 sm:p-6 lg:p-8 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-all">
          <h2 className="text-lg sm:text-xl font-bold text-slate-900 mb-4 sm:mb-8">Daily Ticket Volume</h2>
          <div className="h-[280px] sm:h-[350px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={volumeData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 12, fontWeight: 600}} dy={10} />
                <YAxis axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 12, fontWeight: 600}} dx={-10} />
                <Tooltip
                  contentStyle={{borderRadius: '16px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)'}}
                  cursor={{fill: '#f1f5f9'}}
                />
                <Bar dataKey="tickets" fill="#3b82f6" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8 lg:gap-10">
        <div className="bg-white p-4 sm:p-6 lg:p-8 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-all text-center">
          <h2 className="text-base sm:text-xl font-bold text-slate-900 mb-4 sm:mb-8">By Channel</h2>
          <ChannelPieChart data={stats.charts.by_channel} />
        </div>
        <div className="bg-white p-4 sm:p-6 lg:p-8 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-all text-center">
          <h2 className="text-base sm:text-xl font-bold text-slate-900 mb-4 sm:mb-8">By Status</h2>
          <StatusBarChart data={stats.charts.by_status} />
        </div>
        <div className="bg-white p-4 sm:p-6 lg:p-8 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-all text-center">
          <h2 className="text-base sm:text-xl font-bold text-slate-900 mb-4 sm:mb-8">By Priority</h2>
          <PriorityChart data={stats.charts.by_priority} />
        </div>
      </div>
    </div>
  );
}
