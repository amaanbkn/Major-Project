import React, { useState, useEffect } from 'react';
import { Card } from './ui/Card';
import { Badge } from './ui/Badge';
import { ArrowUpRight, ArrowDownRight, Loader2, RefreshCw } from 'lucide-react';
import { Button } from './ui/Button';
import { getTransactions } from '../api';

const MOCK_TRANSACTIONS = [
  { symbol: 'RELIANCE', action: 'BUY', quantity: 10, price: 2940.00, total: 29400.00, timestamp: '2026-05-16 10:45:00' },
  { symbol: 'INFY', action: 'SELL', quantity: 25, price: 1650.00, total: 41250.00, timestamp: '2026-05-16 10:30:00' },
  { symbol: 'TCS', action: 'BUY', quantity: 5, price: 4050.00, total: 20250.00, timestamp: '2026-05-15 14:22:00' },
  { symbol: 'HDFCBANK', action: 'BUY', quantity: 30, price: 1420.10, total: 42603.00, timestamp: '2026-05-15 11:10:00' },
  { symbol: 'WIPRO', action: 'SELL', quantity: 50, price: 480.25, total: 24012.50, timestamp: '2026-05-14 15:15:00' },
  { symbol: 'TATAMOTORS', action: 'BUY', quantity: 20, price: 950.30, total: 19006.00, timestamp: '2026-05-14 09:45:00' },
  { symbol: 'SBIN', action: 'BUY', quantity: 40, price: 780.50, total: 31220.00, timestamp: '2026-05-13 12:30:00' },
  { symbol: 'ADANIENT', action: 'SELL', quantity: 15, price: 3250.75, total: 48761.25, timestamp: '2026-05-13 10:00:00' },
  { symbol: 'ICICIBANK', action: 'BUY', quantity: 35, price: 1120.00, total: 39200.00, timestamp: '2026-05-12 14:50:00' },
  { symbol: 'BAJFINANCE', action: 'SELL', quantity: 8, price: 7120.00, total: 56960.00, timestamp: '2026-05-12 11:20:00' },
];

function formatTimestamp(ts) {
  try {
    const date = new Date(ts);
    return date.toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return ts;
  }
}

