import React, { useState, useEffect } from 'react';
import { Card } from './ui/Card';
import { Badge } from './ui/Badge';
import { Button } from './ui/Button';
import { ArrowUpRight, ArrowDownRight, Activity, Loader2 } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useCountUp } from '../hooks/useCountUp';
import { getNifty50, getMarketSentiment, getNiftyHistory } from '../api';

const StatCard = ({ label, value, change, isPositive, suffix = "", prefix = "", loading = false }) => {
  const animatedValue = useCountUp(typeof value === 'number' && !loading ? value : 0);
  const displayValue = loading 
    ? <Loader2 className="w-6 h-6 animate-spin text-[#E5E7EB]" /> 
    : typeof value === 'number' ? `${prefix}${animatedValue.toLocaleString()}${suffix}` : value;

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
          {change !== undefined && !loading && (
            <div className={`flex items-center gap-0.5 px-2 py-1 rounded-[6px] ${isPositive ? 'bg-[#22C55E]/10 text-[#22C55E]' : 'bg-[#EF4444]/10 text-[#EF4444]'}`}>
              {isPositive ? <ArrowUpRight className="w-3.5 h-3.5" /> : <ArrowDownRight className="w-3.5 h-3.5" />}
              <span className="text-[13px] font-semibold">{Math.abs(change).toFixed(2)}%</span>
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
  
  const [loading, setLoading] = useState(true);
  const [indexData, setIndexData] = useState({ value: 0, change: 0, change_pct: 0 });
  const [stocks, setStocks] = useState([]);
  const [sentiment, setSentiment] = useState({ overall_label: "NEUTRAL", overall_score: 0 });
  
  // Fake chart data for now since we don't have historical index API implemented, but we'd normally fetch it
  const [chartData, setChartData] = useState([]);
  const [chartLoading, setChartLoading] = useState(false);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      try {
        const [niftyRes, sentRes] = await Promise.allSettled([
          getNifty50(),
          getMarketSentiment()
        ]);
        
        if (niftyRes.status === 'fulfilled' && niftyRes.value) {
          if (niftyRes.value.index) setIndexData(niftyRes.value.index);
          if (niftyRes.value.stocks) setStocks(niftyRes.value.stocks);
        }
        
        if (sentRes.status === 'fulfilled' && sentRes.value) {
          setSentiment(sentRes.value);
        }
        
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    
    fetchData();
  }, []);

  async function fetchHistory(range) {
    setChartLoading(true);
    try {
      const apiPeriod = range.toLowerCase();
      const history = await getNiftyHistory(apiPeriod);
      setChartData(history || []);
    } catch (err) {
      console.error("Failed to fetch Nifty index history in Dashboard", err);
    } finally {
      setChartLoading(false);
    }
  }

  useEffect(() => {
    fetchHistory(timeRange);
  }, [timeRange]);

  const topMovers = stocks
    .sort((a, b) => Math.abs(b.change_pct || 0) - Math.abs(a.change_pct || 0))
    .slice(0, 5);

  const isMarketUp = (indexData.change_pct || 0) >= 0;

  return (
    <div className="flex flex-col gap-5 pb-10">
      
      {/* Top Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        <StatCard 
          label="NIFTY 50" 
          value={indexData.value} 
          change={indexData.change_pct} 
          isPositive={isMarketUp} 
          prefix="₹" 
          loading={loading}
        />
        <StatCard 
          label="INDEX CHANGE" 
          value={indexData.change} 
          isPositive={isMarketUp} 
          prefix={isMarketUp ? "+₹" : "-₹"} 
          loading={loading}
        />
        <StatCard 
          label="Market Sentiment" 
          value={sentiment.overall_label || "NEUTRAL"} 
          loading={loading}
        />
        <StatCard 
          label="Active Stocks" 
          value={stocks.length || 50} 
          loading={loading}
        />
      </div>

      {/* Main Chart */}
      <Card className="p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-semibold text-[#111111]">NIFTY 50 Overview</h2>
            <Badge variant={isMarketUp ? "success" : "danger"}>
              {isMarketUp ? "Market Up" : "Market Down"}
            </Badge>
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
          {loading || chartLoading ? (
            <div className="w-full h-full flex items-center justify-center">
              <Loader2 className="w-8 h-8 animate-spin text-[#E5E7EB]" />
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 0, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={isMarketUp ? "#22C55E" : "#EF4444"} stopOpacity={0.15}/>
                    <stop offset="95%" stopColor={isMarketUp ? "#22C55E" : "#EF4444"} stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#6B7280', strokeWidth: 1, strokeDasharray: '4 4' }} />
                <Area 
                  type="monotone" 
                  dataKey="value" 
                  stroke={isMarketUp ? "#22C55E" : "#EF4444"} 
                  strokeWidth={2}
                  fillOpacity={1} 
                  fill="url(#colorValue)" 
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
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
                <th className="px-6 py-4 font-medium text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E5E7EB]">
              {loading ? (
                <tr>
                  <td colSpan="4" className="px-6 py-8 text-center"><Loader2 className="w-6 h-6 animate-spin text-[#E5E7EB] mx-auto" /></td>
                </tr>
              ) : topMovers.length === 0 ? (
                <tr>
                  <td colSpan="4" className="px-6 py-8 text-center text-gray-500">No active movers found.</td>
                </tr>
              ) : topMovers.map((stock) => {
                const changePct = stock.change_pct || 0;
                return (
                  <tr key={stock.symbol} className="hover:bg-[#F7F8F5] transition-colors duration-150">
                    <td className="px-6 py-4 font-semibold text-[#111111]">{stock.symbol}</td>
                    <td className="px-6 py-4 font-bold tabular-nums">₹{stock.price.toFixed(2)}</td>
                    <td className={`px-6 py-4 font-semibold tabular-nums ${changePct >= 0 ? 'text-[#22C55E]' : 'text-[#EF4444]'}`}>
                      {changePct > 0 ? '+' : ''}{changePct.toFixed(2)}%
                    </td>
                    <td className="px-6 py-3 text-right">
                      <div className="flex justify-end gap-2">
                        <Button variant="outline" size="sm" className="w-[60px]" onClick={() => window.location.href='/portfolio'}>Sell</Button>
                        <Button variant="primary" size="sm" className="w-[60px]" onClick={() => window.location.href='/portfolio'}>Buy</Button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>
      
    </div>
  );
}
