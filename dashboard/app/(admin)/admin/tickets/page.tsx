'use client';

import { useEffect, useState } from 'react';
import { Search, Filter, ArrowUpDown, ChevronLeft, ChevronRight, X, AlertCircle } from 'lucide-react';
import StatusBadge from '@/components/StatusBadge';
import ChannelIcon from '@/components/ChannelIcon';
import { api } from '@/lib/api';
import ReactDOM from 'react-dom';

type FilterState = {
  status: string[];
  priority: string[];
  channel: string[];
};

type TicketDetails = {
  ticket: any;
  messages: any[];
};

export default function TicketsPage() {
  const [tickets, setTickets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showFilter, setShowFilter] = useState(false);
  const [filters, setFilters] = useState<FilterState>({
    status: [],
    priority: [],
    channel: []
  });
  const [selectedTicketId, setSelectedTicketId] = useState<string | null>(null);
  const [ticketDetails, setTicketDetails] = useState<TicketDetails | null>(null);
  const [detailsLoading, setDetailsLoading] = useState(false);

  useEffect(() => {
    async function loadTickets() {
      try {
        const data = await api.getTickets();
        setTickets(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadTickets();
  }, []);

  const toggleFilter = (type: keyof FilterState, value: string) => {
    setFilters(prev => ({
      ...prev,
      [type]: prev[type].includes(value)
        ? prev[type].filter(v => v !== value)
        : [...prev[type], value]
    }));
  };

  const clearFilters = () => {
    setFilters({ status: [], priority: [], channel: [] });
  };

  const hasActiveFilters = filters.status.length > 0 || filters.priority.length > 0 || filters.channel.length > 0;

  const filteredTickets = tickets.filter(ticket => {
    const matchesSearch = 
      ticket.customer_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      ticket.customer_email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      ticket.id.includes(searchTerm);
    
    const matchesStatus = filters.status.length === 0 || filters.status.includes(ticket.status);
    const matchesPriority = filters.priority.length === 0 || filters.priority.includes(ticket.priority);
    const matchesChannel = filters.channel.length === 0 || filters.channel.includes(ticket.source_channel);
    
    return matchesSearch && matchesStatus && matchesPriority && matchesChannel;
  });

  const exportToCSV = () => {
    const headers = ['ID', 'Customer Name', 'Customer Email', 'Channel', 'Status', 'Priority', 'Created At'];
    const csvData = filteredTickets.map(ticket => [
      ticket.id,
      ticket.customer_name || 'Anonymous',
      ticket.customer_email || '',
      ticket.source_channel,
      ticket.status,
      ticket.priority,
      new Date(ticket.created_at).toLocaleString()
    ]);

    const csvContent = [
      headers.join(','),
      ...csvData.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `tickets-export-${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
  };

  const handleViewDetails = async (ticketId: string) => {
    console.log('Opening ticket details for:', ticketId);
    setSelectedTicketId(ticketId);
    setDetailsLoading(true);
    try {
      const data = await api.getTicketDetails(ticketId);
      console.log('Ticket details loaded:', data);
      setTicketDetails(data);
    } catch (err) {
      console.error('Failed to load ticket details:', err);
    } finally {
      setDetailsLoading(false);
    }
  };

  const closeDetailsModal = () => {
    setSelectedTicketId(null);
    setTicketDetails(null);
  };

  const activeFilterCount = filters.status.length + filters.priority.length + filters.channel.length;

  return (
    <div className="space-y-6 sm:space-y-8 lg:space-y-10 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 sm:gap-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">Tickets</h1>
          <p className="text-base sm:text-lg text-slate-500 mt-1">Manage and track all customer requests</p>
        </div>
        <div className="flex flex-wrap gap-3 w-full sm:w-auto">
          <button 
            onClick={() => setShowFilter(!showFilter)}
            className={`flex-1 sm:flex-none px-4 sm:px-6 py-3 border-2 rounded-xl text-sm sm:text-base font-bold flex items-center justify-center shadow-sm transition-all ${
              hasActiveFilters 
                ? 'bg-blue-600 border-blue-600 text-white hover:bg-blue-700' 
                : 'bg-white border-slate-100 text-slate-700 hover:bg-slate-50 hover:border-slate-200'
            }`}
          >
            <Filter size={18} className="sm:mr-2" /> 
            <span className="hidden sm:inline">Filter</span>
            {activeFilterCount > 0 && (
              <span className="ml-2 bg-white text-blue-600 px-2 py-0.5 rounded-full text-xs font-bold">
                {activeFilterCount}
              </span>
            )}
          </button>
          <button 
            onClick={exportToCSV}
            className="flex-1 sm:flex-none px-4 sm:px-6 py-3 bg-blue-600 text-white rounded-xl text-sm sm:text-base font-bold hover:bg-blue-700 shadow-xl shadow-blue-100 transition-all"
          >
            Export CSV
          </button>
        </div>
      </div>

      {/* Filter Panel */}
      {showFilter && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 sm:p-6 animate-fade-in">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-bold text-slate-900">Filter Tickets</h3>
            <button
              onClick={clearFilters}
              className="text-sm text-blue-600 font-bold hover:text-blue-700 flex items-center gap-1"
            >
              <X size={16} /> Clear All
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <label className="text-sm font-bold text-slate-700 mb-3 block">Status</label>
              <div className="space-y-2">
                {['open', 'resolved', 'escalated'].map(status => (
                  <button
                    key={status}
                    onClick={() => toggleFilter('status', status)}
                    className={`w-full text-left px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                      filters.status.includes(status)
                        ? 'bg-blue-600 text-white'
                        : 'bg-slate-50 text-slate-700 hover:bg-slate-100'
                    }`}
                  >
                    {status.charAt(0).toUpperCase() + status.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="text-sm font-bold text-slate-700 mb-3 block">Priority</label>
              <div className="space-y-2">
                {['low', 'medium', 'high'].map(priority => (
                  <button
                    key={priority}
                    onClick={() => toggleFilter('priority', priority)}
                    className={`w-full text-left px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                      filters.priority.includes(priority)
                        ? 'bg-blue-600 text-white'
                        : 'bg-slate-50 text-slate-700 hover:bg-slate-100'
                    }`}
                  >
                    {priority.charAt(0).toUpperCase() + priority.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="text-sm font-bold text-slate-700 mb-3 block">Channel</label>
              <div className="space-y-2">
                {['web_form', 'email', 'whatsapp'].map(channel => (
                  <button
                    key={channel}
                    onClick={() => toggleFilter('channel', channel)}
                    className={`w-full text-left px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                      filters.channel.includes(channel)
                        ? 'bg-blue-600 text-white'
                        : 'bg-slate-50 text-slate-700 hover:bg-slate-100'
                    }`}
                  >
                    {channel.replace('_', ' ').split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 sm:p-6 border-b border-slate-100 bg-slate-50/50">
          <div className="relative group">
            <Search className="absolute left-3 sm:left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-600 transition-colors" size={20} />
            <input
              type="text"
              placeholder="Search by ID, customer name or email..."
              className="w-full pl-10 sm:pl-12 pr-4 sm:pr-6 py-3 sm:py-4 border-2 border-slate-100 rounded-2xl bg-white focus:outline-none focus:ring-4 focus:ring-blue-100 focus:border-blue-500 transition-all text-sm sm:text-base md:text-lg"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-slate-50/50 text-slate-500 text-xs sm:text-sm uppercase tracking-widest font-bold">
                <th className="px-3 sm:px-4 lg:px-8 py-3 sm:py-4 lg:py-5 whitespace-nowrap">ID</th>
                <th className="px-3 sm:px-4 lg:px-8 py-3 sm:py-4 lg:py-5 whitespace-nowrap">Customer</th>
                <th className="px-3 sm:px-4 lg:px-8 py-3 sm:py-4 lg:py-5 whitespace-nowrap">Channel</th>
                <th className="px-3 sm:px-4 lg:px-8 py-3 sm:py-4 lg:py-5 whitespace-nowrap">Status</th>
                <th className="px-3 sm:px-4 lg:px-8 py-3 sm:py-4 lg:py-5 whitespace-nowrap">Priority</th>
                <th className="px-3 sm:px-4 lg:px-8 py-3 sm:py-4 lg:py-5 whitespace-nowrap">Date</th>
                <th className="px-3 sm:px-4 lg:px-8 py-3 sm:py-4 lg:py-5 whitespace-nowrap text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                Array(5).fill(0).map((_, i) => (
                  <tr key={i} className="animate-pulse">
                    <td className="px-3 sm:px-4 lg:px-8 py-4 sm:py-6"><div className="h-4 sm:h-5 bg-slate-100 rounded w-12 sm:w-16"></div></td>
                    <td className="px-3 sm:px-4 lg:px-8 py-4 sm:py-6"><div className="h-4 sm:h-5 bg-slate-100 rounded w-24 sm:w-32"></div></td>
                    <td className="px-3 sm:px-4 lg:px-8 py-4 sm:py-6"><div className="h-4 sm:h-5 bg-slate-100 rounded w-6 sm:w-8"></div></td>
                    <td className="px-3 sm:px-4 lg:px-8 py-4 sm:py-6"><div className="h-6 sm:h-7 bg-slate-100 rounded-full w-16 sm:w-20"></div></td>
                    <td className="px-3 sm:px-4 lg:px-8 py-4 sm:py-6"><div className="h-4 sm:h-5 bg-slate-100 rounded w-12 sm:w-16"></div></td>
                    <td className="px-3 sm:px-4 lg:px-8 py-4 sm:py-6"><div className="h-4 sm:h-5 bg-slate-100 rounded w-16 sm:w-24"></div></td>
                    <td className="px-3 sm:px-4 lg:px-8 py-4 sm:py-6"><div className="h-4 sm:h-5 bg-slate-100 rounded w-8 sm:w-12 ml-auto"></div></td>
                  </tr>
                ))
              ) : filteredTickets.length > 0 ? (
                filteredTickets.map((ticket) => (
                  <tr key={ticket.id} className="hover:bg-slate-50/80 transition-all group">
                    <td className="px-3 sm:px-4 lg:px-8 py-4 sm:py-6 text-xs sm:text-base font-mono text-slate-400 whitespace-nowrap">
                      {ticket.id.substring(0, 8)}...
                    </td>
                    <td className="px-3 sm:px-4 lg:px-8 py-4 sm:py-6">
                      <div className="text-xs sm:text-base font-bold text-slate-900">{ticket.customer_name || 'Anonymous'}</div>
                      <div className="text-xs sm:text-sm text-slate-500 mt-0.5">{ticket.customer_email || 'No email'}</div>
                    </td>
                    <td className="px-3 sm:px-4 lg:px-8 py-4 sm:py-6">
                      <div className="scale-110 origin-left">
                        <ChannelIcon channel={ticket.source_channel} />
                      </div>
                    </td>
                    <td className="px-3 sm:px-4 lg:px-8 py-4 sm:py-6">
                      <StatusBadge status={ticket.status} />
                    </td>
                    <td className="px-3 sm:px-4 lg:px-8 py-4 sm:py-6">
                      <span className={`text-xs sm:text-sm font-extrabold uppercase tracking-wider ${
                        ticket.priority === 'high' ? 'text-red-600' :
                        ticket.priority === 'medium' ? 'text-amber-600' : 'text-green-600'
                      }`}>
                        {ticket.priority}
                      </span>
                    </td>
                    <td className="px-3 sm:px-4 lg:px-8 py-4 sm:py-6 text-xs sm:text-base text-slate-500 whitespace-nowrap">
                      {new Date(ticket.created_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                    </td>
                    <td className="px-3 sm:px-4 lg:px-8 py-4 sm:py-6 text-right">
                      <button
                        onClick={() => handleViewDetails(ticket.id)}
                        className="px-3 sm:px-4 py-2 bg-slate-100 text-blue-600 rounded-lg text-xs sm:text-sm font-bold hover:bg-blue-600 hover:text-white transition-all "
                      >
                        View Details
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="px-3 sm:px-4 lg:px-8 py-12 sm:py-20 text-center text-slate-500">
                    <div className="text-sm sm:text-lg font-medium">No tickets found matching your search.</div>
                    <p className="mt-1 text-xs sm:text-sm">Try a different search term or filter.</p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div className="p-4 sm:p-6 border-t border-slate-100 bg-slate-50/30 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div className="text-xs sm:text-base text-slate-500">
            Showing <span className="font-bold text-slate-900">{filteredTickets.length}</span> of <span className="font-bold text-slate-900">{tickets.length}</span> tickets
          </div>
          <div className="flex space-x-2 sm:space-x-3">
            <button className="p-2 sm:p-2.5 border-2 border-slate-100 rounded-xl bg-white text-slate-400 hover:bg-slate-50 hover:border-slate-200 disabled:opacity-30 transition-all" disabled>
              <ChevronLeft size={18} className="sm:w-5 sm:h-5" />
            </button>
            <button className="p-2 sm:p-2.5 border-2 border-slate-100 rounded-xl bg-white text-slate-400 hover:bg-slate-50 hover:border-slate-200 disabled:opacity-30 transition-all" disabled>
              <ChevronRight size={18} className="sm:w-5 sm:h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Ticket Details Modal - Rendered via Portal */}
      {selectedTicketId && ReactDOM.createPortal(
        <div 
          className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
          onClick={closeDetailsModal}
        >
          <div 
            className="bg-white rounded-3xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between p-6 border-b border-slate-200 bg-slate-50 flex-shrink-0">
              <div>
                <h2 className="text-2xl font-extrabold text-slate-900">Ticket Details</h2>
                {ticketDetails?.ticket && (
                  <p className="text-sm text-slate-500 mt-1 font-mono">{ticketDetails.ticket.id.substring(0, 8)}...</p>
                )}
              </div>
              <button
                onClick={closeDetailsModal}
                className="p-2 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-all"
                aria-label="Close modal"
              >
                <X size={24} />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6 bg-slate-50">
              {detailsLoading ? (
                <div className="flex flex-col items-center justify-center py-20">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
                  <p className="text-slate-500 font-medium">Loading ticket details...</p>
                </div>
              ) : ticketDetails?.ticket ? (
                <div className="space-y-6">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-blue-50 p-4 rounded-xl border border-blue-100">
                      <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Status</p>
                      <p className="text-lg font-bold text-slate-900 mt-1 capitalize">{ticketDetails.ticket.status}</p>
                    </div>
                    <div className="bg-purple-50 p-4 rounded-xl border border-purple-100">
                      <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Priority</p>
                      <p className="text-lg font-bold text-slate-900 mt-1 capitalize">{ticketDetails.ticket.priority}</p>
                    </div>
                    <div className="bg-green-50 p-4 rounded-xl border border-green-100">
                      <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Channel</p>
                      <p className="text-lg font-bold text-slate-900 mt-1 capitalize">{ticketDetails.ticket.source_channel?.replace('_', ' ')}</p>
                    </div>
                    <div className="bg-amber-50 p-4 rounded-xl border border-amber-100">
                      <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Created</p>
                      <p className="text-sm font-bold text-slate-900 mt-1">{new Date(ticketDetails.ticket.created_at).toLocaleDateString()}</p>
                    </div>
                  </div>

                  <div className="bg-white border-2 border-slate-100 rounded-2xl p-6">
                    <h3 className="text-lg font-bold text-slate-900 mb-4">Customer Information</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Name</p>
                        <p className="text-base font-bold text-slate-900 mt-1">{ticketDetails.ticket.customer_name || 'Anonymous'}</p>
                      </div>
                      <div>
                        <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Email</p>
                        <p className="text-base font-bold text-slate-900 mt-1">{ticketDetails.ticket.customer_email || 'N/A'}</p>
                      </div>
                      {ticketDetails.ticket.customer_phone && (
                        <div>
                          <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Phone</p>
                          <p className="text-base font-bold text-slate-900 mt-1">{ticketDetails.ticket.customer_phone}</p>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="bg-white border-2 border-slate-100 rounded-2xl p-6">
                    <h3 className="text-lg font-bold text-slate-900 mb-4">Conversation History</h3>
                    {ticketDetails.messages && ticketDetails.messages.length > 0 ? (
                      <div className="space-y-4">
                        {ticketDetails.messages.map((msg, i) => {
                          const isAgent = msg.role === 'agent' || msg.role === 'system';
                          return (
                            <div key={i} className={`flex ${isAgent ? 'justify-end' : 'justify-start'}`}>
                              <div className={`max-w-[80%] rounded-2xl p-4 ${
                                isAgent 
                                  ? 'bg-blue-600 text-white rounded-tr-none' 
                                  : 'bg-slate-50 text-slate-700 border border-slate-100 rounded-tl-none'
                              }`}>
                                <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                                <p className={`text-xs mt-2 font-bold ${isAgent ? 'text-blue-100' : 'text-slate-400'}`}>
                                  {new Date(msg.created_at).toLocaleString()}
                                </p>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <p className="text-slate-400 text-center py-8 bg-slate-50 rounded-xl">No messages in this conversation</p>
                    )}
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-20 text-slate-400">
                  <AlertCircle size={48} className="mb-4" />
                  <p className="text-lg font-medium">Failed to load ticket details</p>
                  <button 
                    onClick={() => handleViewDetails(selectedTicketId)}
                    className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg font-bold hover:bg-blue-700"
                  >
                    Retry
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>,
        document.body
      )}
    </div>
  );
}
