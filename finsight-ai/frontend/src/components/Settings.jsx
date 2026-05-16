import React, { useState } from 'react';
import { Card } from './ui/Card';
import { Button } from './ui/Button';
import { Badge } from './ui/Badge';
import { User, Bell, KeyRound, Palette, Eye, EyeOff, Check, Copy } from 'lucide-react';

const TABS = [
  { key: 'profile', label: 'Profile', icon: User },
  { key: 'notifications', label: 'Notifications', icon: Bell },
  { key: 'apikeys', label: 'API Keys', icon: KeyRound },
  { key: 'theme', label: 'Theme', icon: Palette },
];

function ProfileSection() {
  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold text-[#111111] mb-6">Profile Settings</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div>
          <label className="block text-[11px] font-semibold tracking-[0.08em] uppercase text-[#6B7280] mb-2">
            Display Name
          </label>
          <input
            id="settings-display-name"
            type="text"
            defaultValue="Amaan Siddiqui"
            className="w-full px-4 py-2.5 rounded-[12px] border border-[#E5E7EB] bg-white text-sm text-[#111111] focus:outline-none focus:border-[#111111] transition-colors"
          />
        </div>
        <div>
          <label className="block text-[11px] font-semibold tracking-[0.08em] uppercase text-[#6B7280] mb-2">
            Email
          </label>
          <input
            id="settings-email"
            type="email"
            defaultValue="amaan@example.com"
            className="w-full px-4 py-2.5 rounded-[12px] border border-[#E5E7EB] bg-white text-sm text-[#111111] focus:outline-none focus:border-[#111111] transition-colors"
          />
        </div>
        <div>
          <label className="block text-[11px] font-semibold tracking-[0.08em] uppercase text-[#6B7280] mb-2">
            Default User ID
          </label>
          <input
            id="settings-user-id"
            type="text"
            defaultValue="default"
            className="w-full px-4 py-2.5 rounded-[12px] border border-[#E5E7EB] bg-white text-sm text-[#111111] focus:outline-none focus:border-[#111111] transition-colors"
          />
        </div>
        <div>
          <label className="block text-[11px] font-semibold tracking-[0.08em] uppercase text-[#6B7280] mb-2">
            Starting Balance (₹)
          </label>
          <input
            id="settings-balance"
            type="number"
            defaultValue={100000}
            className="w-full px-4 py-2.5 rounded-[12px] border border-[#E5E7EB] bg-white text-sm text-[#111111] focus:outline-none focus:border-[#111111] transition-colors tabular-nums"
          />
        </div>
      </div>
      <div className="mt-6 flex justify-end">
        <Button variant="primary" size="sm">Save Changes</Button>
      </div>
    </Card>
  );
}

