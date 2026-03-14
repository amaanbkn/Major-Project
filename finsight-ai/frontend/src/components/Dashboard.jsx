import { useState, useEffect } from 'react'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell
} from 'recharts'
import {
  TrendingUp, TrendingDown, BarChart3, Activity,
  RefreshCw, Search, Loader2, ArrowUpRight, ArrowDownRight
} from 'lucide-react'
import { getNifty50, getMarketSentiment, getStockData } from '../api'

const CHART_COLORS = ['#6366f1', '#06d6a0', '#f59e0b', '#ef4444', '#8b5cf6', '#3b82f6']

export default function Dashboard() {
  const [niftyData, setNiftyData] = useState(null)
  const [sentiment, setSentiment] = useState(null)
  const [selectedStock, setSelectedStock] = useState('RELIANCE')
  const [stockData, setStockData] = useState(null)
  const [searchInput, setSearchInput] = useState('')
  const [loading, setLoading] = useState(true)
  const [chartPeriod, setChartPeriod] = useState('6mo')

  useEffect(() => {
    loadDashboard()
  }, [])

  useEffect(() => {
    loadStockChart()
  }, [selectedStock, chartPeriod])

  async function loadDashboard() {
    setLoading(true)
    try {
      const [nifty, sent] = await Promise.all([
        getNifty50().catch(() => null),
        getMarketSentiment().catch(() => null),
      ])
      setNiftyData(nifty)
      setSentiment(sent)
    } catch (e) {
      console.error('Dashboard load error:', e)
    }
    setLoading(false)
  }

  async function loadStockChart() {
    try {
      const data = await getStockData(selectedStock, chartPeriod)
      setStockData(data)
    } catch (e) {
      console.error('Stock chart error:', e)
    }
  }

  function handleSearch(e) {
    e.preventDefault()
    if (searchInput.trim()) {
      setSelectedStock(searchInput.trim().toUpperCase())
      setSearchInput('')
    }
  }

  const sentimentPieData = sentiment ? [
    { name: 'ET', value: 40, score: sentiment.sources?.economic_times?.score || 0 },
    { name: 'MC', value: 40, score: sentiment.sources?.moneycontrol?.score || 0 },
    { name: 'Reddit', value: 20, score: sentiment.sources?.reddit?.score || 0 },
  ] : []

  const periods = [
    { label: '1M', value: '1mo' },
    { label: '3M', value: '3mo' },
    { label: '6M', value: '6mo' },
    { label: '1Y', value: '1y' },
    { label: '2Y', value: '2y' },
  ]

  return (
    <div className="p-4 md:p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">Market Dashboard</h1>
          <p className="text-sm text-[var(--text-muted)]">Real-time market overview powered by yfinance</p>
        </div>
        <div className="flex items-center gap-3">
          <form onSubmit={handleSearch} className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)]" />
            <input
              id="stock-search"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search stock (e.g. TCS)"
              className="input-field pl-10 w-48 md:w-64"
            />
          </form>
          <button
            onClick={loadDashboard}
            className="btn-ghost p-3"
            title="Refresh data"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Top cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 stagger-children">
        {/* NIFTY 50 Index */}
        <div className="glass-card p-5">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs text-[var(--text-muted)] font-medium uppercase tracking-wider">NIFTY 50</span>
            <Activity className="w-4 h-4 text-indigo-400" />
          </div>
          <p className="text-2xl font-bold text-[var(--text-primary)]">
            {niftyData?.index?.value?.toLocaleString('en-IN') || '—'}
          </p>
          <div className="flex items-center gap-1 mt-1">
            {(niftyData?.index?.change || 0) >= 0 ? (
              <ArrowUpRight className="w-4 h-4 text-emerald-400" />
            ) : (
              <ArrowDownRight className="w-4 h-4 text-red-400" />
            )}
            <span className={`text-sm font-semibold ${(niftyData?.index?.change || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
              {niftyData?.index?.change || 0} ({niftyData?.index?.change_pct || 0}%)
            </span>
          </div>
        </div>

        {/* Sentiment */}
        <div className="glass-card p-5">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs text-[var(--text-muted)] font-medium uppercase tracking-wider">Sentiment</span>
            <BarChart3 className="w-4 h-4 text-indigo-400" />
          </div>
          <p className="text-2xl font-bold text-[var(--text-primary)]">
            {sentiment?.overall_label || '—'}
          </p>
          <p className="text-sm text-[var(--text-muted)] mt-1">
            Score: {sentiment?.overall_score || '—'}
          </p>
        </div>

        {/* Selected Stock */}
        <div className="glass-card p-5">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs text-[var(--text-muted)] font-medium uppercase tracking-wider">{selectedStock}</span>
            <TrendingUp className="w-4 h-4 text-indigo-400" />
          </div>
          <p className="text-2xl font-bold text-[var(--text-primary)]">
            ₹{stockData?.price?.price?.toLocaleString('en-IN') || '—'}
          </p>
          <div className="flex items-center gap-1 mt-1">
            {(stockData?.price?.change || 0) >= 0 ? (
              <ArrowUpRight className="w-4 h-4 text-emerald-400" />
            ) : (
              <ArrowDownRight className="w-4 h-4 text-red-400" />
            )}
            <span className={`text-sm font-semibold ${(stockData?.price?.change || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
              {stockData?.price?.change || 0} ({stockData?.price?.change_pct || 0}%)
            </span>
          </div>
        </div>

        {/* Market Cap */}
        <div className="glass-card p-5">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs text-[var(--text-muted)] font-medium uppercase tracking-wider">Market Cap</span>
            <BarChart3 className="w-4 h-4 text-indigo-400" />
          </div>
          <p className="text-2xl font-bold text-[var(--text-primary)]">
            {stockData?.price?.market_cap
              ? `₹${(stockData.price.market_cap / 10000000).toFixed(0)} Cr`
              : '—'
            }
          </p>
          <p className="text-sm text-[var(--text-muted)] mt-1">
            PE: {stockData?.price?.pe_ratio?.toFixed(1) || '—'}
          </p>
        </div>
      </div>

      {/* Stock Chart + Sentiment Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Price Chart */}
        <div className="lg:col-span-2 glass-card p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-[var(--text-primary)]">
              {selectedStock} Price Chart
            </h3>
            <div className="flex gap-1">
              {periods.map(p => (
                <button
                  key={p.value}
                  onClick={() => setChartPeriod(p.value)}
                  className={`px-3 py-1 rounded-lg text-xs font-medium transition-all
                    ${chartPeriod === p.value
                      ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30'
                      : 'text-[var(--text-muted)] hover:text-white hover:bg-[var(--bg-card)]'
                    }
                  `}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>
          <div className="h-[300px]">
            {stockData?.history?.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={stockData.history}>
                  <defs>
                    <linearGradient id="colorClose" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.08)" />
                  <XAxis
                    dataKey="date"
                    tick={{ fill: '#64748b', fontSize: 11 }}
                    tickFormatter={(v) => new Date(v).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })}
                    interval="preserveStartEnd"
                  />
                  <YAxis tick={{ fill: '#64748b', fontSize: 11 }} domain={['auto', 'auto']} />
                  <Tooltip
                    contentStyle={{
                      background: '#16163a',
                      border: '1px solid rgba(99,102,241,0.2)',
                      borderRadius: '8px',
                      color: '#f1f5f9',
                    }}
                    formatter={(v) => [`₹${v.toFixed(2)}`, 'Close']}
                    labelFormatter={(v) => new Date(v).toLocaleDateString('en-IN', { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' })}
                  />
                  <Area
                    type="monotone"
                    dataKey="close"
                    stroke="#6366f1"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#colorClose)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-[var(--text-muted)]">
                <Loader2 className="w-6 h-6 animate-spin mr-2" /> Loading chart...
              </div>
            )}
          </div>
        </div>

        {/* Sentiment breakdown */}
        <div className="glass-card p-5">
          <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">Sentiment Sources</h3>
          {sentiment ? (
            <>
              <div className="h-[180px]">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={sentimentPieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={70}
                      dataKey="value"
                      stroke="none"
                    >
                      {sentimentPieData.map((entry, index) => (
                        <Cell key={index} fill={CHART_COLORS[index]} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        background: '#16163a',
                        border: '1px solid rgba(99,102,241,0.2)',
                        borderRadius: '8px',
                        color: '#f1f5f9',
                      }}
                      formatter={(v, n, p) => [`${v}%`, p.payload.name]}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="space-y-3 mt-2">
                {sentimentPieData.map((s, i) => (
                  <div key={i} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="w-3 h-3 rounded-full" style={{ background: CHART_COLORS[i] }} />
                      <span className="text-sm text-[var(--text-secondary)]">{s.name}</span>
                    </div>
                    <span className={`text-sm font-semibold ${s.score > 0 ? 'text-emerald-400' : s.score < 0 ? 'text-red-400' : 'text-[var(--text-muted)]'}`}>
                      {s.score > 0 ? '+' : ''}{s.score}
                    </span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="h-[250px] flex items-center justify-center text-[var(--text-muted)]">
              <Loader2 className="w-6 h-6 animate-spin mr-2" /> Loading...
            </div>
          )}
        </div>
      </div>

      {/* NIFTY 50 Stock Table */}
      <div className="glass-card p-5">
        <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">NIFTY 50 Stocks</h3>
        {niftyData?.stocks?.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-[var(--text-muted)] border-b border-[var(--border)]">
                  <th className="text-left py-3 px-4 font-medium">Symbol</th>
                  <th className="text-right py-3 px-4 font-medium">Price</th>
                  <th className="text-right py-3 px-4 font-medium">Change</th>
                  <th className="text-right py-3 px-4 font-medium">Change %</th>
                </tr>
              </thead>
              <tbody>
                {niftyData.stocks.map((stock, i) => (
                  <tr
                    key={i}
                    className="border-b border-[var(--border)]/50 hover:bg-[var(--bg-card)] cursor-pointer transition-colors"
                    onClick={() => setSelectedStock(stock.symbol)}
                  >
                    <td className="py-3 px-4 font-medium text-[var(--text-primary)]">{stock.symbol}</td>
                    <td className="py-3 px-4 text-right text-[var(--text-primary)]">
                      ₹{stock.price?.toLocaleString('en-IN')}
                    </td>
                    <td className={`py-3 px-4 text-right font-medium ${stock.change >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                      {stock.change >= 0 ? '+' : ''}{stock.change}
                    </td>
                    <td className={`py-3 px-4 text-right font-medium ${stock.change_pct >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                      {stock.change_pct >= 0 ? '+' : ''}{stock.change_pct}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-12 text-center text-[var(--text-muted)]">
            {loading ? (
              <><Loader2 className="w-6 h-6 animate-spin inline mr-2" /> Loading NIFTY 50 data...</>
            ) : (
              'No market data available. Start the backend to fetch live data.'
            )}
          </div>
        )}
      </div>
    </div>
  )
}
