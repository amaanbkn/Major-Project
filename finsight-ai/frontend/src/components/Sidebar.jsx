import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { LayoutDashboard, LineChart, Wallet2, ArrowLeftRight, Settings, Sparkles, PiggyBank, LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const navItems = [
  { path: '/', icon: Sparkles, label: 'Chat' },
  { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/market', icon: LineChart, label: 'Market' },
  { path: '/portfolio', icon: Wallet2, label: 'Wallet' },
  { path: '/sip', icon: PiggyBank, label: 'SIP Advisor' },
  { path: '/transactions', icon: ArrowLeftRight, label: 'Transactions' },
  { path: '/settings', icon: Settings, label: 'Settings' }
];

export const Sidebar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const userInitial = user?.email ? user.email.charAt(0).toUpperCase() : 'U';

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

      {/* User Profile & Logout */}
      <div className="p-6 mt-auto">
        <div className="flex items-center gap-3 p-2 rounded-[12px] bg-[#1A1A1A] mb-3 border border-[#333333]">
          <div className="w-9 h-9 rounded-full bg-[#111111] flex items-center justify-center text-xs font-semibold">
            {userInitial}
          </div>
          <div className="flex flex-col overflow-hidden text-ellipsis">
            <span className="text-sm font-medium truncate">{user?.email || 'User'}</span>
            <span className="text-[11px] text-[#6B7280]">Authenticated</span>
          </div>
        </div>
        
        <button
          onClick={handleLogout}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-[12px] text-sm font-medium text-[#EF4444] bg-[#EF4444]/10 hover:bg-[#EF4444]/20 transition-colors"
        >
          <LogOut className="w-4 h-4" />
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  );
};
