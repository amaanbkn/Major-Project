import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, LineChart, Wallet2, ArrowLeftRight, Settings, Sparkles } from 'lucide-react';

const navItems = [
  { path: '/', icon: Sparkles, label: 'Chat' },
  { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/market', icon: LineChart, label: 'Market' },
  { path: '/portfolio', icon: Wallet2, label: 'Wallet' },
  { path: '/transactions', icon: ArrowLeftRight, label: 'Transactions' },
  { path: '/settings', icon: Settings, label: 'Settings' }
];

export const Sidebar = () => {
  return (
    <aside className="fixed inset-y-0 left-0 z-50 w-[220px] bg-[#111111] text-white flex flex-col h-full">
      {/* Brand */}
      <div className="flex items-center gap-3 px-6 py-8">
        <div className="w-8 h-8 rounded-full bg-white flex items-center justify-center">
          <span className="text-[#111111] font-bold text-sm">F</span>
        </div>
        <span className="font-semibold tracking-wide">FinSight</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => `
              flex items-center gap-3 px-4 py-3 rounded-full
              text-sm font-medium transition-all duration-200
              ${isActive
                ? 'bg-white text-[#111111]'
                : 'text-[#6B7280] hover:text-white hover:bg-[#1A1A1A]'
              }
            `}
          >
            {({ isActive }) => (
              <>
                <item.icon className={`w-4 h-4 ${isActive ? 'text-[#111111]' : ''}`} />
                <span>{item.label}</span>
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* User Profile */}
      <div className="p-6 mt-auto">
        <div className="flex items-center gap-3 p-2 rounded-[12px] hover:bg-[#1A1A1A] transition-colors cursor-pointer border border-transparent hover:border-[#1A1A1A]">
          <div className="w-9 h-9 rounded-full bg-[#1A1A1A] flex items-center justify-center text-xs font-semibold">
            AS
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-medium">Amaan S.</span>
            <span className="text-[11px] text-[#6B7280]">0x7F...3a9C</span>
          </div>
        </div>
      </div>
    </aside>
  );
};
