import { useEffect, useRef } from 'react'
import { gsap } from 'gsap'
import {
  Activity,
  ArrowUpRight,
  LineChart as ChartIcon,
  ShieldAlert,
  TrendingDown,
  TrendingUp,
} from 'lucide-react'
import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

export default function AnalyticsView({ history = [], onSelectTab }) {
  const containerRef = useRef(null)

  useEffect(() => {
    if (containerRef.current) {
      gsap.fromTo(
        containerRef.current.children,
        { opacity: 0, y: 15 },
        { opacity: 1, y: 0, duration: 0.5, stagger: 0.08, ease: 'power2.out' }
      )
    }
  }, [history])

  if (!history || history.length === 0) {
    return (
      <div className="bg-white rounded-2xl p-16 text-center border-2 border-dashed border-slate-300 shadow-clinical">
        <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-xl bg-teal-50 border border-teal-200 text-teal-800">
          <ChartIcon className="h-7 w-7" />
        </div>
        <h3 className="font-sans text-lg font-bold text-slate-900">No Longitudinal Data</h3>
        <p className="mx-auto mt-1 max-w-md text-xs sm:text-sm text-slate-500">
          Complete at least 2 clinical skin scans over time to visualize barrier restoration curve, risk reduction, and cutaneous attribute evolution.
        </p>
        <button
          onClick={() => onSelectTab('analyze')}
          className="mt-5 rounded-xl bg-teal-700 hover:bg-teal-800 px-6 py-2.5 text-xs font-semibold text-white shadow-sm transition cursor-pointer"
        >
          Perform Initial Clinical Scan →
        </button>
      </div>
    )
  }

  // Format chronologically (oldest to newest for charting)
  const chartData = [...history].reverse().map((s, idx) => ({
    name: s.created_at
      ? new Date(s.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
      : `Scan ${idx + 1}`,
    healthScore: Math.round(s.skin_health_score ?? 0),
    riskPercent: Math.round(s.risk_percent ?? 0),
    oiliness: s.image_attributes?.oiliness ?? 0,
    redness: s.image_attributes?.redness ?? 0,
  }))

  const avgHealth = Math.round(
    history.reduce((acc, curr) => acc + (curr.skin_health_score || 0), 0) / history.length
  )
  const avgRisk = Math.round(
    history.reduce((acc, curr) => acc + (curr.risk_percent || 0), 0) / history.length
  )

  return (
    <div ref={containerRef} className="space-y-6">
      {/* Top Stats Overview */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-clinical">
          <p className="text-[11px] font-sans font-bold uppercase tracking-wider text-slate-500">
            Total Evaluations
          </p>
          <p className="font-sans text-3xl font-bold text-slate-900 mt-1 font-mono">
            {history.length}
          </p>
          <p className="text-xs text-slate-400 mt-0.5 font-sans">Documented clinical sessions</p>
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-clinical">
          <p className="text-[11px] font-sans font-bold uppercase tracking-wider text-slate-500">
            Mean Barrier Health
          </p>
          <p className="font-sans text-3xl font-bold text-teal-800 mt-1 font-mono">
            {avgHealth} <span className="text-xs font-normal text-slate-400 font-sans">/ 100</span>
          </p>
          <p className="text-xs text-slate-400 mt-0.5 font-sans">Aggregate barrier stability</p>
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-clinical">
          <p className="text-[11px] font-sans font-bold uppercase tracking-wider text-slate-500">
            Mean Cutaneous Risk
          </p>
          <p className="font-sans text-3xl font-bold text-rose-700 mt-1 font-mono">
            {avgRisk}%
          </p>
          <p className="text-xs text-slate-400 mt-0.5 font-sans">Average lesion propensity</p>
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-clinical">
          <p className="text-[11px] font-sans font-bold uppercase tracking-wider text-slate-500">
            Clinical Status
          </p>
          <p className="font-sans text-xl font-bold text-slate-900 mt-2 flex items-center gap-1.5">
            <ArrowUpRight className="h-5 w-5 text-teal-700" />
            <span>Monitored</span>
          </p>
          <p className="text-xs text-slate-400 mt-0.5 font-sans">Longitudinal tracking active</p>
        </div>
      </div>

      {/* Main Longitudinal Comparison Chart */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 space-y-4 shadow-clinical">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200 pb-4">
          <div>
            <span className="text-[11px] font-sans uppercase tracking-wider text-teal-800 font-bold">
              LONGITUDINAL TELEMETRY
            </span>
            <h3 className="font-sans text-xl font-bold text-slate-900 mt-0.5">
              Barrier Health vs. Acne Risk Over Time
            </h3>
          </div>
          <div className="flex items-center gap-4 text-xs font-sans">
            <div className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full bg-teal-700" />
              <span className="text-slate-700 font-medium">Health Score</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full bg-rose-600" />
              <span className="text-slate-700 font-medium">Risk %</span>
            </div>
          </div>
        </div>

        <div className="h-72 w-full pt-4">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="healthGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#0f766e" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#0f766e" stopOpacity={0.02} />
                </linearGradient>
                <linearGradient id="riskGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#e11d48" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#e11d48" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" />
              <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 11, fontFamily: 'Inter, sans-serif' }} axisLine={{ stroke: '#cbd5e1' }} tickLine={false} />
              <YAxis domain={[0, 100]} tick={{ fill: '#64748b', fontSize: 11, fontFamily: 'Inter, sans-serif' }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#ffffff',
                  borderColor: '#cbd5e1',
                  borderRadius: '10px',
                  color: '#0f172a',
                  fontFamily: 'Inter, sans-serif',
                  fontSize: '12px',
                  boxShadow: '0 4px 12px rgba(15, 23, 42, 0.08)',
                }}
              />
              <Area type="monotone" dataKey="healthScore" stroke="#0f766e" strokeWidth={2.5} fill="url(#healthGrad)" dot={{ r: 4, fill: '#0f766e', stroke: '#fff', strokeWidth: 2 }} />
              <Area type="monotone" dataKey="riskPercent" stroke="#e11d48" strokeWidth={2.5} fill="url(#riskGrad)" dot={{ r: 4, fill: '#e11d48', stroke: '#fff', strokeWidth: 2 }} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
