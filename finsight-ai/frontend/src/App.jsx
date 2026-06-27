import { Routes, Route, Navigate } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import Chat from './components/Chat';
import Dashboard from './components/Dashboard';
import IPOTracker from './components/IPOTracker';
import Portfolio from './components/Portfolio';
import SIPAdvisor from './components/SIPAdvisor';
import Settings from './components/Settings';
import Transactions from './components/Transactions';
import Market from './components/Market';
import AdminRAG from './components/AdminRAG';
import Login from './pages/Login';
import Register from './pages/Register';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';

function ProtectedRoute({ children }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" />;
  
  return (
    <div className="flex h-screen bg-[#F7F8F5] overflow-hidden">
      <Sidebar />
      <main className="flex-1 ml-[220px] h-full overflow-y-auto overflow-x-hidden p-[28px] md:px-[32px] md:py-[28px] max-w-[1100px] mx-auto w-full">
        <div className="animate-in fade-in duration-200 h-full">
          {children}
        </div>
      </main>
    </div>
  );
}

function PublicRoute({ children }) {
  const { user } = useAuth();
  if (user) return <Navigate to="/" />;
  return children;
}

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
          <Route path="/register" element={<PublicRoute><Register /></PublicRoute>} />
          
          <Route path="/" element={<ProtectedRoute><Chat /></ProtectedRoute>} />
          <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/market" element={<ProtectedRoute><Market /></ProtectedRoute>} />
          <Route path="/portfolio" element={<ProtectedRoute><Portfolio /></ProtectedRoute>} />
          <Route path="/transactions" element={<ProtectedRoute><Transactions /></ProtectedRoute>} />
          <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
          <Route path="/sip" element={<ProtectedRoute><SIPAdvisor /></ProtectedRoute>} />
          <Route path="/ipo" element={<ProtectedRoute><IPOTracker /></ProtectedRoute>} />
          <Route path="/admin" element={<ProtectedRoute><AdminRAG /></ProtectedRoute>} />
        </Routes>
      </AuthProvider>
    </ThemeProvider>
  );
}
