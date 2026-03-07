'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import StatusBadge from '@/components/StatusBadge';
import SentimentBar from '@/components/SentimentBar';
import ChannelIcon from '@/components/ChannelIcon';
import { MessageCircle, Send, User } from 'lucide-react';

export default function ConversationsPage() {
  const [conversations, setConversations] = useState<any[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [msgLoading, setMsgLoading] = useState(false);

  useEffect(() => {
    async function loadConversations() {
      try {
        const data = await api.getConversations();
        setConversations(data);
        if (data.length > 0) {
          handleSelect(data[0].id);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadConversations();
  }, []);

  const handleSelect = async (id: string) => {
    setSelectedId(id);
    setMsgLoading(true);
    try {
      const data = await api.getMessages(id);
      setMessages(data);
    } catch (err) {
      console.error(err);
    } finally {
      setMsgLoading(false);
    }
  };

  const selectedConversation = conversations.find(c => c.id === selectedId);

  return (
    <div className="flex flex-col lg:flex-row h-auto lg:h-[calc(100vh-8rem)] gap-4 lg:gap-8 animate-fade-in min-h-screen lg:min-h-0">
      {/* Sidebar List */}
      <div className="w-full lg:w-1/3 lg:flex-1 bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col overflow-hidden">
        <div className="p-4 sm:p-6 border-b border-slate-100 bg-slate-50/50 flex-shrink-0">
          <h2 className="text-lg sm:text-xl font-bold text-slate-900">Conversations</h2>
        </div>
        <div className="flex-1 overflow-y-auto" style={{ minHeight: '200px', maxHeight: '40vh' }}>
          {loading ? (
            <div className="p-12 text-center text-slate-400">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
              Loading...
            </div>
          ) : conversations.length > 0 ? (
            <div className="divide-y divide-slate-100">
              {conversations.map((conv) => (
                <div
                  key={conv.id}
                  onClick={() => handleSelect(conv.id)}
                  className={`p-4 sm:p-6 cursor-pointer transition-all ${
                    selectedId === conv.id ? 'bg-blue-50/50 border-l-4 border-l-blue-600 shadow-inner' : 'hover:bg-slate-50 border-l-4 border-l-transparent'
                  }`}
                >
                  <div className="flex justify-between items-start mb-3">
                    <span className="text-sm sm:text-base font-bold text-slate-900 truncate pr-2">
                      {conv.customer_name || 'Anonymous'}
                    </span>
                    <span className="text-xs font-medium text-slate-400 whitespace-nowrap">
                      {new Date(conv.started_at).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="flex items-center justify-between gap-2 sm:gap-4">
                    <div className="flex items-center gap-2 sm:gap-2.5">
                      <div className="scale-110">
                        <ChannelIcon channel={conv.initial_channel} size={16} />
                      </div>
                      <StatusBadge status={conv.status} />
                    </div>
                    <div className="flex-1 max-w-[100px]">
                      <SentimentBar score={conv.sentiment_score || 0.5} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-12 text-center text-slate-400 text-sm sm:text-lg">No conversations found.</div>
          )}
        </div>
      </div>

      {/* Message Thread */}
      <div className="w-full lg:w-2/3 lg:flex-1 bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col overflow-hidden"
        style={{ minHeight: '500px', maxHeight: 'calc(100vh - 200px)' }}
      >
        {selectedConversation ? (
          <>
            <div className="p-4 sm:p-6 border-b border-slate-100 bg-slate-50/50 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
              <div className="flex items-center gap-3 sm:gap-4">
                <div className="h-12 w-12 sm:h-14 sm:w-14 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold text-lg sm:text-xl shadow-inner flex-shrink-0">
                  {selectedConversation.customer_name?.charAt(0).toUpperCase() || '?'}
                </div>
                <div className="min-w-0">
                  <h2 className="text-base sm:text-xl font-bold text-slate-900 truncate">{selectedConversation.customer_name || 'Anonymous'}</h2>
                  <p className="text-xs sm:text-sm font-medium text-slate-500 truncate">{selectedConversation.customer_email}</p>
                </div>
              </div>
              <div className="flex items-center gap-4 sm:gap-6 w-full sm:w-auto">
                 <div className="text-right flex-shrink-0">
                    <div className="text-[10px] sm:text-xs uppercase font-extrabold text-slate-400 mb-2 tracking-widest">Sentiment</div>
                    <div className="w-24 sm:w-32">
                      <SentimentBar score={selectedConversation.sentiment_score || 0.5} />
                    </div>
                 </div>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto    p-4 sm:p-6 lg:p-8 space-y-4 sm:space-y-6 lg:space-y-8 bg-slate-50/20">
              {msgLoading ? (
                <div className="flex justify-center p-12">
                  <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600"></div>
                </div>
              ) : messages.length > 0 ? (
                messages.map((msg, i) => {
                  const isAgent = msg.role === 'agent' || msg.role === 'system';
                  return (
                    <div key={i} className={`flex ${isAgent ? 'justify-end ' : 'justify-start'}  animate-fade-in`}>
                      <div className={`flex max-w-[85%]  sm:max-w-[75%] ${isAgent ? 'flex-row-reverse' : 'flex-row'}`}>
                        <div className={`flex-shrink-0  h-8 w-8 sm:h-10 sm:w-10 rounded-full flex items-center justify-center shadow-sm ${
                          isAgent ? 'bg-blue-600 ml-2 sm:ml-4' : 'bg-white border border-slate-200 mr-2 sm:mr-4'
                        }`}>
                          {isAgent ? <Send size={16} className="text-white" /> : <User size={16} className="text-slate-500" />}
                        </div>
                        <div className={`p-3 sm:p-5 rounded-[1.5rem] shadow-sm text-sm sm:text-base leading-relaxed ${
                          isAgent
                            ? 'bg-blue-600 text-white rounded-tr-none'
                            : 'bg-white text-slate-700 border border-slate-100 rounded-tl-none shadow-md shadow-slate-100'
                        }`}>
                          <div className="whitespace-pre-wrap">{msg.content}</div>
                          <div className={`text-[10px] sm:text-xs mt-2 font-bold uppercase tracking-wider ${isAgent ? 'text-blue-100' : 'text-slate-400'}`}>
                            {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            {msg.delivery_status === 'sent' && isAgent && ' • Sent'}
                          </div>
                        </div>
                      </div>
                    </div>
                  )
                })
              ) : (
                <div className="p-12 text-center text-slate-400 text-sm sm:text-lg italic bg-white/50 rounded-3xl border-2 border-dashed border-slate-100">
                  No messages in this thread.
                </div>
              )}
            </div>

            <div className="p-4 sm:p-6 border-t border-slate-100 bg-white">
              <div className="relative">
                <textarea
                  disabled
                  placeholder="AI Agent is handling this conversation in real-time..."
                  className="w-full p-4 sm:p-5 border-2 border-slate-100 rounded-2xl bg-slate-50 text-slate-400 text-sm sm:text-base font-medium resize-none h-20 sm:h-24 focus:outline-none cursor-not-allowed shadow-inner"
                />
                <div className="absolute right-3 sm:right-5 bottom-3 sm:bottom-5 text-[10px] sm:text-xs font-extrabold text-slate-300 uppercase tracking-widest">Read Only Mode</div>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-slate-300 p-8 sm:p-12">
            <div className="p-6 sm:p-8 bg-slate-50 rounded-full mb-4 sm:mb-6">
              <MessageCircle size={60} className="sm:w-20 sm:h-20 opacity-20" />
            </div>
            <p className="text-base sm:text-xl font-bold text-center">Select a conversation to view the thread</p>
            <p className="text-slate-400 mt-2 text-sm sm:text-base text-center">All interactions are logged in real-time.</p>
          </div>
        )}
      </div>
    </div>
  );
}
