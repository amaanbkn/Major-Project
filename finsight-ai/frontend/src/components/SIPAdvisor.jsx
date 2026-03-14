import { useState } from 'react'
import {
  PiggyBank, TrendingUp, Shield, Zap, Calculator,
  Loader2, ArrowRight, IndianRupee
} from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell
} from 'recharts'
import { getSIPRecommendation } from '../api'

const CHART_COLORS = ['#6366f1', '#06d6a0', '#f59e0b', '#8b5cf6', '#3b82f6']

const RISK_LEVELS = [
  {
    value: 'low',
    label: 'Conservative',
    icon: Shield,
    color: 'text-blue-400',
    bg: 'bg-blue-500/10 border-blue-500/20',
    desc: 'Debt-heavy portfolio, stable returns (~8% p.a.)',
  },
  {
    value: 'medium',
    label: 'Balanced',
    icon: TrendingUp,
    color: 'text-indigo-400',
    bg: 'bg-indigo-500/10 border-indigo-500/20',
    desc: 'Mix of equity & debt, moderate growth (~12% p.a.)',
  },
  {
    value: 'high',
    label: 'Aggressive',
    icon: Zap,
    color: 'text-amber-400',
    bg: 'bg-amber-500/10 border-amber-500/20',
    desc: 'Equity-heavy, higher growth potential (~15% p.a.)',
  },
]

