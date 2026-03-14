import { useState, useEffect } from 'react'
import { Calendar, TrendingUp, Info, Loader2, RefreshCw, ExternalLink } from 'lucide-react'
import { getIPOs } from '../api'

export default function IPOTracker() {
  const [ipos, setIpos] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    loadIPOs()
  }, [])

  async function loadIPOs() {
    setLoading(true)
    setError('')
    try {
      const data = await getIPOs()
      setIpos(data.ipos || [])
    } catch (e) {
      setError(e.message || 'Failed to fetch IPO data')
    }
    setLoading(false)
  }

  function getGMPColor(gmp) {
    if (!gmp || gmp === 'N/A') return 'text-[var(--text-muted)]'
    if (gmp.includes('+') || gmp.includes('₹')) return 'text-emerald-400'
    if (gmp.includes('-')) return 'text-red-400'
    return 'text-[var(--text-secondary)]'
  }

  return (
    <div className="p-4 md:p-6 space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">IPO Tracker</h1>
          <p className="text-sm text-[var(--text-muted)]">
            Upcoming & current IPOs with Grey Market Premium data
          </p>
        </div>
        <button
          onClick={loadIPOs}
          className="btn-ghost"
          disabled={loading}
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Info Banner */}
      <div className="glass-card p-4 flex items-start gap-3 border-indigo-500/20">
        <Info className="w-5 h-5 text-indigo-400 flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-sm text-[var(--text-secondary)]">
            IPO data is sourced from investorgain.com and chittorgarh.com.
            GMP (Grey Market Premium) indicates the unofficial premium at which IPO shares
            are trading before listing.
          </p>
        </div>
      </div>

      {error && (
        <div className="glass-card p-4 border-red-500/20 bg-red-500/5">
          <p className="text-sm text-red-400">{error}</p>
        </div>
      )}

      {/* IPO Cards */}
      {loading ? (
        <div className="py-20 text-center text-[var(--text-muted)]">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-3" />
          <p>Fetching IPO data...</p>
        </div>
      ) : ipos.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 stagger-children">
          {ipos.map((ipo, i) => (
            <div key={i} className="glass-card p-5 hover:border-indigo-500/30 transition-all">
              <div className="flex items-start justify-between gap-3 mb-4">
                <h3 className="text-base font-semibold text-[var(--text-primary)] leading-tight">
                  {ipo.name}
                </h3>
                {ipo.gmp && ipo.gmp !== 'N/A' && (
                  <span className={`badge ${
                    ipo.gmp.includes('+') ? 'badge-buy' : ipo.gmp.includes('-') ? 'badge-sell' : 'badge-hold'
                  }`}>
                    GMP: {ipo.gmp}
                  </span>
                )}
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <p className="text-xs text-[var(--text-muted)]">Price Band</p>
                  <p className="text-sm font-medium text-[var(--text-primary)]">{ipo.price_band || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-xs text-[var(--text-muted)]">Lot Size</p>
                  <p className="text-sm font-medium text-[var(--text-primary)]">{ipo.lot_size || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-xs text-[var(--text-muted)]">Open Date</p>
                  <p className="text-sm font-medium text-[var(--text-primary)]">{ipo.open_date || 'TBA'}</p>
                </div>
                <div>
                  <p className="text-xs text-[var(--text-muted)]">Close Date</p>
                  <p className="text-sm font-medium text-[var(--text-primary)]">{ipo.close_date || 'TBA'}</p>
                </div>
              </div>

              {ipo.source && ipo.source !== 'demo' && (
                <div className="mt-3 pt-3 border-t border-[var(--border)]">
                  <span className="text-xs text-[var(--text-muted)]">
                    Source: {ipo.source}
                  </span>
                </div>
              )}

              {ipo.note && (
                <div className="mt-3 p-2 rounded-lg bg-amber-500/5 border border-amber-500/10">
                  <p className="text-xs text-amber-400">{ipo.note}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="glass-card py-20 text-center">
          <Calendar className="w-12 h-12 text-[var(--text-muted)] mx-auto mb-3" />
          <p className="text-[var(--text-muted)]">No upcoming IPOs found</p>
          <p className="text-xs text-[var(--text-muted)] mt-1">Check back later for new listings</p>
        </div>
      )}

      {/* Disclaimer */}
      <div className="text-center">
        <p className="text-xs text-[var(--text-muted)] italic">
          GMP data is unofficial and indicative only. IPO investment carries risk.
          Please read the DRHP and consult a financial advisor before investing.
        </p>
      </div>
    </div>
  )
}
