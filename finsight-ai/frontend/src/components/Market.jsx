import React, { useState, useEffect } from 'react';
import { Card } from './ui/Card';
import { Badge } from './ui/Badge';
import { Button } from './ui/Button';
import { useCountUp } from '../hooks/useCountUp';
import { ArrowUpRight, ArrowDownRight, Loader2, Activity, TrendingUp, TrendingDown, RefreshCw } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { getNifty50, getMarketSentiment, getNiftyHistory } from '../api';



function getSentimentColor(label) {
  if (!label) return '#6B7280';
  const l = label.toUpperCase();
  if (l.includes('BULL') || l.includes('POSITIVE')) return '#22C55E';
  if (l.includes('BEAR') || l.includes('NEGATIVE')) return '#EF4444';
  return '#F59E0B';
}

function getSentimentVariant(label) {
  if (!label) return 'neutral';
  const l = label.toUpperCase();
  if (l.includes('BULL') || l.includes('POSITIVE')) return 'success';
  if (l.includes('BEAR') || l.includes('NEGATIVE')) return 'danger';
  return 'neutral';
}

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

export default function Market() {
  const [indexData, setIndexData] = useState({ value: null, change: null, change_pct: null });
  const [stocks, setStocks] = useState([]);
  const [sentiment, setSentiment] = useState({ overall_score: 0, overall_label: 'NEUTRAL', sources: {} });
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [chartLoading, setChartLoading] = useState(false);
  const [timeRange, setTimeRange] = useState('1D');
  const [error, setError] = useState(null);

  const niftyValue = useCountUp(indexData.value || 0);

  async function fetchData() {
    setLoading(true);
    setError(null);
    try {
      const [niftyRes, sentRes] = await Promise.allSettled([
        getNifty50(),
        getMarketSentiment(),
      ]);

      if (niftyRes.status === 'fulfilled' && niftyRes.value) {
        const idx = niftyRes.value.index;
        if (idx && (idx.status === 'error' || idx.status === 'unavailable' || idx.value == null)) {
          setIndexData({ value: null, change: null, change_pct: null });
          setError(idx.error || 'NIFTY 50 data is unavailable.');
        } else if (idx) {
          setIndexData(idx);
        }
        if (niftyRes.value.stocks && niftyRes.value.stocks.length > 0) {
          setStocks(niftyRes.value.stocks);
        }
      } else if (niftyRes.status === 'rejected') {
        console.error("Nifty 50 API error", niftyRes.reason);
        setError("Nifty 50 data is temporarily unavailable.");
      }

      if (sentRes.status === 'fulfilled' && sentRes.value) {
        if (sentRes.value.status === 'error') {
          console.warn("Sentiment fetch warning:", sentRes.value.error);
        } else {
          setSentiment(sentRes.value);
        }
      } else if (sentRes.status === 'rejected') {
        console.error("Sentiment API error", sentRes.reason);
      }
    } catch {
      setError("Failed to load market data.");
    } finally {
      setLoading(false);
    }
  }

  async function fetchHistory(range) {
    setChartLoading(true);
    try {
      const apiPeriod = range.toLowerCase();
      const history = await getNiftyHistory(apiPeriod);
      setChartData(history || []);
    } catch (err) {
      console.error("Failed to fetch Nifty index history", err);
    } finally {
      setChartLoading(false);
    }
  }

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    fetchHistory(timeRange);
  }, [timeRange]);

  const gainers = [...stocks]
    .filter(s => (s.change_pct || s.changePct || 0) > 0)
    .sort((a, b) => (b.change_pct || b.changePct || 0) - (a.change_pct || a.changePct || 0))
    .slice(0, 5);

  const losers = [...stocks]
    .filter(s => (s.change_pct || s.changePct || 0) < 0)
    .sort((a, b) => (a.change_pct || a.changePct || 0) - (b.change_pct || b.changePct || 0))
    .slice(0, 5);

  const changePct = indexData.change_pct || indexData.changePct || 0;
  const isPositive = changePct >= 0;
  const sentimentLabel = sentiment.overall_label || 'NEUTRAL';
  const sentimentScore = sentiment.overall_score || 0;

  return (
    <div className="flex flex-col gap-5 pb-10">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-[28px] font-bold text-[#111111] leading-tight">Market Overview</h1>
          <p className="text-[#6B7280] text-sm mt-1">
            NIFTY 50 index, top movers & market sentiment
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchData}>
          <RefreshCw className={`w-4 h-4 mr-1.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-[12px] text-sm">
          {error}
        </div>
      )}

      {/* Top Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        <Card className="px-5 py-5 border-[#E5E7EB]">
          <span className="text-[11px] font-medium uppercase tracking-[0.08em] text-[#6B7280]">NIFTY 50</span>
          <div className="flex items-end justify-between mt-1">
            <span className="text-[28px] font-bold tabular-nums text-[#111111] leading-none">
              {indexData.value == null ? 'Unavailable' : `₹${niftyValue.toLocaleString()}`}
            </span>
            <div className={`flex items-center gap-0.5 px-2 py-1 rounded-[6px] ${
              isPositive ? 'bg-[#22C55E]/10 text-[#22C55E]' : 'bg-[#EF4444]/10 text-[#EF4444]'
            }`}>
              {isPositive ? <ArrowUpRight className="w-3.5 h-3.5" /> : <ArrowDownRight className="w-3.5 h-3.5" />}
              <span className="text-[13px] font-semibold">{Math.abs(changePct)}%</span>
            </div>
          </div>
        </Card>

        <Card className="px-5 py-5 border-[#E5E7EB]">
          <span className="text-[11px] font-medium uppercase tracking-[0.08em] text-[#6B7280]">Change</span>
          <div className="flex items-end justify-between mt-1">
            <span className={`text-[28px] font-bold tabular-nums leading-none ${
              isPositive ? 'text-[#22C55E]' : 'text-[#EF4444]'
            }`}>
              {isPositive ? '+' : ''}₹{(indexData.change || 0).toLocaleString('en-IN', { maximumFractionDigits: 1 })}
            </span>
          </div>
        </Card>

        <Card className="px-5 py-5 border-[#E5E7EB]">
          <span className="text-[11px] font-medium uppercase tracking-[0.08em] text-[#6B7280]">Market Sentiment</span>
          <div className="flex items-end justify-between mt-1">
            <span className="text-[28px] font-bold leading-none" style={{ color: getSentimentColor(sentimentLabel) }}>
              {sentimentLabel}
            </span>
            <Badge variant={getSentimentVariant(sentimentLabel)}>
              {(sentimentScore * 100).toFixed(0)}%
            </Badge>
          </div>
        </Card>

        <Card className="px-5 py-5 border-[#E5E7EB]">
          <span className="text-[11px] font-medium uppercase tracking-[0.08em] text-[#6B7280]">Active Stocks</span>
          <div className="flex items-end justify-between mt-1">
            <span className="text-[28px] font-bold tabular-nums text-[#111111] leading-none">
              {stocks.length}
            </span>
            <div className="flex items-center gap-2 text-xs text-[#6B7280]">
              <span className="text-[#22C55E] font-semibold">{stocks.filter(s => (s.change_pct || 0) > 0).length}↑</span>
              <span className="text-[#EF4444] font-semibold">{stocks.filter(s => (s.change_pct || 0) < 0).length}↓</span>
            </div>
          </div>
        </Card>
      </div>

      {/* NIFTY 50 Chart */}
      <Card className="p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-semibold text-[#111111]">NIFTY 50 Intraday</h2>
            <Badge variant={isPositive ? 'success' : 'danger'}>
              {isPositive ? 'Market Up' : 'Market Down'}
            </Badge>
          </div>
          <div className="flex items-center gap-2">
            {['1D', '7D', '1M', '3M', '1Y'].map(range => (
              <button
                key={range}
                onClick={() => setTimeRange(range)}
                className={`px-3 py-1 text-xs font-semibold rounded-full transition-colors cursor-pointer ${
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
        <div className="h-[300px] w-full relative">
          {chartLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-white/50 backdrop-blur-sm z-10 rounded-[8px]">
              <Loader2 className="w-8 h-8 animate-spin text-[#111111]" />
            </div>
          )}
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 10, right: 0, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={isPositive ? '#22C55E' : '#EF4444'} stopOpacity={0.15} />
                  <stop offset="95%" stopColor={isPositive ? '#22C55E' : '#EF4444'} stopOpacity={0} />
                </linearGradient>
              </defs>
              <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#6B7280', strokeWidth: 1, strokeDasharray: '4 4' }} />
              <Area
                type="monotone"
                dataKey="value"
                stroke={isPositive ? '#22C55E' : '#EF4444'}
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#chartGradient)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {/* Sentiment Breakdown */}
      <Card className="p-6">
        <h2 className="text-lg font-semibold text-[#111111] mb-4">Sentiment Sources</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Object.entries(sentiment.sources || {}).map(([name, data]) => {
            const score = data?.score || 0;
            const weight = data?.weight || 0;
            const label = score > 0.15 ? 'Bullish' : score < -0.15 ? 'Bearish' : 'Neutral';
            const color = score > 0.15 ? '#22C55E' : score < -0.15 ? '#EF4444' : '#F59E0B';

            return (
              <div key={name} className="p-4 rounded-[12px] border border-[#E5E7EB]">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-semibold text-[#111111] capitalize">
                    {name.replace(/_/g, ' ')}
                  </span>
                  <span className="text-xs text-[#6B7280]">Weight: {(weight * 100).toFixed(0)}%</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex-1 h-2 bg-[#F3F4F6] rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{
                        width: `${Math.max(10, (Math.abs(score) * 100))}%`,
                        backgroundColor: color,
                      }}
                    />
                  </div>
                  <span className="text-sm font-bold tabular-nums" style={{ color }}>
                    {label}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </Card>

      {/* Gainers & Losers */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Top Gainers */}
        <Card className="p-0 overflow-hidden">
          <div className="px-6 py-5 border-b border-[#E5E7EB] flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-[#22C55E]" />
            <h2 className="text-lg font-semibold text-[#111111]">Top Gainers</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-[11px] uppercase tracking-[0.08em] text-[#6B7280] bg-[#F7F8F5]">
                <tr>
                  <th className="px-6 py-3 font-medium">Stock</th>
                  <th className="px-6 py-3 font-medium">Price</th>
                  <th className="px-6 py-3 font-medium text-right">Change</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E5E7EB]">
                {gainers.map(stock => (
                  <tr key={stock.symbol} className="hover:bg-[#F7F8F5] transition-colors duration-150">
                    <td className="px-6 py-3.5 font-semibold text-[#111111]">{stock.symbol}</td>
                    <td className="px-6 py-3.5 tabular-nums font-bold text-[#111111]">
                      ₹{(stock.price || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="px-6 py-3.5 text-right">
                      <span className="text-[#22C55E] font-semibold tabular-nums">
                        +{(stock.change_pct || stock.changePct || 0).toFixed(2)}%
                      </span>
                    </td>
                  </tr>
                ))}
                {gainers.length === 0 && (
                  <tr><td colSpan={3} className="px-6 py-8 text-center text-[#6B7280]">No gainers today</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>

        {/* Top Losers */}
        <Card className="p-0 overflow-hidden">
          <div className="px-6 py-5 border-b border-[#E5E7EB] flex items-center gap-2">
            <TrendingDown className="w-5 h-5 text-[#EF4444]" />
            <h2 className="text-lg font-semibold text-[#111111]">Top Losers</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-[11px] uppercase tracking-[0.08em] text-[#6B7280] bg-[#F7F8F5]">
                <tr>
                  <th className="px-6 py-3 font-medium">Stock</th>
                  <th className="px-6 py-3 font-medium">Price</th>
                  <th className="px-6 py-3 font-medium text-right">Change</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E5E7EB]">
                {losers.map(stock => (
                  <tr key={stock.symbol} className="hover:bg-[#F7F8F5] transition-colors duration-150">
                    <td className="px-6 py-3.5 font-semibold text-[#111111]">{stock.symbol}</td>
                    <td className="px-6 py-3.5 tabular-nums font-bold text-[#111111]">
                      ₹{(stock.price || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="px-6 py-3.5 text-right">
                      <span className="text-[#EF4444] font-semibold tabular-nums">
                        {(stock.change_pct || stock.changePct || 0).toFixed(2)}%
                      </span>
                    </td>
                  </tr>
                ))}
                {losers.length === 0 && (
                  <tr><td colSpan={3} className="px-6 py-8 text-center text-[#6B7280]">No losers today</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </div>
  );
}