export default function SIPAdvisor() {
  const [riskLevel, setRiskLevel] = useState('medium')
  const [monthlyAmount, setMonthlyAmount] = useState(5000)
  const [goalYears, setGoalYears] = useState(10)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleCalculate() {
    if (monthlyAmount <= 0 || goalYears <= 0) {
      setError('Please enter valid amount and years')
      return
    }

    setLoading(true)
    setError('')
    try {
      const data = await getSIPRecommendation(riskLevel, monthlyAmount, goalYears)
      setResult(data)
    } catch (e) {
      setError(e.message || 'Failed to get SIP recommendation')
    }
    setLoading(false)
  }

  const projectionChartData = result ? [
    { name: 'Invested', value: result.projections.total_invested, fill: '#64748b' },
    { name: 'Returns', value: result.projections.estimated_returns, fill: '#06d6a0' },
  ] : []

  const allocationPieData = result ? result.recommended_allocation.map((a, i) => ({
    name: a.type,
    value: a.allocation,
    amount: a.monthly_amount,
    fill: CHART_COLORS[i % CHART_COLORS.length],
  })) : []

  return (
    <div className="p-4 md:p-6 space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">SIP Advisor</h1>
        <p className="text-sm text-[var(--text-muted)]">
          Personalized SIP recommendations based on your risk appetite
        </p>
      </div>

      {/* Risk Selection */}
      <div className="glass-card p-5">
        <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">
          1. Select your risk appetite
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {RISK_LEVELS.map((risk) => (
            <button
              key={risk.value}
              onClick={() => setRiskLevel(risk.value)}
              className={`
                p-4 rounded-xl border text-left transition-all cursor-pointer
                ${riskLevel === risk.value
                  ? `${risk.bg} border-2 shadow-lg`
                  : 'bg-[var(--bg-card)] border-[var(--border)] hover:border-[var(--border-active)]'
                }
              `}
            >
              <div className="flex items-center gap-2 mb-2">
                <risk.icon className={`w-5 h-5 ${risk.color}`} />
                <span className={`font-semibold ${riskLevel === risk.value ? risk.color : 'text-[var(--text-primary)]'}`}>
                  {risk.label}
                </span>
              </div>
              <p className="text-xs text-[var(--text-muted)]">{risk.desc}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Amount & Duration */}
      <div className="glass-card p-5">
        <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">
          2. Enter SIP details
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-[var(--text-muted)] mb-2">
              Monthly SIP Amount (₹)
            </label>
            <div className="relative">
              <IndianRupee className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)]" />
              <input
                id="sip-amount"
                type="number"
                value={monthlyAmount}
                onChange={(e) => setMonthlyAmount(Number(e.target.value))}
                placeholder="5000"
                className="input-field pl-10"
                min="100"
                step="500"
              />
            </div>
            <div className="flex gap-2 mt-2">
              {[1000, 2000, 5000, 10000, 25000].map(v => (
                <button
                  key={v}
                  onClick={() => setMonthlyAmount(v)}
                  className={`px-2 py-1 rounded text-xs transition-all cursor-pointer
                    ${monthlyAmount === v
                      ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30'
                      : 'bg-[var(--bg-card)] text-[var(--text-muted)] border border-[var(--border)] hover:text-white'
                    }
                  `}
                >
                  ₹{v.toLocaleString()}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-xs text-[var(--text-muted)] mb-2">
              Investment Horizon (Years)
            </label>
            <input
              id="sip-years"
              type="number"
              value={goalYears}
              onChange={(e) => setGoalYears(Number(e.target.value))}
              placeholder="10"
              className="input-field"
              min="1"
              max="50"
            />
            <div className="flex gap-2 mt-2">
              {[3, 5, 10, 15, 20, 30].map(v => (
                <button
                  key={v}
                  onClick={() => setGoalYears(v)}
                  className={`px-2 py-1 rounded text-xs transition-all cursor-pointer
                    ${goalYears === v
                      ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30'
                      : 'bg-[var(--bg-card)] text-[var(--text-muted)] border border-[var(--border)] hover:text-white'
                    }
                  `}
                >
                  {v}yr
                </button>
              ))}
            </div>
          </div>
        </div>

        <button
          id="sip-calculate-btn"
          onClick={handleCalculate}
          disabled={loading}
          className="btn-primary mt-6 w-full justify-center"
        >
          {loading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <>
              <Calculator className="w-5 h-5" />
              Calculate SIP Recommendation
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="glass-card p-4 border-red-500/20 bg-red-500/5">
          <p className="text-sm text-red-400">{error}</p>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-6 animate-slideUp">
          {/* Projection Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 stagger-children">
            <div className="glass-card p-5 text-center">
              <p className="text-xs text-[var(--text-muted)] uppercase tracking-wider mb-2">Total Invested</p>
              <p className="text-2xl font-bold text-[var(--text-primary)]">
                ₹{result.projections.total_invested.toLocaleString('en-IN')}
              </p>
            </div>
            <div className="glass-card p-5 text-center border-emerald-500/20">
              <p className="text-xs text-[var(--text-muted)] uppercase tracking-wider mb-2">Estimated Value</p>
              <p className="text-2xl font-bold text-emerald-400">
                ₹{result.projections.estimated_value.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
              </p>
            </div>
            <div className="glass-card p-5 text-center">
              <p className="text-xs text-[var(--text-muted)] uppercase tracking-wider mb-2">Wealth Multiplier</p>
              <p className="text-2xl font-bold text-indigo-400">
                {result.projections.wealth_created_multiplier}x
              </p>
              <p className="text-xs text-emerald-400 mt-1">
                Returns: ₹{result.projections.estimated_returns.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
              </p>
            </div>
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Projection Bar Chart */}
            <div className="glass-card p-5">
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
                Investment vs Returns
              </h3>
              <div className="h-[250px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={projectionChartData} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.08)" />
                    <XAxis type="number" tick={{ fill: '#64748b', fontSize: 11 }}
                      tickFormatter={(v) => `₹${(v/100000).toFixed(0)}L`} />
                    <YAxis type="category" dataKey="name" tick={{ fill: '#94a3b8', fontSize: 13 }} width={70} />
                    <Tooltip
                      contentStyle={{
                        background: '#16163a',
                        border: '1px solid rgba(99,102,241,0.2)',
                        borderRadius: '8px',
                        color: '#f1f5f9',
                      }}
                      formatter={(v) => [`₹${v.toLocaleString('en-IN')}`, '']}
                    />
                    <Bar dataKey="value" radius={[0, 8, 8, 0]}>
                      {projectionChartData.map((entry, i) => (
                        <Cell key={i} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Allocation Pie */}
            <div className="glass-card p-5">
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
                Recommended Allocation
              </h3>
              <div className="h-[200px]">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={allocationPieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={80}
                      dataKey="value"
                      stroke="none"
                    >
                      {allocationPieData.map((entry, i) => (
                        <Cell key={i} fill={entry.fill} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        background: '#16163a',
                        border: '1px solid rgba(99,102,241,0.2)',
                        borderRadius: '8px',
                        color: '#f1f5f9',
                      }}
                      formatter={(v, n, p) => [`${v}% (₹${p.payload.amount}/mo)`, p.payload.name]}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Fund Recommendations */}
          <div className="glass-card p-5">
            <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
              Fund Recommendations
            </h3>
            <div className="space-y-3">
              {result.recommended_allocation?.map((fund, i) => (
                <div key={i} className="flex items-center gap-4 p-4 rounded-xl bg-[var(--bg-card)] border border-[var(--border)]">
                  <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ background: CHART_COLORS[i] }} />
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-[var(--text-primary)]">{fund.type}</p>
                    <p className="text-xs text-[var(--text-muted)]">{fund.example}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-bold text-[var(--text-primary)]">{fund.allocation}%</p>
                    <p className="text-xs text-indigo-400">₹{fund.monthly_amount?.toLocaleString()}/mo</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Disclaimer */}
          <div className="text-center p-4">
            <p className="text-xs text-[var(--text-muted)] italic">{result.disclaimer}</p>
          </div>
        </div>
      )}
    </div>
  )
}