function NotificationsSection() {
  const [prefs, setPrefs] = useState({
    priceAlerts: true,
    ipoAlerts: true,
    portfolioUpdates: false,
    sentimentAlerts: false,
    weeklyReport: true,
  });

  const toggle = (key) => setPrefs(prev => ({ ...prev, [key]: !prev[key] }));

  const items = [
    { key: 'priceAlerts', label: 'Price Alerts', desc: 'Get notified when a stock hits your target price' },
    { key: 'ipoAlerts', label: 'IPO Alerts', desc: 'Notifications for new IPO openings and GMP changes' },
    { key: 'portfolioUpdates', label: 'Portfolio Updates', desc: 'Daily summary of your portfolio performance' },
    { key: 'sentimentAlerts', label: 'Sentiment Shifts', desc: 'Alert when market sentiment changes significantly' },
    { key: 'weeklyReport', label: 'Weekly Report', desc: 'Receive a weekly digest of market analysis' },
  ];

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold text-[#111111] mb-6">Notification Preferences</h3>
      <div className="space-y-4">
        {items.map(item => (
          <div key={item.key} className="flex items-center justify-between p-4 rounded-[12px] border border-[#E5E7EB] hover:bg-[#F7F8F5] transition-colors">
            <div>
              <p className="text-sm font-semibold text-[#111111]">{item.label}</p>
              <p className="text-xs text-[#6B7280] mt-0.5">{item.desc}</p>
            </div>
            <button
              id={`toggle-${item.key}`}
              onClick={() => toggle(item.key)}
              className={`relative w-11 h-6 rounded-full transition-colors duration-200 cursor-pointer ${
                prefs[item.key] ? 'bg-[#22C55E]' : 'bg-[#E5E7EB]'
              }`}
            >
              <span className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform duration-200 ${
                prefs[item.key] ? 'translate-x-5' : 'translate-x-0'
              }`} />
            </button>
          </div>
        ))}
      </div>
    </Card>
  );
}

function APIKeysSection() {
  const [showGemini, setShowGemini] = useState(false);
  const [copied, setCopied] = useState('');

  const handleCopy = (key) => {
    navigator.clipboard.writeText('••••••••••••');
    setCopied(key);
    setTimeout(() => setCopied(''), 2000);
  };

  const keys = [
    { key: 'gemini', label: 'Gemini API Key', status: 'configured', masked: 'AIza••••••••••••3xQ' },
    { key: 'reddit', label: 'Reddit Client ID', status: 'configured', masked: 'f3k••••••••d9' },
    { key: 'supabase', label: 'Supabase Key', status: 'not_set', masked: '' },
  ];

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold text-[#111111] mb-2">API Keys</h3>
      <p className="text-xs text-[#6B7280] mb-6">
        Manage external service API keys. Keys are stored in your <code className="bg-[#F3F4F6] px-1.5 py-0.5 rounded text-[11px]">.env</code> file.
      </p>
      <div className="space-y-4">
        {keys.map(item => (
          <div key={item.key} className="flex items-center justify-between p-4 rounded-[12px] border border-[#E5E7EB]">
            <div className="flex items-center gap-3">
              <KeyRound className="w-4 h-4 text-[#6B7280]" />
              <div>
                <p className="text-sm font-semibold text-[#111111]">{item.label}</p>
                {item.masked ? (
                  <p className="text-xs text-[#6B7280] tabular-nums mt-0.5 font-mono">{item.masked}</p>
                ) : (
                  <p className="text-xs text-[#EF4444] mt-0.5">Not configured</p>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant={item.status === 'configured' ? 'success' : 'danger'}>
                {item.status === 'configured' ? 'Active' : 'Missing'}
              </Badge>
              {item.masked && (
                <button
                  onClick={() => handleCopy(item.key)}
                  className="p-1.5 rounded-[6px] hover:bg-[#F3F4F6] transition-colors cursor-pointer"
                >
                  {copied === item.key ? <Check className="w-4 h-4 text-[#22C55E]" /> : <Copy className="w-4 h-4 text-[#6B7280]" />}
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

function ThemeSection() {
  const [theme, setTheme] = useState('light');

  const themes = [
    { key: 'light', label: 'Light', desc: 'Clean, minimal light interface', preview: 'bg-[#F7F8F5] border-[#E5E7EB]' },
    { key: 'dark', label: 'Dark', desc: 'Easy on the eyes for night trading', preview: 'bg-[#111111] border-[#333333]' },
    { key: 'system', label: 'System', desc: 'Follow your OS preference', preview: 'bg-gradient-to-r from-[#F7F8F5] to-[#111111] border-[#E5E7EB]' },
  ];

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold text-[#111111] mb-6">Theme</h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {themes.map(t => (
          <button
            key={t.key}
            id={`theme-${t.key}`}
            onClick={() => setTheme(t.key)}
            className={`p-4 rounded-[12px] border-2 text-left transition-all cursor-pointer ${
              theme === t.key
                ? 'border-[#111111] bg-[#F7F8F5]'
                : 'border-[#E5E7EB] hover:border-[#D1D5DB]'
            }`}
          >
            <div className={`w-full h-16 rounded-[8px] mb-3 border ${t.preview}`} />
            <p className="text-sm font-semibold text-[#111111]">{t.label}</p>
            <p className="text-xs text-[#6B7280] mt-0.5">{t.desc}</p>
            {theme === t.key && (
              <div className="flex items-center gap-1 mt-2">
                <Check className="w-3.5 h-3.5 text-[#22C55E]" />
                <span className="text-xs font-medium text-[#22C55E]">Active</span>
              </div>
            )}
          </button>
        ))}
      </div>
    </Card>
  );
}

export default function Settings() {
  const [activeTab, setActiveTab] = useState('profile');

  const sections = {
    profile: <ProfileSection />,
    notifications: <NotificationsSection />,
    apikeys: <APIKeysSection />,
    theme: <ThemeSection />,
  };

  return (
    <div className="flex flex-col gap-6 pb-10">
      <div>
        <h1 className="text-[28px] font-bold text-[#111111] leading-tight">Settings</h1>
        <p className="text-[#6B7280] text-sm mt-1">Manage your account, preferences, and integrations</p>
      </div>

      {/* Tab Bar */}
      <div className="flex gap-1 p-1 bg-[#F3F4F6] rounded-[12px] w-fit">
        {TABS.map(tab => (
          <button
            key={tab.key}
            id={`settings-tab-${tab.key}`}
            onClick={() => setActiveTab(tab.key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-[8px] text-sm font-medium transition-all cursor-pointer ${
              activeTab === tab.key
                ? 'bg-white text-[#111111] shadow-[0_1px_3px_rgba(0,0,0,0.06)]'
                : 'text-[#6B7280] hover:text-[#111111]'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Active Section */}
      {sections[activeTab]}
    </div>
  );
}
