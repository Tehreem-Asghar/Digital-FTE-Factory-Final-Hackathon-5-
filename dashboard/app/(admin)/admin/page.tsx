'use client';

import { useEffect, useState } from 'react';
import { 
  Ticket, 
  Users, 
  MessageSquare, 
  TrendingUp, 
  AlertCircle, 
  Clock,
  ExternalLink
} from 'lucide-react';
import KPICard from '@/components/KPICard';
import StatusBadge from '@/components/StatusBadge';
import ChannelPieChart from '@/components/charts/ChannelPieChart';
import StatusBarChart from '@/components/charts/StatusBarChart';
import PriorityChart from '@/components/charts/PriorityChart';
import { api } from '@/lib/api';
import Link from 'next/link';

export default function Dashboard() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadStats() {
      try {
        const data = await api.getDashboardStats();
        setStats(data);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    loadStats();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 p-6 rounded-2xl text-red-700 border border-red-200 text-lg">
        Error loading dashboard: {error}
      </div>
    );
  }

  const { kpis, charts, recent_tickets } = stats;

  return (
    <div className="space-y-6 sm:space-y-8 lg:space-y-10 animate-fade-in">
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">System Overview</h1>
        <p className="text-base sm:text-lg text-slate-500 mt-1">Real-time status of your Customer Success AI Agent</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 lg:gap-8">
        <KPICard
          title="Total Tickets"
          value={kpis.total_tickets}
          icon={Ticket}
          description="Total incoming requests"
        />
        <KPICard
          title="Open Tickets"
          value={kpis.open_tickets}
          icon={AlertCircle}
          description="Requiring attention"
          trend={{ value: 12, isUp: true }}
        />
        <KPICard
          title="Escalated"
          value={kpis.escalated_tickets}
          icon={TrendingUp}
          description="Handed to humans"
          trend={{ value: 5, isUp: false }}
        />
        <KPICard
          title="Avg Sentiment"
          value={`${(kpis.avg_sentiment * 100).toFixed(0)}%`}
          icon={MessageSquare}
          description="Customer satisfaction"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6 lg:gap-8">
        <div className="bg-white p-4 sm:p-6 lg:p-8 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-all">
          <h2 className="text-lg sm:text-xl font-bold text-slate-900 mb-4 sm:mb-8">Tickets by Channel</h2>
          <ChannelPieChart data={charts.by_channel} />
        </div>
        <div className="bg-white p-4 sm:p-6 lg:p-8 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-all">
          <h2 className="text-lg sm:text-xl font-bold text-slate-900 mb-4 sm:mb-8">Status Distribution</h2>
          <StatusBarChart data={charts.by_status} />
        </div>
        <div className="bg-white p-4 sm:p-6 lg:p-8 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-all">
          <h2 className="text-lg sm:text-xl font-bold text-slate-900 mb-4 sm:mb-8">Priority Level</h2>
          <PriorityChart data={charts.by_priority} />
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 sm:p-6 lg:p-8 border-b border-slate-100 flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3 bg-slate-50/30">
          <h2 className="text-lg sm:text-xl font-bold text-slate-900">Recent Tickets</h2>
          <Link href="/admin/tickets" className="text-blue-600 text-sm sm:text-base font-bold hover:text-blue-700 transition-colors flex items-center justify-center gap-1">
            View All <ExternalLink size={16} className="sm:w-4 sm:h-4" />
          </Link>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-slate-50/50 text-slate-500 text-xs sm:text-sm uppercase tracking-widest font-bold">
                <th className="px-3 sm:px-4 lg:px-8 py-3 sm:py-4 lg:py-5 whitespace-nowrap">ID</th>
                <th className="px-3 sm:px-4 lg:px-8 py-3 sm:py-4 lg:py-5 whitespace-nowrap">Customer</th>
                <th className="px-3 sm:px-4 lg:px-8 py-3 sm:py-4 lg:py-5 whitespace-nowrap">Status</th>
                <th className="px-3 sm:px-4 lg:px-8 py-3 sm:py-4 lg:py-5 whitespace-nowrap">Priority</th>
                <th className="px-3 sm:px-4 lg:px-8 py-3 sm:py-4 lg:py-5 whitespace-nowrap hidden sm:table-cell">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {recent_tickets.map((ticket: any) => (
                <tr key={ticket.id} className="hover:bg-slate-50/80 transition-all group">
                  <td className="px-3 sm:px-4 lg:px-8 py-3 sm:py-4 lg:py-5 text-xs sm:text-base font-mono text-slate-400 whitespace-nowrap">
                    {ticket.id.substring(0, 8)}...
                  </td>
                  <td className="px-3 sm:px-4 lg:px-8 py-3 sm:py-4 lg:py-5 text-xs sm:text-base font-bold text-slate-700 whitespace-nowrap">
                    {ticket.customer_name || 'Anonymous'}
                  </td>
                  <td className="px-3 sm:px-4 lg:px-8 py-3 sm:py-4 lg:py-5">
                    <StatusBadge status={ticket.status} />
                  </td>
                  <td className="px-3 sm:px-4 lg:px-8 py-3 sm:py-4 lg:py-5">
                    <span className={`text-xs sm:text-sm font-extrabold tracking-wider ${
                      ticket.priority === 'high' ? 'text-red-600' :
                      ticket.priority === 'medium' ? 'text-amber-600' : 'text-green-600'
                    }`}>
                      {ticket.priority.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-3 sm:px-4 lg:px-8 py-3 sm:py-4 lg:py-5 text-xs sm:text-base text-slate-500 whitespace-nowrap hidden sm:table-cell">
                    {new Date(ticket.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
