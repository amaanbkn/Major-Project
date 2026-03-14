import { useState } from 'react'
import {
  TrendingUp, TrendingDown, Minus, Search, Loader2,
  ArrowUpRight, ArrowDownRight, BarChart3, Activity
} from 'lucide-react'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts'
import { getSignal, getRecommendation, getStockData } from '../api'

const POPULAR_STOCKS = [
  'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK',
  'HINDUNILVR', 'ITC', 'SBIN', 'BAJFINANCE', 'BHARTIARTL',
  'WIPRO', 'TATAMOTORS', 'MARUTI', 'SUNPHARMA', 'LT',
]

export default function StockCard() {
  const [symbol, setSymbol] = useState('')
  const [signalData, setSignalData] = useState(null)
  const [recommendation, setRecommendation] = useState(null)
  const [chartData, setChartData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleAnalyze(sym) {
    const target = sym || symbol.trim().toUpperCase()
    if (!target) return

    setLoading(true)
    setError('')
    setSignalData(null)
    setRecommendation(null)
    setChartData(null)

    try {
      const [signal, reco, stock] = await Promise.all([
        getSignal(target),
        getRecommendation(target),
        getStockData(target, '6mo'),
      ])
      setSignalData(signal)
      setRecommendation(reco)
      setChartData(stock)
    } catch (e) {
      setError(e.message || 'Failed to fetch signal data')
    }
    setLoading(false)
  }

  function getSignalColor(signal) {
    if (!signal) return 'text-[var(--text-muted)]'
    if (signal.includes('BUY')) return 'text-emerald-400'
    if (signal.includes('SELL')) return 'text-red-400'
    return 'text-amber-400'
  }

  function getSignalBg(signal) {
    if (!signal) return 'bg-[var(--bg-card)]'
    if (signal.includes('BUY')) return 'bg-emerald-500/10 border-emerald-500/20'
    if (signal.includes('SELL')) return 'bg-red-500/10 border-red-500/20'
    return 'bg-amber-500/10 border-amber-500/20'
  }

  function getSignalIcon(signal) {
    if (!signal) return <Minus className="w-5 h-5" />
    if (signal.includes('BUY')) return <TrendingUp className="w-5 h-5" />
    if (signal.includes('SELL')) return <TrendingDown className="w-5 h-5" />
    return <Minus className="w-5 h-5" />
  }

  return (
    <div className="p-4 md:p-6 space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">Technical Signals</h1>
        <p className="text-sm text-[var(--text-muted)]">
          RSI + 50/200-day MA crossover analysis powered by pandas-ta
        </p>
      </div>

      {/* Search */}
      <div className="glass-card p-5">
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)]" />
            <input
              id="signal-search"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
              placeholder="Enter stock symbol (e.g. RELIANCE, TCS, INFY)"
              className="input-field pl-10"
            />
          </div>
          <button
            id="signal-analyze-btn"
            onClick={() => handleAnalyze()}
            disabled={loading}
            className="btn-primary px-6"
          >
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Analyze'}
          </button>
        </div>

        {/* Quick picks */}
        <div className="mt-4">
          <p className="text-xs text-[var(--text-muted)] mb-2">Popular stocks:</p>
          <div className="flex flex-wrap gap-2">
            {POPULAR_STOCKS.map((s) => (
              <button
                key={s}
                onClick={() => { setSymbol(s); handleAnalyze(s) }}
                className="px-3 py-1 rounded-lg text-xs font-medium
                  bg-[var(--bg-card)] border border-[var(--border)]
                  text-[var(--text-secondary)] hover:text-indigo-400
                  hover:border-indigo-500/30 transition-all cursor-pointer"
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      </div>

      {error && (
        <div className="glass-card p-4 border-red-500/20 bg-red-500/5">
          <p className="text-sm text-red-400">{error}</p>
        </div>
      )}

      {/* Signal Results */}
      {signalData && signalData.status === 'success' && (
        <div className="space-y-6 animate-slideUp">
          {/* Signal Header */}
          <div className="glass-card p-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-bold text-[var(--text-primary)]">
                  {signalData.symbol}
                </h2>
                <p className="text-3xl font-bold text-[var(--text-primary)] mt-1">
                  ₹{signalData.current_price?.toLocaleString('en-IN')}
                </p>
              </div>
              <div className={`flex items-center gap-3 px-6 py-4 rounded-xl border ${getSignalBg(signalData.signal)}`}>
                <div className={getSignalColor(signalData.signal)}>
                  {getSignalIcon(signalData.signal)}
                </div>
                <div>
                  <p className={`text-2xl font-bold ${getSignalColor(signalData.signal)}`}>
                    {signalData.signal?.replace('_', ' ')}
                  </p>
                  <p className="text-xs text-[var(--text-muted)]">
                    Score: {signalData.signal_score}/3
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Indicators Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 stagger-children">
            <div className="glass-card p-4 text-center">
              <p className="text-xs text-[var(--text-muted)] uppercase tracking-wider mb-1">RSI (14)</p>
              <p className={`text-2xl font-bold ${
                signalData.indicators?.rsi?.value < 30 ? 'text-emerald-400' :
                signalData.indicators?.rsi?.value > 70 ? 'text-red-400' :
                'text-[var(--text-primary)]'
              }`}>
                {signalData.indicators?.rsi?.value || '—'}
              </p>
              <p className="text-xs text-[var(--text-muted)] mt-1">
                {signalData.indicators?.rsi?.signal || ''}
              </p>
            </div>

            <div className="glass-card p-4 text-center">
              <p className="text-xs text-[var(--text-muted)] uppercase tracking-wider mb-1">SMA 50</p>
              <p className="text-2xl font-bold text-[var(--text-primary)]">
                {signalData.indicators?.sma_50 ? `₹${signalData.indicators.sma_50}` : '—'}
              </p>
            </div>

            <div className="glass-card p-4 text-center">
              <p className="text-xs text-[var(--text-muted)] uppercase tracking-wider mb-1">SMA 200</p>
              <p className="text-2xl font-bold text-[var(--text-primary)]">
                {signalData.indicators?.sma_200 ? `₹${signalData.indicators.sma_200}` : '—'}
              </p>
            </div>

            <div className="glass-card p-4 text-center">
              <p className="text-xs text-[var(--text-muted)] uppercase tracking-wider mb-1">MA Crossover</p>
              <p className={`text-lg font-bold ${
                signalData.indicators?.ma_crossover === 'GOLDEN_CROSS' ? 'text-emerald-400' :
                signalData.indicators?.ma_crossover === 'DEATH_CROSS' ? 'text-red-400' :
                signalData.indicators?.ma_crossover === 'BULLISH' ? 'text-emerald-400' :
                signalData.indicators?.ma_crossover === 'BEARISH' ? 'text-red-400' :
                'text-[var(--text-primary)]'
              }`}>
                {signalData.indicators?.ma_crossover?.replace('_', ' ') || '—'}
              </p>
            </div>
          </div>

          {/* Analysis points */}
          <div className="glass-card p-5">
            <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-3">Analysis</h3>
            <div className="space-y-2">
              {signalData.analysis?.map((point, i) => (
                <div key={i} className="flex items-start gap-2">
                  <span className="text-indigo-400 mt-0.5">•</span>
                  <p className="text-sm text-[var(--text-secondary)]">{point}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Price Chart */}
          {chartData?.history?.length > 0 && (
            <div className="glass-card p-5">
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
                Price History (6 Months)
              </h3>
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData.history}>
                    <defs>
                      <linearGradient id="signalGrad" x1="0" y1="0" x2="0" y2="1">
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
                    />
                    <Area type="monotone" dataKey="close" stroke="#6366f1" strokeWidth={2} fill="url(#signalGrad)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Recommendation */}
          {recommendation && (
            <div className="glass-card p-5">
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
                Combined Recommendation
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className={`p-4 rounded-xl border text-center ${getSignalBg(recommendation.recommendation)}`}>
                  <p className="text-xs text-[var(--text-muted)] mb-1">Recommendation</p>
                  <p className={`text-xl font-bold ${getSignalColor(recommendation.recommendation)}`}>
                    {recommendation.recommendation?.replace('_', ' ')}
                  </p>
                </div>
                <div className="glass-card p-4 text-center">
                  <p className="text-xs text-[var(--text-muted)] mb-1">Confidence</p>
                  <p className="text-xl font-bold text-indigo-400">{recommendation.confidence}%</p>
                </div>
                <div className="glass-card p-4 text-center">
                  <p className="text-xs text-[var(--text-muted)] mb-1">Composite Score</p>
                  <p className="text-xl font-bold text-[var(--text-primary)]">{recommendation.composite_score}</p>
                </div>
              </div>
              <div className="mt-4 space-y-1">
                {recommendation.reasoning?.map((r, i) => (
                  <p key={i} className="text-sm text-[var(--text-secondary)]">• {r}</p>
                ))}
              </div>
              <p className="text-xs text-[var(--text-muted)] mt-4 italic">{recommendation.disclaimer}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
