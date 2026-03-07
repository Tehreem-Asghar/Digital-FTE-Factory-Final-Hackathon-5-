'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Search, Mail, Phone, Calendar, Ticket, User, X, ExternalLink, MessageSquare } from 'lucide-react';
import ReactDOM from 'react-dom';
import StatusBadge from '@/components/StatusBadge';
import ChannelIcon from '@/components/ChannelIcon';

type CustomerDetails = {
  customer: any;
  tickets: any[];
  conversations: any[];
};

export default function CustomersPage() {
  const [customers, setCustomers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCustomer, setSelectedCustomer] = useState<string | null>(null);
  const [customerDetails, setCustomerDetails] = useState<CustomerDetails | null>(null);
  const [detailsLoading, setDetailsLoading] = useState(false);

  useEffect(() => {
    async function loadCustomers() {
      try {
        const data = await api.getCustomers();
        setCustomers(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadCustomers();
  }, []);

  const filteredCustomers = customers.filter(c =>
    c.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.email?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleViewProfile = async (customerId: string) => {
    setSelectedCustomer(customerId);
    setDetailsLoading(true);
    try {
      const data = await api.getCustomerDetails(customerId);
      setCustomerDetails(data);
    } catch (err) {
      console.error('Failed to load customer details:', err);
    } finally {
      setDetailsLoading(false);
    }
  };

  const closeDetailsModal = () => {
    setSelectedCustomer(null);
    setCustomerDetails(null);
  };

  return (
    <div className="space-y-6 sm:space-y-8 lg:space-y-10 animate-fade-in">
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">Customers</h1>
        <p className="text-base sm:text-lg text-slate-500 mt-1">View and manage your unified customer database</p>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 sm:p-6 border-b border-slate-100 bg-slate-50/50">
          <div className="relative group">
            <Search className="absolute left-3 sm:left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-600 transition-colors" size={20} />
            <input
              type="text"
              placeholder="Search by name or email..."
              className="w-full pl-10 sm:pl-12 pr-4 sm:pr-6 py-3 sm:py-4 border-2 border-slate-100 rounded-2xl bg-white focus:outline-none focus:ring-4 focus:ring-blue-100 focus:border-blue-500 transition-all text-sm sm:text-base md:text-lg"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 lg:gap-8 p-4 sm:p-6 lg:p-8">
          {loading ? (
            Array(6).fill(0).map((_, i) => (
              <div key={i} className="animate-pulse bg-slate-50 rounded-2xl p-6 sm:p-8 h-56 sm:h-64 border border-slate-100"></div>
            ))
          ) : filteredCustomers.length > 0 ? (
            filteredCustomers.map((customer) => (
              <div key={customer.id} className="bg-white rounded-3xl border border-slate-100 shadow-sm hover:shadow-xl hover:border-blue-100 transition-all p-4 sm:p-6 lg:p-8 flex flex-col justify-between group relative overflow-hidden">
                <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                  <User size={120} />
                </div>

                <div className="relative z-10">
                  <div className="flex justify-between items-start mb-4 sm:mb-6">
                    <div className="h-12 w-12 sm:h-16 sm:w-16 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-extrabold text-xl sm:text-2xl shadow-lg shadow-blue-100 flex-shrink-0">
                      {customer.name?.charAt(0).toUpperCase() || '?'}
                    </div>
                    <div className="flex items-center text-xs font-extrabold text-blue-600 bg-blue-50 px-2 sm:px-3 py-1.5 rounded-lg border border-blue-100 tracking-wider whitespace-nowrap">
                      <Ticket size={12} className="sm:mr-1.5" /> <span className="hidden sm:inline">{customer.ticket_count} TICKETS</span><span className="sm:hidden">{customer.ticket_count}</span>
                    </div>
                  </div>

                  <h3 className="text-base sm:text-xl font-bold text-slate-900 mb-2 group-hover:text-blue-600 transition-colors truncate">
                    {customer.name || 'Anonymous'}
                  </h3>

                  <div className="space-y-2 sm:space-y-3 mt-4 sm:mt-6">
                    <div className="flex items-center text-xs sm:text-base text-slate-600 font-medium truncate">
                      <Mail size={14} className="sm:mr-3 text-slate-400 flex-shrink-0" /> <span className="truncate">{customer.email}</span>
                    </div>
                    {customer.phone && (
                      <div className="flex items-center text-xs sm:text-base text-slate-600 font-medium truncate">
                        <Phone size={14} className="sm:mr-3 text-slate-400 flex-shrink-0" /> {customer.phone}
                      </div>
                    )}
                    <div className="flex items-center text-[10px] sm:text-sm text-slate-400 font-bold uppercase tracking-wide mt-3 sm:mt-4">
                      <Calendar size={14} className="sm:mr-3 flex-shrink-0" /> <span className="hidden sm:inline">Joined</span> {new Date(customer.created_at).toLocaleDateString()}
                    </div>
                  </div>
                </div>

                <button 
                  onClick={() => handleViewProfile(customer.id)}
                  className="mt-4 sm:mt-8 w-full py-3 sm:py-3.5 bg-slate-50 text-slate-600 rounded-xl text-sm sm:text-base font-bold hover:bg-blue-600 hover:text-white hover:shadow-lg hover:shadow-blue-100 transition-all relative z-10 border border-slate-100"
                >
                  View Full Profile
                </button>
              </div>
            ))
          ) : (
            <div className="col-span-full py-12 sm:py-20 text-center text-slate-400 px-4">
              <div className="text-base sm:text-xl font-medium">No customers found.</div>
              <p className="mt-1 text-sm">Try a different search term.</p>
            </div>
          )}
        </div>
      </div>

      {/* Customer Details Modal */}
      {selectedCustomer && ReactDOM.createPortal(
        <div 
          className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
          onClick={closeDetailsModal}
        >
          <div 
            className="bg-white rounded-3xl shadow-2xl w-full max-w-5xl max-h-[90vh] overflow-hidden flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between p-6 border-b border-slate-200 bg-slate-50 flex-shrink-0">
              <div>
                <h2 className="text-2xl font-extrabold text-slate-900">Customer Profile</h2>
                {customerDetails?.customer && (
                  <p className="text-sm text-slate-500 mt-1">{customerDetails.customer.name || 'Anonymous'}</p>
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
                  <p className="text-slate-500 font-medium">Loading customer details...</p>
                </div>
              ) : customerDetails?.customer ? (
                <div className="space-y-8">
                  {/* Customer Info Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="bg-white p-6 rounded-2xl border-2 border-slate-100">
                      <div className="flex items-center gap-4 mb-4">
                        <div className="h-16 w-16 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-extrabold text-2xl">
                          {customerDetails.customer.name?.charAt(0).toUpperCase() || '?'}
                        </div>
                        <div>
                          <h3 className="text-xl font-bold text-slate-900">{customerDetails.customer.name || 'Anonymous'}</h3>
                          <p className="text-sm text-slate-500">Customer since {new Date(customerDetails.customer.created_at).toLocaleDateString()}</p>
                        </div>
                      </div>
                    </div>

                    <div className="bg-white p-6 rounded-2xl border-2 border-slate-100">
                      <div className="flex items-center gap-3 mb-3">
                        <div className="h-10 w-10 rounded-xl bg-blue-50 flex items-center justify-center text-blue-600">
                          <Mail size={20} />
                        </div>
                        <div>
                          <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Email</p>
                          <p className="text-base font-bold text-slate-900">{customerDetails.customer.email || 'N/A'}</p>
                        </div>
                      </div>
                      {customerDetails.customer.phone && (
                        <div className="flex items-center gap-3 mt-4">
                          <div className="h-10 w-10 rounded-xl bg-green-50 flex items-center justify-center text-green-600">
                            <Phone size={20} />
                          </div>
                          <div>
                            <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Phone</p>
                            <p className="text-base font-bold text-slate-900">{customerDetails.customer.phone}</p>
                          </div>
                        </div>
                      )}
                    </div>

                    <div className="bg-white p-6 rounded-2xl border-2 border-slate-100">
                      <div className="flex items-center gap-3 mb-4">
                        <div className="h-10 w-10 rounded-xl bg-purple-50 flex items-center justify-center text-purple-600">
                          <Ticket size={20} />
                        </div>
                        <div>
                          <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Total Tickets</p>
                          <p className="text-2xl font-extrabold text-slate-900">{customerDetails.customer.ticket_count || 0}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-xl bg-amber-50 flex items-center justify-center text-amber-600">
                          <MessageSquare size={20} />
                        </div>
                        <div>
                          <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Conversations</p>
                          <p className="text-2xl font-extrabold text-slate-900">{customerDetails.conversations.length}</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Tickets Section */}
                  <div className="bg-white rounded-2xl border-2 border-slate-100 p-6">
                    <div className="flex items-center justify-between mb-6">
                      <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                        <Ticket size={20} className="text-blue-600" />
                        Recent Tickets
                      </h3>
                      {customerDetails.tickets.length > 0 && (
                        <span className="text-sm font-bold text-slate-500">{customerDetails.tickets.length} tickets</span>
                      )}
                    </div>
                    {customerDetails.tickets.length > 0 ? (
                      <div className="overflow-x-auto">
                        <table className="w-full text-left">
                          <thead>
                            <tr className="bg-slate-50 text-slate-500 text-xs uppercase tracking-widest font-bold">
                              <th className="px-4 py-3 rounded-l-lg">ID</th>
                              <th className="px-4 py-3">Status</th>
                              <th className="px-4 py-3">Priority</th>
                              <th className="px-4 py-3">Channel</th>
                              <th className="px-4 py-3 rounded-r-lg">Created</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-100">
                            {customerDetails.tickets.map((ticket) => (
                              <tr key={ticket.id} className="hover:bg-slate-50 transition-all">
                                <td className="px-4 py-3 text-sm font-mono text-slate-400">{ticket.id.substring(0, 8)}...</td>
                                <td className="px-4 py-3"><StatusBadge status={ticket.status} /></td>
                                <td className="px-4 py-3">
                                  <span className={`text-xs font-extrabold uppercase tracking-wider ${
                                    ticket.priority === 'high' ? 'text-red-600' :
                                    ticket.priority === 'medium' ? 'text-amber-600' : 'text-green-600'
                                  }`}>
                                    {ticket.priority}
                                  </span>
                                </td>
                                <td className="px-4 py-3"><ChannelIcon channel={ticket.source_channel} /></td>
                                <td className="px-4 py-3 text-sm text-slate-500">{new Date(ticket.created_at).toLocaleDateString()}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <p className="text-slate-400 text-center py-8">No tickets found for this customer</p>
                    )}
                  </div>

                  {/* Conversations Section */}
                  <div className="bg-white rounded-2xl border-2 border-slate-100 p-6">
                    <div className="flex items-center justify-between mb-6">
                      <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                        <MessageSquare size={20} className="text-green-600" />
                        Recent Conversations
                      </h3>
                      {customerDetails.conversations.length > 0 && (
                        <span className="text-sm font-bold text-slate-500">{customerDetails.conversations.length} conversations</span>
                      )}
                    </div>
                    {customerDetails.conversations.length > 0 ? (
                      <div className="space-y-3">
                        {customerDetails.conversations.map((conv) => (
                          <div key={conv.id} className="flex items-center justify-between p-4 bg-slate-50 rounded-xl border border-slate-100 hover:border-blue-200 transition-all">
                            <div className="flex items-center gap-3">
                              <ChannelIcon channel={conv.initial_channel} />
                              <div>
                                <p className="text-sm font-bold text-slate-900">Conversation via {conv.initial_channel.replace('_', ' ')}</p>
                                <p className="text-xs text-slate-500">{new Date(conv.started_at).toLocaleString()}</p>
                              </div>
                            </div>
                            <StatusBadge status={conv.status} />
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-slate-400 text-center py-8">No conversations found for this customer</p>
                    )}
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-20 text-slate-400">
                  <p className="text-lg font-medium">Failed to load customer details</p>
                  <button 
                    onClick={() => handleViewProfile(selectedCustomer)}
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
