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
  AreaChart,
  Area
} from 'recharts';

export default function AnalyticsPage() {
  const [stats, setStats] = useState<any>(null);
  const [sentimentReport, setSentimentReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadStats() {
      try {
        const [data, sentiment] = await Promise.all([
          api.getDashboardStats(),
          api.getSentimentReport(7).catch(() => null),
        ]);
        setStats(data);
        setSentimentReport(sentiment);
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

  // Prepare sentiment trend data from real API
  const sentimentTrendData = sentimentReport?.daily_trends
    ? sentimentReport.daily_trends
        .slice()
        .reverse()
        .map((d: any) => ({
          date: new Date(d.date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' }),
          sentiment: parseFloat(d.avg_sentiment) || 0,
          conversations: d.conversation_count || 0,
          angry: d.angry_count || 0,
          satisfied: d.satisfied_count || 0,
        }))
    : [];

  const summaryStats = sentimentReport?.summary || {};

  return (
    <div className="space-y-6 sm:space-y-8 lg:space-y-10 animate-fade-in">
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">Analytics & Insights</h1>
        <p className="text-base sm:text-lg text-slate-500 mt-1">Deep dive into agent performance and ticket trends</p>
      </div>

      {/* Sentiment Summary KPIs */}
      {sentimentReport && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 sm:gap-6">
          <div className="bg-white p-4 sm:p-6 rounded-2xl border border-slate-200 shadow-sm text-center">
            <p className="text-sm text-slate-500 font-semibold">Avg Sentiment</p>
            <p className="text-2xl sm:text-3xl font-extrabold text-blue-600 mt-1">
              {summaryStats.overall_avg ? (summaryStats.overall_avg * 100).toFixed(0) : 0}%
            </p>
          </div>
          <div className="bg-white p-4 sm:p-6 rounded-2xl border border-slate-200 shadow-sm text-center">
            <p className="text-sm text-slate-500 font-semibold">Total Conversations</p>
            <p className="text-2xl sm:text-3xl font-extrabold text-slate-900 mt-1">
              {summaryStats.total_conversations || 0}
            </p>
          </div>
          <div className="bg-white p-4 sm:p-6 rounded-2xl border border-slate-200 shadow-sm text-center">
            <p className="text-sm text-slate-500 font-semibold">Angry Customers</p>
            <p className="text-2xl sm:text-3xl font-extrabold text-red-500 mt-1">
              {summaryStats.total_angry || 0}
            </p>
          </div>
          <div className="bg-white p-4 sm:p-6 rounded-2xl border border-slate-200 shadow-sm text-center">
            <p className="text-sm text-slate-500 font-semibold">Escalation Rate</p>
            <p className="text-2xl sm:text-3xl font-extrabold text-amber-500 mt-1">
              {summaryStats.escalation_rate_pct || 0}%
            </p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 sm:gap-8 lg:gap-10">
        <div className="bg-white p-4 sm:p-6 lg:p-8 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-all">
          <h2 className="text-lg sm:text-xl font-bold text-slate-900 mb-4 sm:mb-8">Daily Sentiment Trend (7 Days)</h2>
          <div className="h-[280px] sm:h-[350px]">
            {sentimentTrendData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={sentimentTrendData}>
                  <defs>
                    <linearGradient id="colorSentiment" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.15}/>
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 11, fontWeight: 600}} dy={10} />
                  <YAxis domain={[0, 1]} axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 12, fontWeight: 600}} dx={-10} />
                  <Tooltip
                    contentStyle={{borderRadius: '16px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)'}}
                    formatter={(value) => [(((value as number) ?? 0) * 100).toFixed(0) + '%', 'Sentiment']}
                  />
                  <Area type="monotone" dataKey="sentiment" stroke="#10b981" fillOpacity={1} fill="url(#colorSentiment)" strokeWidth={3} />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-slate-400">
                No sentiment data available yet
              </div>
            )}
          </div>
        </div>

        <div className="bg-white p-4 sm:p-6 lg:p-8 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-all">
          <h2 className="text-lg sm:text-xl font-bold text-slate-900 mb-4 sm:mb-8">Daily Conversation Volume</h2>
          <div className="h-[280px] sm:h-[350px]">
            {sentimentTrendData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={sentimentTrendData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 11, fontWeight: 600}} dy={10} />
                  <YAxis axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 12, fontWeight: 600}} dx={-10} />
                  <Tooltip
                    contentStyle={{borderRadius: '16px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)'}}
                    cursor={{fill: '#f1f5f9'}}
                  />
                  <Bar dataKey="satisfied" name="Satisfied" fill="#10b981" radius={[6, 6, 0, 0]} stackId="stack" />
                  <Bar dataKey="angry" name="Angry" fill="#ef4444" radius={[6, 6, 0, 0]} stackId="stack" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-slate-400">
                No volume data available yet
              </div>
            )}

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
