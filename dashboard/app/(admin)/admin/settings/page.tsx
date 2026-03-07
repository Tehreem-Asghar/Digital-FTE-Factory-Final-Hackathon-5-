'use client';

import { useState } from 'react';
import { Save, Bell, Mail, MessageCircle, Globe, Lock, Database, Users, Zap, AlertCircle } from 'lucide-react';

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<'general' | 'channels' | 'notifications' | 'security'>('general');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaving(true);
    setTimeout(() => {
      setSaving(false);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    }, 1000);
  };

  return (
    <div className="space-y-6 sm:space-y-8 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">Settings</h1>
        <p className="text-base sm:text-lg text-slate-500 mt-1">Configure your SaaSFlow Digital FTE system</p>
      </div>

      {/* Settings Tabs */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="flex border-b border-slate-200 overflow-x-auto">
          <button
            onClick={() => { setActiveTab('general'); setSaved(false); }}
            className={`flex items-center gap-2 px-6 py-4 text-sm font-bold whitespace-nowrap transition-all ${
              activeTab === 'general'
                ? 'bg-blue-50 text-blue-600 border-b-2 border-blue-600'
                : 'text-slate-600 hover:bg-slate-50'
            }`}
          >
            <Globe size={18} /> General
          </button>
          <button
            onClick={() => { setActiveTab('channels'); setSaved(false); }}
            className={`flex items-center gap-2 px-6 py-4 text-sm font-bold whitespace-nowrap transition-all ${
              activeTab === 'channels'
                ? 'bg-blue-50 text-blue-600 border-b-2 border-blue-600'
                : 'text-slate-600 hover:bg-slate-50'
            }`}
          >
            <MessageCircle size={18} /> Channels
          </button>
          <button
            onClick={() => { setActiveTab('notifications'); setSaved(false); }}
            className={`flex items-center gap-2 px-6 py-4 text-sm font-bold whitespace-nowrap transition-all ${
              activeTab === 'notifications'
                ? 'bg-blue-50 text-blue-600 border-b-2 border-blue-600'
                : 'text-slate-600 hover:bg-slate-50'
            }`}
          >
            <Bell size={18} /> Notifications
          </button>
          <button
            onClick={() => { setActiveTab('security'); setSaved(false); }}
            className={`flex items-center gap-2 px-6 py-4 text-sm font-bold whitespace-nowrap transition-all ${
              activeTab === 'security'
                ? 'bg-blue-50 text-blue-600 border-b-2 border-blue-600'
                : 'text-slate-600 hover:bg-slate-50'
            }`}
          >
            <Lock size={18} /> Security
          </button>
        </div>

        {/* Tab Content */}
        <div className="p-6 sm:p-8">
          {activeTab === 'general' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-bold text-slate-900 mb-4">System Configuration</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-bold text-slate-700 mb-2">System Name</label>
                    <input
                      type="text"
                      defaultValue="SaaSFlow Digital FTE"
                      className="w-full px-4 py-3 border-2 border-slate-100 rounded-xl bg-white focus:outline-none focus:ring-4 focus:ring-blue-100 focus:border-blue-500 transition-all"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-bold text-slate-700 mb-2">Admin Email</label>
                    <input
                      type="email"
                      defaultValue="admin@saasflow.com"
                      className="w-full px-4 py-3 border-2 border-slate-100 rounded-xl bg-white focus:outline-none focus:ring-4 focus:ring-blue-100 focus:border-blue-500 transition-all"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-bold text-slate-700 mb-2">Timezone</label>
                    <select className="w-full px-4 py-3 border-2 border-slate-100 rounded-xl bg-white focus:outline-none focus:ring-4 focus:ring-blue-100 focus:border-blue-500 transition-all">
                      <option>UTC</option>
                      <option>America/New_York</option>
                      <option>Europe/London</option>
                      <option>Asia/Karachi</option>
                      <option>Asia/Tokyo</option>
                    </select>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-bold text-slate-900 mb-4">AI Agent Settings</h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 bg-slate-50 rounded-xl">
                    <div>
                      <p className="text-sm font-bold text-slate-900">Auto-escalation</p>
                      <p className="text-xs text-slate-500 mt-1">Automatically escalate unresolved tickets after 3 attempts</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input type="checkbox" defaultChecked className="sr-only peer" />
                      <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-100 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>
                  <div className="flex items-center justify-between p-4 bg-slate-50 rounded-xl">
                    <div>
                      <p className="text-sm font-bold text-slate-900">Sentiment Analysis</p>
                      <p className="text-xs text-slate-500 mt-1">Analyze customer sentiment in all conversations</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input type="checkbox" defaultChecked className="sr-only peer" />
                      <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-100 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'channels' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-bold text-slate-900 mb-4">Channel Configuration</h3>
                <div className="space-y-4">
                  {/* Web Form */}
                  <div className="border-2 border-slate-100 rounded-2xl p-6">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="h-12 w-12 rounded-xl bg-blue-50 flex items-center justify-center text-blue-600">
                          <Globe size={24} />
                        </div>
                        <div>
                          <h4 className="text-base font-bold text-slate-900">Web Form</h4>
                          <p className="text-xs text-slate-500">Customer support form on website</p>
                        </div>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input type="checkbox" defaultChecked className="sr-only peer" />
                        <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-100 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                      </label>
                    </div>
                  </div>

                  {/* Email */}
                  <div className="border-2 border-slate-100 rounded-2xl p-6">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="h-12 w-12 rounded-xl bg-purple-50 flex items-center justify-center text-purple-600">
                          <Mail size={24} />
                        </div>
                        <div>
                          <h4 className="text-base font-bold text-slate-900">Email Support</h4>
                          <p className="text-xs text-slate-500">Gmail integration for email tickets</p>
                        </div>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input type="checkbox" defaultChecked className="sr-only peer" />
                        <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-100 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                      </label>
                    </div>
                    <div className="bg-slate-50 rounded-xl p-4 mt-4">
                      <label className="block text-sm font-bold text-slate-700 mb-2">Gmail API Key</label>
                      <input
                        type="password"
                        defaultValue="••••••••••••••••"
                        className="w-full px-4 py-3 border-2 border-slate-100 rounded-xl bg-white focus:outline-none focus:ring-4 focus:ring-blue-100 focus:border-blue-500 transition-all"
                      />
                    </div>
                  </div>

                  {/* WhatsApp */}
                  <div className="border-2 border-slate-100 rounded-2xl p-6">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="h-12 w-12 rounded-xl bg-green-50 flex items-center justify-center text-green-600">
                          <MessageCircle size={24} />
                        </div>
                        <div>
                          <h4 className="text-base font-bold text-slate-900">WhatsApp</h4>
                          <p className="text-xs text-slate-500">Meta WhatsApp Cloud API integration</p>
                        </div>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input type="checkbox" className="sr-only peer" />
                        <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-100 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                      </label>
                    </div>
                    <div className="bg-slate-50 rounded-xl p-4 mt-4 space-y-4">
                      <div>
                        <label className="block text-sm font-bold text-slate-700 mb-2">WhatsApp Phone ID</label>
                        <input
                          type="text"
                          placeholder="Enter your WhatsApp Phone ID"
                          className="w-full px-4 py-3 border-2 border-slate-100 rounded-xl bg-white focus:outline-none focus:ring-4 focus:ring-blue-100 focus:border-blue-500 transition-all"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-bold text-slate-700 mb-2">Meta Access Token</label>
                        <input
                          type="password"
                          placeholder="Enter your Meta Access Token"
                          className="w-full px-4 py-3 border-2 border-slate-100 rounded-xl bg-white focus:outline-none focus:ring-4 focus:ring-blue-100 focus:border-blue-500 transition-all"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'notifications' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-bold text-slate-900 mb-4">Email Notifications</h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-4 bg-slate-50 rounded-xl">
                    <div>
                      <p className="text-sm font-bold text-slate-900">New Ticket Alerts</p>
                      <p className="text-xs text-slate-500 mt-1">Receive email when a new ticket is created</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input type="checkbox" defaultChecked className="sr-only peer" />
                      <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-100 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>
                  <div className="flex items-center justify-between p-4 bg-slate-50 rounded-xl">
                    <div>
                      <p className="text-sm font-bold text-slate-900">Escalation Alerts</p>
                      <p className="text-xs text-slate-500 mt-1">Get notified when tickets are escalated</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input type="checkbox" defaultChecked className="sr-only peer" />
                      <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-100 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>
                  <div className="flex items-center justify-between p-4 bg-slate-50 rounded-xl">
                    <div>
                      <p className="text-sm font-bold text-slate-900">Daily Summary</p>
                      <p className="text-xs text-slate-500 mt-1">Receive daily summary of all tickets</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input type="checkbox" className="sr-only peer" />
                      <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-100 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-bold text-slate-900 mb-4">Notification Email</h3>
                <input
                  type="email"
                  defaultValue="admin@saasflow.com"
                  className="w-full px-4 py-3 border-2 border-slate-100 rounded-xl bg-white focus:outline-none focus:ring-4 focus:ring-blue-100 focus:border-blue-500 transition-all"
                />
              </div>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="space-y-6">
              <div className="bg-amber-50 border-2 border-amber-100 rounded-2xl p-6 flex items-start gap-4">
                <AlertCircle className="text-amber-600 flex-shrink-0 mt-1" size={24} />
                <div>
                  <h4 className="text-base font-bold text-amber-900">Security Notice</h4>
                  <p className="text-sm text-amber-700 mt-1">Keep your API keys and credentials secure. Never share them publicly.</p>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-bold text-slate-900 mb-4">API Configuration</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-bold text-slate-700 mb-2">OpenAI API Key</label>
                    <input
                      type="password"
                      defaultValue="sk-••••••••••••••••••••••••"
                      className="w-full px-4 py-3 border-2 border-slate-100 rounded-xl bg-white focus:outline-none focus:ring-4 focus:ring-blue-100 focus:border-blue-500 transition-all"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-bold text-slate-700 mb-2">Database Connection</label>
                    <div className="flex items-center gap-3 p-4 bg-green-50 border-2 border-green-100 rounded-xl">
                      <Database className="text-green-600" size={20} />
                      <span className="text-sm font-bold text-green-800">Connected to PostgreSQL</span>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-bold text-slate-700 mb-2">Kafka Broker</label>
                    <div className="flex items-center gap-3 p-4 bg-green-50 border-2 border-green-100 rounded-xl">
                      <Zap className="text-green-600" size={20} />
                      <span className="text-sm font-bold text-green-800">Connected to localhost:9092</span>
                    </div>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-bold text-slate-900 mb-4">Admin Users</h3>
                <div className="border-2 border-slate-100 rounded-2xl p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="h-12 w-12 rounded-xl bg-blue-50 flex items-center justify-center text-blue-600">
                        <Users size={24} />
                      </div>
                      <div>
                        <h4 className="text-base font-bold text-slate-900">Manage Admin Access</h4>
                        <p className="text-xs text-slate-500">Add or remove admin users</p>
                      </div>
                    </div>
                    <button className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-bold hover:bg-blue-700 transition-all">
                      Manage Users
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Save Button */}
          <div className="flex items-center justify-end gap-4 pt-6 border-t border-slate-200 mt-8">
            {saved && (
              <div className="flex items-center gap-2 text-green-600">
                <div className="h-2 w-2 rounded-full bg-green-600"></div>
                <span className="text-sm font-bold">Settings saved successfully!</span>
              </div>
            )}
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-xl font-bold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-blue-100"
            >
              {saving ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  Saving...
                </>
              ) : (
                <>
                  <Save size={20} />
                  Save Changes
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
