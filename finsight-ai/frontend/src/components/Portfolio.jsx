import React, { useState } from 'react';
import { Card } from './ui/Card';
import { Badge } from './ui/Badge';
import { Button } from './ui/Button';
import { useCountUp } from '../hooks/useCountUp';
import { ChevronDown, ChevronUp } from 'lucide-react';

const mockHoldings = [
  { name: 'RELIANCE', shares: 50, avgPrice: 2850.00, currentPrice: 2950.45, change24h: 2.4 },
  { name: 'TCS', shares: 20, avgPrice: 3950.00, currentPrice: 4100.00, change24h: 1.8 },
  { name: 'HDFCBANK', shares: 100, avgPrice: 1550.00, currentPrice: 1420.10, change24h: -1.2 },
];

const mockTransactions = [
  { 
    date: 'Today, 10:45 AM',
    items: [
      { type: 'BUY', name: 'RELIANCE', shares: 10, price: 2940.00 },
      { type: 'SELL', name: 'INFY', shares: 25, price: 1650.00 }
    ]
  },
  { 
    date: 'Yesterday',
    items: [
      { type: 'BUY', name: 'TCS', shares: 5, price: 4050.00 }
    ]
  }
];

export default function Portfolio() {
  const balance = useCountUp(1450000);
  const totalPL = useCountUp(45600);
  const [expandedTx, setExpandedTx] = useState(mockTransactions.map((_, i) => i));

  const toggleTx = (index) => {
    setExpandedTx(prev => 
      prev.includes(index) ? prev.filter(i => i !== index) : [...prev, index]
    );
  };

  return (
    <div className="flex flex-col gap-6 pb-10">
      
      {/* Balance Hero Card */}
      <div className="bg-[#111111] rounded-[16px] p-8 text-white relative overflow-hidden shadow-lg">
        <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-indigo-500/20 to-purple-500/0 rounded-full blur-3xl -mr-20 -mt-20"></div>
        <div className="relative z-10">
          <span className="text-[11px] font-semibold tracking-[0.08em] uppercase text-[#6B7280]">
            Virtual Portfolio
          </span>
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mt-2">
            <h1 className="text-[36px] md:text-[48px] font-bold tabular-nums tracking-[-0.02em] leading-none">
              ₹{balance.toLocaleString()}
            </h1>
            <div className="flex items-center gap-3">
              <span className="text-[#6B7280] text-sm font-medium">Total P&L</span>
              <Badge variant="success" className="!text-sm !px-3 !py-1">
                +₹{totalPL.toLocaleString()} (+3.2%)
              </Badge>
            </div>
          </div>
        </div>
      </div>

      {/* Holdings Table */}
      <Card className="p-0 overflow-hidden">
        <div className="px-6 py-5 border-b border-[#E5E7EB] flex justify-between items-center bg-white">
          <h2 className="text-lg font-semibold text-[#111111]">Current Holdings</h2>
          <Button variant="outline" size="sm">Download Report</Button>
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
              {mockHoldings.map((stock) => {
                const pl = (stock.currentPrice - stock.avgPrice) * stock.shares;
                const plPercent = ((stock.currentPrice - stock.avgPrice) / stock.avgPrice) * 100;
                const isPositive = pl >= 0;

                return (
                  <tr key={stock.name} className="hover:bg-[#F7F8F5] transition-colors duration-150">
                    <td className="px-6 py-4 font-semibold text-[#111111]">{stock.name}</td>
                    <td className="px-6 py-4 tabular-nums text-[#6B7280]">{stock.shares}</td>
                    <td className="px-6 py-4 tabular-nums">₹{stock.avgPrice.toFixed(2)}</td>
                    <td className="px-6 py-4 font-bold tabular-nums text-[#111111]">₹{stock.currentPrice.toFixed(2)}</td>
                    <td className={`px-6 py-4 font-bold tabular-nums ${isPositive ? 'text-[#22C55E]' : 'text-[#EF4444]'}`}>
                      {isPositive ? '+' : ''}₹{pl.toLocaleString('en-IN', { maximumFractionDigits: 0 })} 
                      <span className="text-[11px] font-medium ml-1">({isPositive ? '+' : ''}{plPercent.toFixed(1)}%)</span>
                    </td>
                    <td className="px-6 py-3 text-right">
                      <div className="flex justify-end gap-2">
                        <Button variant="outline" size="sm" className="w-[60px]">Sell</Button>
                        <Button variant="primary" size="sm" className="w-[80px]">Buy More</Button>
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
      <h2 className="text-lg font-semibold text-[#111111] mt-4 px-2">Transaction History</h2>
      <div className="flex flex-col gap-3">
        {mockTransactions.map((group, index) => {
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
                className={`overflow-hidden transition-all duration-300 ease-in-out ${isOpen ? 'max-h-[500px]' : 'max-h-0'}`}
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
