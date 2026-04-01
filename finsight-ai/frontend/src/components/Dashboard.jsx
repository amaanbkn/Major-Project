import React, { useState } from 'react';
import { Card } from './ui/Card';
import { Badge } from './ui/Badge';
import { Button } from './ui/Button';
import { ArrowUpRight, ArrowDownRight, Activity } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useCountUp } from '../hooks/useCountUp';

const mockChartData = [
  { time: '09:15', value: 22100 },
  { time: '10:00', value: 22150 },
  { time: '11:00', value: 22080 },
  { time: '12:00', value: 22200 },
  { time: '13:00', value: 22190 },
  { time: '14:00', value: 22350 },
  { time: '15:00', value: 22400 },
  { time: '15:30', value: 22450 },
];

const mockMovers = [
  { name: 'RELIANCE', price: 2950.45, change24h: 2.4, change7d: 5.2 },
  { name: 'HDFCBANK', price: 1420.10, change24h: -1.2, change7d: -2.0 },
  { name: 'TCS', price: 4100.00, change24h: 1.8, change7d: 3.5 },
  { name: 'INFY', price: 1650.75, change24h: -0.5, change7d: 1.1 },
];

const StatCard = ({ label, value, change, isPositive, suffix = "", prefix = "" }) => {
  const animatedValue = useCountUp(typeof value === 'number' ? value : 0);
  const displayValue = typeof value === 'number' ? `${prefix}${animatedValue.toLocaleString()}${suffix}` : value;

  return (
    <Card className="px-5 py-5 border-[#E5E7EB]">
      <div className="flex flex-col gap-1.5 cursor-default">
        <span className="text-[11px] font-medium uppercase tracking-[0.08em] text-[#6B7280]">
          {label}
        </span>
        <div className="flex items-end justify-between mt-1">
          <span className="text-[28px] font-bold tabular-nums text-[#111111] leading-none">
            {displayValue}
          </span>
          {change && (
            <div className={`flex items-center gap-0.5 px-2 py-1 rounded-[6px] ${isPositive ? 'bg-[#22C55E]/10 text-[#22C55E]' : 'bg-[#EF4444]/10 text-[#EF4444]'}`}>
              {isPositive ? <ArrowUpRight className="w-3.5 h-3.5" /> : <ArrowDownRight className="w-3.5 h-3.5" />}
              <span className="text-[13px] font-semibold">{Math.abs(change)}%</span>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
};

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-[#111111] text-white px-3 py-2 rounded-[8px] shadow-lg text-sm tabular-nums flex flex-col gap-1">
        <span className="text-[#6B7280] text-xs">{label}</span>
        <span className="font-semibold">₹{payload[0].value.toLocaleString()}</span>
      </div>
    );
  }
  return null;
};

export default function Dashboard() {
  const [timeRange, setTimeRange] = useState('1D');
  const ranges = ['1D', '7D', '1M', '1Y', 'ALL'];

  return (
    <div className="flex flex-col gap-5 pb-10">
      
      {/* Top Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        <StatCard label="NIFTY 50" value={22450} change={1.2} isPositive={true} prefix="₹" />
        <StatCard label="SENSEX" value={73800} change={0.8} isPositive={true} prefix="₹" />
        <StatCard label="Market Sentiment" value="BULLISH" change={0} isPositive={true} />
        <StatCard label="Active IPOs" value={4} />
      </div>

      {/* Main Chart */}
      <Card className="p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-semibold text-[#111111]">NIFTY 50 Overview</h2>
            <Badge variant="success">Market Open</Badge>
          </div>
          
          <div className="flex items-center gap-2">
            {ranges.map(range => (
              <button
                key={range}
                onClick={() => setTimeRange(range)}
                className={`px-3 py-1 text-xs font-semibold rounded-full transition-colors ${
                  timeRange === range 
                    ? 'bg-[#111111] text-white' 
                    : 'bg-transparent border border-[#E5E7EB] text-[#6B7280] hover:bg-[#F3F4F6]'
                }`}
              >
                {range}
              </button>
            ))}
          </div>
        </div>

        <div className="h-[300px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={mockChartData} margin={{ top: 10, right: 0, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#22C55E" stopOpacity={0.15}/>
                  <stop offset="95%" stopColor="#22C55E" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#6B7280', strokeWidth: 1, strokeDasharray: '4 4' }} />
              <Area 
                type="monotone" 
                dataKey="value" 
                stroke="#22C55E" 
                strokeWidth={2}
                fillOpacity={1} 
                fill="url(#colorValue)" 
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {/* Top Movers Table */}
      <Card className="p-0 overflow-hidden">
        <div className="px-6 py-5 border-b border-[#E5E7EB]">
          <h2 className="text-lg font-semibold text-[#111111]">Top Movers</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-[11px] uppercase tracking-[0.08em] text-[#6B7280] bg-[#F7F8F5]">
              <tr>
                <th className="px-6 py-4 font-medium">Name</th>
                <th className="px-6 py-4 font-medium">Price</th>
                <th className="px-6 py-4 font-medium">24h Change</th>
                <th className="px-6 py-4 font-medium">7d Change</th>
                <th className="px-6 py-4 font-medium text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E5E7EB]">
              {mockMovers.map((stock) => (
                <tr key={stock.name} className="hover:bg-[#F7F8F5] transition-colors duration-150">
                  <td className="px-6 py-4 font-semibold text-[#111111]">{stock.name}</td>
                  <td className="px-6 py-4 font-bold tabular-nums">₹{stock.price.toFixed(2)}</td>
                  <td className={`px-6 py-4 font-semibold tabular-nums ${stock.change24h >= 0 ? 'text-[#22C55E]' : 'text-[#EF4444]'}`}>
                    {stock.change24h > 0 ? '+' : ''}{stock.change24h}%
                  </td>
                  <td className={`px-6 py-4 font-semibold tabular-nums ${stock.change7d >= 0 ? 'text-[#22C55E]' : 'text-[#EF4444]'}`}>
                    {stock.change7d > 0 ? '+' : ''}{stock.change7d}%
                  </td>
                  <td className="px-6 py-3 text-right">
                    <div className="flex justify-end gap-2">
                      <Button variant="outline" size="sm" className="w-[60px]">Sell</Button>
                      <Button variant="primary" size="sm" className="w-[60px]">Buy</Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
      
    </div>
  );
}
