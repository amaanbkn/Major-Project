import { useState, useEffect } from 'react'
import {
  Briefcase, TrendingUp, TrendingDown, Plus, Minus,
  RefreshCw, Loader2, ArrowUpRight, ArrowDownRight,
  Wallet, History, RotateCcw, IndianRupee
} from 'lucide-react'
import { getPortfolio, buyStock, sellStock, getTransactions, resetPortfolio } from '../api'

export default function Portfolio() {
  const [portfolio, setPortfolio] = useState(null)
  const [transactions, setTransactions] = useState([])
  const [loading, setLoading] = useState(true)
  const [tradeLoading, setTradeLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('portfolio')
  const [tradeSymbol, setTradeSymbol] = useState('')
  const [tradeQty, setTradeQty] = useState(1)
  const [tradeResult, setTradeResult] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    setLoading(true)
    try {
      const [p, t] = await Promise.all([
        getPortfolio().catch(() => null),
        getTransactions().catch(() => ({ transactions: [] })),
      ])
      setPortfolio(p)
      setTransactions(t.transactions || [])
    } catch (e) {
      console.error('Portfolio load error:', e)
    }
    setLoading(false)
  }

  async function handleBuy() {
    if (!tradeSymbol.trim() || tradeQty <= 0) return
    setTradeLoading(true)
    setError('')
    setTradeResult(null)
    try {
      const result = await buyStock(tradeSymbol, tradeQty)
      setTradeResult(result)
      await loadData()
    } catch (e) {
      setError(e.message)
    }
    setTradeLoading(false)
  }

  async function handleSell() {
    if (!tradeSymbol.trim() || tradeQty <= 0) return
    setTradeLoading(true)
    setError('')
    setTradeResult(null)
    try {
      const result = await sellStock(tradeSymbol, tradeQty)
      setTradeResult(result)
      await loadData()
    } catch (e) {
      setError(e.message)
    }
    setTradeLoading(false)
  }

  async function handleReset() {
    if (!confirm('Reset portfolio to ₹1,00,000? All holdings and history will be cleared.')) return
    try {
      await resetPortfolio()
      await loadData()
      setTradeResult({ status: 'success', message: 'Portfolio reset to ₹1,00,000' })
    } catch (e) {
      setError(e.message)
    }
  }

  const totalPnL = portfolio?.holdings?.reduce((sum, h) => sum + (h.pnl || 0), 0) || 0
  const totalCurrent = portfolio?.holdings?.reduce((sum, h) => sum + (h.current_value || 0), 0) || 0

  return (
    <div className="p-4 md:p-6 space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">Paper Trading</h1>
          <p className="text-sm text-[var(--text-muted)]">
            Virtual portfolio simulation with ₹1,00,000 starting balance
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={loadData} className="btn-ghost" disabled={loading}>
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button onClick={handleReset} className="btn-ghost text-red-400 border-red-500/20 hover:bg-red-500/10">
            <RotateCcw className="w-4 h-4" />
            Reset
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 stagger-children">
        <div className="glass-card p-5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-[var(--text-muted)] uppercase tracking-wider">Cash Balance</span>
            <Wallet className="w-4 h-4 text-indigo-400" />
          </div>
          <p className="text-2xl font-bold text-[var(--text-primary)]">
            ₹{portfolio?.balance?.toLocaleString('en-IN') || '1,00,000'}
          </p>
        </div>

        <div className="glass-card p-5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-[var(--text-muted)] uppercase tracking-wider">Invested</span>
            <Briefcase className="w-4 h-4 text-indigo-400" />
          </div>
          <p className="text-2xl font-bold text-[var(--text-primary)]">
            ₹{portfolio?.total_invested?.toLocaleString('en-IN') || '0'}
          </p>
        </div>

        <div className="glass-card p-5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-[var(--text-muted)] uppercase tracking-wider">Current Value</span>
            <TrendingUp className="w-4 h-4 text-indigo-400" />
          </div>
          <p className="text-2xl font-bold text-[var(--text-primary)]">
            ₹{totalCurrent?.toLocaleString('en-IN') || '0'}
          </p>
        </div>

        <div className="glass-card p-5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-[var(--text-muted)] uppercase tracking-wider">Total P&L</span>
            {totalPnL >= 0 ? (
              <ArrowUpRight className="w-4 h-4 text-emerald-400" />
            ) : (
              <ArrowDownRight className="w-4 h-4 text-red-400" />
            )}
          </div>
          <p className={`text-2xl font-bold ${totalPnL >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
            {totalPnL >= 0 ? '+' : ''}₹{totalPnL?.toLocaleString('en-IN', { maximumFractionDigits: 2 }) || '0'}
          </p>
        </div>
      </div>

      {/* Trade Form */}
      <div className="glass-card p-5">
        <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">Execute Trade</h3>
        <div className="flex flex-col md:flex-row gap-3">
          <div className="flex-1">
            <input
              id="trade-symbol"
              value={tradeSymbol}
              onChange={(e) => setTradeSymbol(e.target.value.toUpperCase())}
              placeholder="Stock symbol (e.g. RELIANCE)"
              className="input-field"
            />
          </div>
          <div className="w-32">
            <input
              id="trade-quantity"
              type="number"
              value={tradeQty}
              onChange={(e) => setTradeQty(Number(e.target.value))}
              placeholder="Qty"
              className="input-field"
              min="1"
            />
          </div>
          <button
            id="trade-buy-btn"
            onClick={handleBuy}
            disabled={tradeLoading || !tradeSymbol}
            className="btn-primary bg-gradient-to-r from-emerald-500 to-teal-600 px-6"
          >
            {tradeLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
            Buy
          </button>
          <button
            id="trade-sell-btn"
            onClick={handleSell}
            disabled={tradeLoading || !tradeSymbol}
            className="btn-primary bg-gradient-to-r from-red-500 to-rose-600 px-6"
          >
            {tradeLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Minus className="w-4 h-4" />}
            Sell
          </button>
        </div>

        {error && (
          <div className="mt-3 p-3 rounded-lg bg-red-500/5 border border-red-500/20">
            <p className="text-sm text-red-400">{error}</p>
          </div>
        )}

        {tradeResult && tradeResult.status === 'success' && (
          <div className="mt-3 p-3 rounded-lg bg-emerald-500/5 border border-emerald-500/20">
            <p className="text-sm text-emerald-400">{tradeResult.message}</p>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 p-1 rounded-xl bg-[var(--bg-card)] w-fit">
        <button
          onClick={() => setActiveTab('portfolio')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all
            ${activeTab === 'portfolio'
              ? 'bg-indigo-500/20 text-indigo-400'
              : 'text-[var(--text-muted)] hover:text-white'
            }
          `}
        >
          <Briefcase className="w-4 h-4 inline mr-2" />
          Holdings
        </button>
        <button
          onClick={() => setActiveTab('transactions')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all
            ${activeTab === 'transactions'
              ? 'bg-indigo-500/20 text-indigo-400'
              : 'text-[var(--text-muted)] hover:text-white'
            }
          `}
        >
          <History className="w-4 h-4 inline mr-2" />
          Transactions
        </button>
      </div>

      {/* Holdings Table */}
      {activeTab === 'portfolio' && (
        <div className="glass-card overflow-hidden">
          {portfolio?.holdings?.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-[var(--text-muted)] border-b border-[var(--border)] bg-[var(--bg-card)]">
                    <th className="text-left py-3 px-4 font-medium">Symbol</th>
                    <th className="text-right py-3 px-4 font-medium">Qty</th>
                    <th className="text-right py-3 px-4 font-medium">Buy Price</th>
                    <th className="text-right py-3 px-4 font-medium">Current</th>
                    <th className="text-right py-3 px-4 font-medium">Invested</th>
                    <th className="text-right py-3 px-4 font-medium">Current Value</th>
                    <th className="text-right py-3 px-4 font-medium">P&L</th>
                    <th className="text-right py-3 px-4 font-medium">P&L %</th>
                  </tr>
                </thead>
                <tbody>
                  {portfolio.holdings.map((h, i) => (
                    <tr key={i} className="border-b border-[var(--border)]/50 hover:bg-[var(--bg-card)] transition-colors">
                      <td className="py-3 px-4 font-semibold text-[var(--text-primary)]">{h.symbol}</td>
                      <td className="py-3 px-4 text-right text-[var(--text-secondary)]">{h.quantity}</td>
                      <td className="py-3 px-4 text-right text-[var(--text-secondary)]">₹{h.buy_price?.toLocaleString('en-IN')}</td>
                      <td className="py-3 px-4 text-right text-[var(--text-primary)]">
                        {h.current_price ? `₹${h.current_price.toLocaleString('en-IN')}` : '—'}
                      </td>
                      <td className="py-3 px-4 text-right text-[var(--text-secondary)]">₹{h.invested_value?.toLocaleString('en-IN')}</td>
                      <td className="py-3 px-4 text-right text-[var(--text-primary)]">
                        {h.current_value ? `₹${h.current_value.toLocaleString('en-IN')}` : '—'}
                      </td>
                      <td className={`py-3 px-4 text-right font-semibold ${(h.pnl || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {h.pnl != null ? `${h.pnl >= 0 ? '+' : ''}₹${h.pnl.toLocaleString('en-IN')}` : '—'}
                      </td>
                      <td className={`py-3 px-4 text-right font-semibold ${(h.pnl_pct || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {h.pnl_pct != null ? `${h.pnl_pct >= 0 ? '+' : ''}${h.pnl_pct}%` : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="py-16 text-center">
              <Briefcase className="w-12 h-12 text-[var(--text-muted)] mx-auto mb-3" />
              <p className="text-[var(--text-muted)]">No holdings yet</p>
              <p className="text-xs text-[var(--text-muted)] mt-1">Start trading to build your portfolio</p>
            </div>
          )}
        </div>
      )}

      {/* Transactions Table */}
      {activeTab === 'transactions' && (
        <div className="glass-card overflow-hidden">
          {transactions.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-[var(--text-muted)] border-b border-[var(--border)] bg-[var(--bg-card)]">
                    <th className="text-left py-3 px-4 font-medium">Time</th>
                    <th className="text-left py-3 px-4 font-medium">Action</th>
                    <th className="text-left py-3 px-4 font-medium">Symbol</th>
                    <th className="text-right py-3 px-4 font-medium">Qty</th>
                    <th className="text-right py-3 px-4 font-medium">Price</th>
                    <th className="text-right py-3 px-4 font-medium">Total</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.map((t, i) => (
                    <tr key={i} className="border-b border-[var(--border)]/50 hover:bg-[var(--bg-card)] transition-colors">
                      <td className="py-3 px-4 text-[var(--text-muted)] text-xs">
                        {new Date(t.timestamp).toLocaleString('en-IN')}
                      </td>
                      <td className="py-3 px-4">
                        <span className={`badge ${t.action === 'BUY' ? 'badge-buy' : 'badge-sell'}`}>
                          {t.action}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-semibold text-[var(--text-primary)]">{t.symbol}</td>
                      <td className="py-3 px-4 text-right text-[var(--text-secondary)]">{t.quantity}</td>
                      <td className="py-3 px-4 text-right text-[var(--text-secondary)]">₹{t.price?.toLocaleString('en-IN')}</td>
                      <td className="py-3 px-4 text-right font-semibold text-[var(--text-primary)]">
                        ₹{t.total?.toLocaleString('en-IN')}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="py-16 text-center">
              <History className="w-12 h-12 text-[var(--text-muted)] mx-auto mb-3" />
              <p className="text-[var(--text-muted)]">No transactions yet</p>
            </div>
          )}
        </div>
      )}

      <p className="text-xs text-[var(--text-muted)] text-center italic">
        Paper trading simulation only. No real money is involved.
      </p>
    </div>
  )
}
