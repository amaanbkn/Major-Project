import React, { useState, useEffect } from 'react';
import { Card } from './ui/Card';
import { Badge } from './ui/Badge';
import { Button } from './ui/Button';
import { useCountUp } from '../hooks/useCountUp';
import { ChevronDown, ChevronUp, Loader2 } from 'lucide-react';
import { getPortfolio, buyStock, sellStock, getTransactions } from '../api';

export default function Portfolio() {
  const [portfolio, setPortfolio] = useState({ balance: 0, holdings: [] });
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedTx, setExpandedTx] = useState([]);

  // For toasts
  const [toast, setToast] = useState(null);

  const balance = useCountUp(portfolio.balance || 0);

  const fetchPortfolioData = async () => {
    try {
      setLoading(true);
      const [portData, txData] = await Promise.all([
        getPortfolio(),
        getTransactions()
      ]);
      setPortfolio(portData);
      
      // Group transactions by date for UI
      const grouped = {};
      (txData.transactions || []).forEach(tx => {
        // Just using full date string as a simple group key for now
        const dateStr = new Date(tx.timestamp).toLocaleDateString();
        if (!grouped[dateStr]) grouped[dateStr] = [];
        grouped[dateStr].push({
          type: tx.action,
          name: tx.symbol,
          shares: tx.quantity,
          price: tx.price
        });
      });
      
      const txGroups = Object.keys(grouped).map(date => ({
        date,
        items: grouped[date]
      }));
      setTransactions(txGroups);
      setExpandedTx(txGroups.map((_, i) => i)); // expand all by default
    } catch (err) {
      setError(err.message || "Failed to load portfolio");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPortfolioData();
  }, []);

  const handleTrade = async (action, symbol, currentQty) => {
    // For a simple UI, we prompt for quantity. In a real app, you'd have a modal.
    const qtyStr = window.prompt(`How many shares of ${symbol} would you like to ${action}?`, "1");
    if (!qtyStr) return;
    const qty = parseFloat(qtyStr);
    if (isNaN(qty) || qty <= 0) {
      showToast("Invalid quantity", "error");
      return;
    }
    
    if (action === 'SELL' && qty > currentQty) {
      showToast(`You only have ${currentQty} shares of ${symbol} to sell.`, "error");
      return;
    }

    try {
      showToast(`Executing ${action}...`, "info");
      let res;
      if (action === 'BUY') {
        res = await buyStock(symbol, qty);
      } else {
        res = await sellStock(symbol, qty);
      }
      
      if (res.status === 'success') {
        showToast(res.message, "success");
        // Re-fetch to get updated state
        fetchPortfolioData();
      } else {
        showToast(res.message || "Trade failed", "error");
      }
    } catch (err) {
      showToast(err.message || "Trade failed", "error");
    }
  };

  const showToast = (message, type) => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const toggleTx = (index) => {
    setExpandedTx(prev => 
      prev.includes(index) ? prev.filter(i => i !== index) : [...prev, index]
    );
  };

  if (loading && !portfolio.holdings.length) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-[#6B7280]" />
      </div>
    );
  }

  // Calculate Total P&L
  let totalCurrentValue = 0;
  let totalInvested = 0;
  portfolio.holdings.forEach(h => {
    totalCurrentValue += (h.current_price || h.buy_price) * h.quantity;
    totalInvested += h.buy_price * h.quantity;
  });
  const plValue = totalCurrentValue - totalInvested;
  const plPercent = totalInvested > 0 ? (plValue / totalInvested) * 100 : 0;
  const isPositiveOverall = plValue >= 0;

  return (
    <div className="flex flex-col gap-6 pb-10 relative">
      
      {/* Toast Notification */}
      {toast && (
        <div className={`fixed bottom-4 right-4 px-4 py-3 rounded shadow-lg text-white z-50 ${toast.type === 'error' ? 'bg-red-500' : toast.type === 'success' ? 'bg-green-500' : 'bg-blue-500'}`}>
          {toast.message}
        </div>
      )}

      {error && (
        <div className="bg-red-50 text-red-500 p-4 rounded-md">
          {error}
        </div>
      )}

      {/* Balance Hero Card */}
      <div className="bg-[#111111] rounded-[16px] p-8 text-white relative overflow-hidden shadow-lg">
        <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-indigo-500/20 to-purple-500/0 rounded-full blur-3xl -mr-20 -mt-20"></div>
        <div className="relative z-10">
          <span className="text-[11px] font-semibold tracking-[0.08em] uppercase text-[#6B7280]">
            Virtual Portfolio Cash Balance
          </span>
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mt-2">
            <h1 className="text-[36px] md:text-[48px] font-bold tabular-nums tracking-[-0.02em] leading-none">
              ₹{balance.toLocaleString()}
            </h1>
            <div className="flex items-center gap-3">
              <span className="text-[#6B7280] text-sm font-medium">Total P&L</span>
              <Badge variant={isPositiveOverall ? "success" : "danger"} className="!text-sm !px-3 !py-1">
                {isPositiveOverall ? '+' : ''}₹{plValue.toLocaleString(undefined, {maximumFractionDigits: 2})} ({isPositiveOverall ? '+' : ''}{plPercent.toFixed(2)}%)
              </Badge>
            </div>
          </div>
        </div>
      </div>

      {/* Holdings Table */}
      <Card className="p-0 overflow-hidden">
        <div className="px-6 py-5 border-b border-[#E5E7EB] flex justify-between items-center bg-white">
          <h2 className="text-lg font-semibold text-[#111111]">Current Holdings</h2>
          <Button variant="outline" size="sm" onClick={fetchPortfolioData}>Refresh</Button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left whitespace-nowrap">
            <thead className="text-[11px] uppercase tracking-[0.08em] text-[#6B7280] bg-[#F7F8F5]">
              <tr>
                <th className="px-6 py-4 font-medium">Asset</th>
                <th className="px-6 py-4 font-medium">Shares</th>
                <th className="px-6 py-4 font-medium">Avg. Price</th>
                <th className="px-6 py-4 font-medium">Current</th>
                <th className="px-6 py-4 font-medium">Total P&L</th>
                <th className="px-6 py-4 font-medium text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E5E7EB] bg-white">
              {portfolio.holdings.length === 0 ? (
                <tr>
                  <td colSpan="6" className="px-6 py-8 text-center text-gray-500">No holdings found. Start trading!</td>
                </tr>
              ) : portfolio.holdings.map((stock) => {
                const currentPrice = stock.current_price || stock.buy_price;
                const pl = (currentPrice - stock.buy_price) * stock.quantity;
                const plPct = ((currentPrice - stock.buy_price) / stock.buy_price) * 100;
                const isPos = pl >= 0;

                return (
                  <tr key={stock.symbol} className="hover:bg-[#F7F8F5] transition-colors duration-150">
                    <td className="px-6 py-4 font-semibold text-[#111111]">{stock.symbol}</td>
                    <td className="px-6 py-4 tabular-nums text-[#6B7280]">{stock.quantity}</td>
                    <td className="px-6 py-4 tabular-nums">₹{stock.buy_price.toFixed(2)}</td>
                    <td className="px-6 py-4 font-bold tabular-nums text-[#111111]">₹{currentPrice.toFixed(2)}</td>
                    <td className={`px-6 py-4 font-bold tabular-nums ${isPos ? 'text-[#22C55E]' : 'text-[#EF4444]'}`}>
                      {isPos ? '+' : ''}₹{pl.toLocaleString('en-IN', { maximumFractionDigits: 0 })} 
                      <span className="text-[11px] font-medium ml-1">({isPos ? '+' : ''}{plPct.toFixed(1)}%)</span>
                    </td>
                    <td className="px-6 py-3 text-right">
                      <div className="flex justify-end gap-2">
                        <Button variant="outline" size="sm" className="w-[60px]" onClick={() => handleTrade('SELL', stock.symbol, stock.quantity)}>Sell</Button>
                        <Button variant="primary" size="sm" className="w-[80px]" onClick={() => handleTrade('BUY', stock.symbol, stock.quantity)}>Buy More</Button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Transaction History Accordion */}
      <h2 className="text-lg font-semibold text-[#111111] mt-4 px-2">Recent Transactions</h2>
      <div className="flex flex-col gap-3">
        {transactions.length === 0 && !loading ? (
          <div className="text-gray-500 text-sm px-2">No transaction history.</div>
        ) : transactions.map((group, index) => {
          const isOpen = expandedTx.includes(index);
          return (
            <Card key={index} className="overflow-hidden">
              <button 
                onClick={() => toggleTx(index)}
                className="w-full flex items-center justify-between px-6 py-4 bg-white hover:bg-[#F7F8F5] transition-colors focus:outline-none"
              >
                <span className="font-semibold text-sm text-[#111111]">{group.date}</span>
                {isOpen ? <ChevronUp className="w-5 h-5 text-[#6B7280]" /> : <ChevronDown className="w-5 h-5 text-[#6B7280]" />}
              </button>
              
              <div 
                className={`overflow-hidden transition-all duration-300 ease-in-out ${isOpen ? 'max-h-[500px] overflow-y-auto' : 'max-h-0'}`}
              >
                <div className="border-t border-[#E5E7EB] bg-[#F7F8F5]">
                  {group.items.map((tx, i) => (
                    <div key={i} className={`flex items-center justify-between px-6 py-4 ${i !== group.items.length - 1 ? 'border-b border-[#E5E7EB]' : ''}`}>
                      <div className="flex items-center gap-4">
                        <Badge variant={tx.type === 'BUY' ? 'success' : 'danger'} className="w-[50px] justify-center">
                          {tx.type}
                        </Badge>
                        <span className="font-semibold text-sm text-[#111111]">{tx.name}</span>
                      </div>
                      <div className="flex items-center gap-6">
                        <span className="text-sm text-[#6B7280]">{tx.shares} shares @ ₹{tx.price.toFixed(2)}</span>
                        <span className="font-bold text-sm tabular-nums text-[#111111]">
                          ₹{(tx.shares * tx.price).toLocaleString()}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </Card>
          );
        })}
      </div>

    </div>
  );
}
