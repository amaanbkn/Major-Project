import { Routes, Route } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import Chat from './components/Chat';
import Dashboard from './components/Dashboard';
import IPOTracker from './components/IPOTracker';
import Portfolio from './components/Portfolio';

export default function App() {
  return (
    <div className="flex h-screen bg-[#F7F8F5] overflow-hidden">
      <Sidebar />
      
      {/* Main content - subtract sidebar width and add padding */}
      <main className="flex-1 ml-[220px] h-full overflow-y-auto overflow-x-hidden p-[28px] md:px-[32px] md:py-[28px] max-w-[1100px] mx-auto w-full">
        <div className="animate-in fade-in duration-200 h-full">
          <Routes>
            <Route path="/" element={<Chat />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/market" element={<IPOTracker />} />
            <Route path="/portfolio" element={<Portfolio />} />
            {/* Fallbacks */}
            <Route path="/transactions" element={<Portfolio />} />
            <Route path="/settings" element={<Dashboard />} />
            <Route path="/ipo" element={<IPOTracker />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}