export default function Transactions() {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState('ALL');

  async function fetchTransactions() {
    setLoading(true);
    setError('');
    try {
      const data = await getTransactions();
      if (data.transactions && data.transactions.length > 0) {
        setTransactions(data.transactions);
      } else {
        // Fallback to mock data when no real transactions exist
        setTransactions(MOCK_TRANSACTIONS);
      }
    } catch {
      // API unavailable — use mock data
      setTransactions(MOCK_TRANSACTIONS);
    }
    setLoading(false);
  }

  useEffect(() => {
    fetchTransactions();
  }, []);

  const filtered = filter === 'ALL'
    ? transactions
    : transactions.filter(tx => tx.action === filter);

  const totalBuys = transactions.filter(t => t.action === 'BUY').reduce((s, t) => s + (t.total || t.quantity * t.price), 0);
  const totalSells = transactions.filter(t => t.action === 'SELL').reduce((s, t) => s + (t.total || t.quantity * t.price), 0);

  return (
    <div className="flex flex-col gap-6 pb-10">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-[28px] font-bold text-[#111111] leading-tight">Transactions</h1>
          <p className="text-[#6B7280] text-sm mt-1">Complete history of your paper trading activity</p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchTransactions}>
          <RefreshCw className={`w-4 h-4 mr-1.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <Card className="px-5 py-5">
          <span className="text-[11px] font-medium uppercase tracking-[0.08em] text-[#6B7280]">Total Transactions</span>
          <p className="text-[28px] font-bold tabular-nums text-[#111111] mt-1 leading-none">{transactions.length}</p>
        </Card>
        <Card className="px-5 py-5">
          <span className="text-[11px] font-medium uppercase tracking-[0.08em] text-[#6B7280]">Total Bought</span>
          <div className="flex items-end gap-2 mt-1">
            <p className="text-[28px] font-bold tabular-nums text-[#111111] leading-none">
              ₹{totalBuys.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
            </p>
            <div className="flex items-center gap-0.5 px-2 py-1 rounded-[6px] bg-[#22C55E]/10 text-[#22C55E] mb-0.5">
              <ArrowUpRight className="w-3.5 h-3.5" />
              <span className="text-[13px] font-semibold">{transactions.filter(t => t.action === 'BUY').length}</span>
            </div>
          </div>
        </Card>
        <Card className="px-5 py-5">
          <span className="text-[11px] font-medium uppercase tracking-[0.08em] text-[#6B7280]">Total Sold</span>
          <div className="flex items-end gap-2 mt-1">
            <p className="text-[28px] font-bold tabular-nums text-[#111111] leading-none">
              ₹{totalSells.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
            </p>
            <div className="flex items-center gap-0.5 px-2 py-1 rounded-[6px] bg-[#EF4444]/10 text-[#EF4444] mb-0.5">
              <ArrowDownRight className="w-3.5 h-3.5" />
              <span className="text-[13px] font-semibold">{transactions.filter(t => t.action === 'SELL').length}</span>
            </div>
          </div>
        </Card>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2">
        {['ALL', 'BUY', 'SELL'].map(f => (
          <button
            key={f}
            id={`filter-${f.toLowerCase()}`}
            onClick={() => setFilter(f)}
            className={`px-4 py-1.5 text-xs font-semibold rounded-full transition-colors cursor-pointer ${
              filter === f
                ? 'bg-[#111111] text-white'
                : 'bg-transparent border border-[#E5E7EB] text-[#6B7280] hover:bg-[#F3F4F6]'
            }`}
          >
            {f === 'ALL' ? 'All' : f === 'BUY' ? '🟢 Buys' : '🔴 Sells'}
          </button>
        ))}
      </div>

      {/* Transactions Table */}
      <Card className="p-0 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-6 h-6 animate-spin text-[#6B7280]" />
          </div>
        ) : error ? (
          <div className="text-center py-16">
            <p className="text-sm text-[#EF4444]">{error}</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left whitespace-nowrap">
              <thead className="text-[11px] uppercase tracking-[0.08em] text-[#6B7280] bg-[#F7F8F5]">
                <tr>
                  <th className="px-6 py-4 font-medium">Date</th>
                  <th className="px-6 py-4 font-medium">Stock</th>
                  <th className="px-6 py-4 font-medium">Action</th>
                  <th className="px-6 py-4 font-medium">Quantity</th>
                  <th className="px-6 py-4 font-medium">Price</th>
                  <th className="px-6 py-4 font-medium text-right">Total</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E5E7EB] bg-white">
                {filtered.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-12 text-center text-[#6B7280]">
                      No transactions found
                    </td>
                  </tr>
                ) : (
                  filtered.map((tx, i) => (
                    <tr key={i} className="hover:bg-[#F7F8F5] transition-colors duration-150">
                      <td className="px-6 py-4 text-[#6B7280] text-xs tabular-nums">
                        {formatTimestamp(tx.timestamp)}
                      </td>
                      <td className="px-6 py-4 font-semibold text-[#111111]">{tx.symbol}</td>
                      <td className="px-6 py-4">
                        <Badge variant={tx.action === 'BUY' ? 'success' : 'danger'}>
                          {tx.action}
                        </Badge>
                      </td>
                      <td className="px-6 py-4 tabular-nums text-[#111111]">{tx.quantity}</td>
                      <td className="px-6 py-4 tabular-nums font-medium text-[#111111]">
                        ₹{tx.price.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </td>
                      <td className="px-6 py-4 text-right font-bold tabular-nums text-[#111111]">
                        ₹{(tx.total || tx.quantity * tx.price).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
