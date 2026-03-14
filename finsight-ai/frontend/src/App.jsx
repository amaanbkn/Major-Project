import { useState } from 'react'
import { Routes, Route, NavLink } from 'react-router-dom'
import {
  MessageSquare, BarChart3, TrendingUp, Calendar,
  PiggyBank, Briefcase, Menu, X, Sparkles
} from 'lucide-react'
import Chat from './components/Chat'
import Dashboard from './components/Dashboard'
import StockCard from './components/StockCard'
import IPOTracker from './components/IPOTracker'
import SIPAdvisor from './components/SIPAdvisor'
import Portfolio from './components/Portfolio'

const navItems = [
  { path: '/', icon: MessageSquare, label: 'Chat', id: 'nav-chat' },
  { path: '/dashboard', icon: BarChart3, label: 'Dashboard', id: 'nav-dashboard' },
  { path: '/signals', icon: TrendingUp, label: 'Signals', id: 'nav-signals' },
  { path: '/ipo', icon: Calendar, label: 'IPO Tracker', id: 'nav-ipo' },
  { path: '/sip', icon: PiggyBank, label: 'SIP Advisor', id: 'nav-sip' },
  { path: '/portfolio', icon: Briefcase, label: 'Portfolio', id: 'nav-portfolio' },
]

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed lg:static inset-y-0 left-0 z-50
          w-64 lg:w-72
          flex flex-col
          bg-[var(--bg-secondary)] border-r border-[var(--border)]
          transition-transform duration-300 ease-in-out
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
      >
        {/* Logo */}
        <div className="flex items-center gap-3 px-6 py-5 border-b border-[var(--border)]">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
              FinSight AI
            </h1>
            <p className="text-[10px] text-[var(--text-muted)] tracking-widest uppercase">
              Market Intelligence
            </p>
          </div>
          <button
            className="lg:hidden ml-auto text-[var(--text-muted)] hover:text-white"
            onClick={() => setSidebarOpen(false)}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Nav links */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              id={item.id}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) => `
                flex items-center gap-3 px-4 py-3 rounded-xl
                text-sm font-medium transition-all duration-200
                group relative overflow-hidden
                ${isActive
                  ? 'bg-gradient-to-r from-indigo-500/15 to-purple-500/10 text-indigo-400 border border-indigo-500/20 shadow-lg shadow-indigo-500/5'
                  : 'text-[var(--text-secondary)] hover:bg-[var(--bg-card)] hover:text-[var(--text-primary)]'
                }
              `}
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-indigo-500 rounded-r-full" />
                  )}
                  <item.icon className={`w-5 h-5 ${isActive ? 'text-indigo-400' : 'text-[var(--text-muted)] group-hover:text-indigo-400'} transition-colors`} />
                  <span>{item.label}</span>
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Bottom section */}
        <div className="p-4 border-t border-[var(--border)]">
          <div className="glass-card p-4 text-center">
            <p className="text-xs text-[var(--text-muted)] mb-1">Developed by</p>
            <p className="text-xs font-semibold text-indigo-400">DBIT CSE 2025-26</p>
            <p className="text-[10px] text-[var(--text-muted)] mt-1">
              Guide: Mrs. Anjali Vyas
            </p>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Mobile header */}
        <header className="lg:hidden flex items-center gap-3 px-4 py-3 border-b border-[var(--border)] bg-[var(--bg-secondary)]">
          <button
            id="mobile-menu-toggle"
            onClick={() => setSidebarOpen(true)}
            className="p-2 rounded-lg hover:bg-[var(--bg-card)] text-[var(--text-muted)]"
          >
            <Menu className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-indigo-400" />
            <span className="font-bold text-indigo-400">FinSight AI</span>
          </div>
        </header>

        {/* Routes */}
        <div className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/" element={<Chat />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/signals" element={<StockCard />} />
            <Route path="/ipo" element={<IPOTracker />} />
            <Route path="/sip" element={<SIPAdvisor />} />
            <Route path="/portfolio" element={<Portfolio />} />
          </Routes>
        </div>
      </main>
    </div>
  )
}
