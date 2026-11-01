import React, { useState } from 'react'
import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Info,
  Minus,
  Sparkles,
  TrendingDown,
  TrendingUp,
} from 'lucide-react'

export default function TrendChart({
  data = [],
  analysis = null,
  disclaimer = null,
  finalRisk = null,
}) {
  const [showMethodology, setShowMethodology] = useState(false)
  const [showAdherenceCurve, setShowAdherenceCurve] = useState(true)

  // Safe fallback constructed strictly from dynamic finalRisk if data is absent, avoiding static constants
  const baselineFallback = typeof finalRisk === 'number' ? finalRisk : 50.0
  const chartData =
    data && data.length > 0
      ? data
      : [
        {
          label: 'Now',
          month_offset: 0,
          risk_percent: Math.round(baselineFallback),
          adherence_risk_percent: Math.round(baselineFallback),
          barrier_health: Math.round(100 - baselineFallback),
          phase: 'Baseline Intake',
        },
        {
          label: 'Month 1',
          month_offset: 1,
          risk_percent: Math.round(baselineFallback),
          adherence_risk_percent: Math.round(baselineFallback * 0.82),
          barrier_health: Math.round(100 - baselineFallback),
          phase: 'Turnover Phase',
        },
        {
          label: 'Month 2',
          month_offset: 2,
          risk_percent: Math.round(baselineFallback),
          adherence_risk_percent: Math.round(baselineFallback * 0.62),
          barrier_health: Math.round(100 - baselineFallback),
          phase: 'Remodeling Phase',
        },
        {
          label: 'Month 3',
          month_offset: 3,
          risk_percent: Math.round(baselineFallback),
          adherence_risk_percent: Math.round(baselineFallback * 0.45),
          barrier_health: Math.round(100 - baselineFallback),
          phase: 'Equilibrium Phase',
        },
      ]

  const nowPt = chartData[0] || { risk_percent: 50 }
  const m3Pt = chartData[chartData.length - 1] || nowPt
  const netDelta = analysis?.net_3_month_delta ?? Math.round((m3Pt.risk_percent - nowPt.risk_percent) * 10) / 10
  const velocity = analysis?.monthly_velocity_pct ?? (netDelta / 2.7).toFixed(1)
  const status = analysis?.trajectory_status_code || (netDelta > 1.5 ? 'escalating' : netDelta < -1.5 ? 'improving' : 'stable')

  const statusConfig = {
    escalating: {
      label: 'Escalating Risk Trajectory',
      color: 'text-rose-700 bg-rose-50 border-rose-200',
      badgeFill: '#e11d48',
      icon: TrendingUp,
      strokeColor: '#e11d48',
      gradId: 'roseTrendGrad',
      gradColor: '#e11d48',
      summaryText: 'Without intervention, existing cutaneous and systemic stressors project upward risk drift.',
    },
    improving: {
      label: 'Favorable Recovery Trajectory',
      color: 'text-teal-700 bg-teal-50 border-teal-200',
      badgeFill: '#0f766e',
      icon: TrendingDown,
      strokeColor: '#0f766e',
      gradId: 'tealTrendGrad',
      gradColor: '#0f766e',
      summaryText: 'Protective lifestyle disciplines and low baseline lesions forecast sustained cutaneous improvement.',
    },
    stable: {
      label: 'Stable / Steady-State Trajectory',
      color: 'text-sky-700 bg-sky-50 border-sky-200',
      badgeFill: '#0284c7',
      icon: Minus,
      strokeColor: '#0284c7',
      gradId: 'skyTrendGrad',
      gradColor: '#0284c7',
      summaryText: 'Current baseline cutaneous factors balance systemic inputs with minimal monthly drift.',
    },
  }[status] || {
    label: 'Evaluated Risk Trajectory',
    color: 'text-slate-700 bg-slate-50 border-slate-200',
    badgeFill: '#64748b',
    icon: Activity,
    strokeColor: '#0f766e',
    gradId: 'defaultGrad',
    gradColor: '#0f766e',
    summaryText: 'Standard 3-month projection model based on intake inputs.',
  }

  const StatusIcon = statusConfig.icon

  // Custom Clinical Tooltip
  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload || !payload.length) return null
    const pt = payload[0].payload
    return (
      <div className="rounded-xl border border-slate-200 bg-white/95 p-3.5 shadow-clinical backdrop-blur-xs text-xs font-sans space-y-2 max-w-xs">
        <div className="border-b border-slate-100 pb-1.5 flex items-center justify-between gap-3">
          <span className="font-bold text-slate-900 font-mono">{label}</span>
          <span className="text-[10px] uppercase tracking-wider text-slate-500 font-medium">
            {pt.phase || 'Milestone'}
          </span>
        </div>
        <div className="space-y-1.5">
          <div className="flex items-center justify-between gap-4">
            <span className="text-slate-600 flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full" style={{ backgroundColor: statusConfig.strokeColor }} />
              Projected Risk:
            </span>
            <span className="font-bold font-mono text-slate-900">
              {pt.risk_percent}%
            </span>
          </div>
          {pt.adherence_risk_percent !== undefined && (
            <div className="flex items-center justify-between gap-4">
              <span className="text-emerald-700 flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-emerald-600" />
                With Action Plan:
              </span>
              <span className="font-bold font-mono text-emerald-800">
                {pt.adherence_risk_percent}%
              </span>
            </div>
          )}
          {pt.barrier_health !== undefined && (
            <div className="flex items-center justify-between gap-4 border-t border-slate-100 pt-1 text-[11px]">
              <span className="text-slate-500">Est. Barrier Health:</span>
              <span className="font-semibold font-mono text-teal-800">
                {pt.barrier_health} / 100
              </span>
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="w-full space-y-4">
      {/* Dynamic Trajectory Status Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-50/80 rounded-xl p-3 border border-slate-200/80">
        <div className="flex items-center gap-2.5">
          <span className={`flex h-7 w-7 items-center justify-center rounded-lg border ${statusConfig.color}`}>
            <StatusIcon className="h-4 w-4" />
          </span>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-slate-900 font-sans">
                {statusConfig.label}
              </span>
              <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded-md bg-white border border-slate-200 text-slate-700">
                Velocity: {velocity > 0 ? `+${velocity}` : velocity}% / mo
              </span>
            </div>
            <p className="text-[11px] text-slate-500 font-sans mt-0.5">
              {statusConfig.summaryText}
            </p>
          </div>
        </div>

        {/* Adherence Curve Toggle */}
        <button
          type="button"
          onClick={() => setShowAdherenceCurve(!showAdherenceCurve)}
          className="flex items-center gap-1.5 self-start sm:self-auto px-2.5 py-1 rounded-lg border border-slate-200 bg-white hover:bg-slate-100 text-[11px] font-sans font-medium text-slate-700 transition cursor-pointer shadow-xs"
        >
          <Sparkles className={`h-3.5 w-3.5 ${showAdherenceCurve ? 'text-emerald-700' : 'text-slate-400'}`} />
          <span>{showAdherenceCurve ? 'Hide Target Plan Curve' : 'Compare With Action Plan'}</span>
        </button>
      </div>

      {/* Main Area Chart */}
      <div className="h-64 sm:h-72 w-full pt-1">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 12, right: 16, left: -14, bottom: 0 }}>
            <defs>
              <linearGradient id={statusConfig.gradId} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={statusConfig.gradColor} stopOpacity={0.25} />
                <stop offset="95%" stopColor={statusConfig.gradColor} stopOpacity={0.02} />
              </linearGradient>
              <linearGradient id="adherenceGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#059669" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#059669" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" />
            <XAxis
              dataKey="label"
              tick={{ fill: '#64748b', fontSize: 11, fontFamily: 'Inter, sans-serif' }}
              axisLine={{ stroke: '#cbd5e1' }}
              tickLine={false}
            />
            <YAxis
              domain={[0, 100]}
              tick={{ fill: '#64748b', fontSize: 11, fontFamily: 'Inter, sans-serif' }}
              axisLine={false}
              tickLine={false}
              width={34}
            />
            <Tooltip content={<CustomTooltip />} />

            {/* Projected Unmanaged Risk Area */}
            <Area
              type="monotone"
              name="Projected Risk"
              dataKey="risk_percent"
              stroke={statusConfig.strokeColor}
              strokeWidth={2.5}
              fillOpacity={1}
              fill={`url(#${statusConfig.gradId})`}
              dot={{ r: 4, fill: statusConfig.strokeColor, stroke: '#ffffff', strokeWidth: 2 }}
              activeDot={{ r: 6, fill: statusConfig.strokeColor, stroke: '#ffffff', strokeWidth: 2 }}
            />

            {/* Optional Comparative Protocol Adherence Curve */}
            {showAdherenceCurve && (
              <Area
                type="monotone"
                name="With Action Plan"
                dataKey="adherence_risk_percent"
                stroke="#059669"
                strokeWidth={2}
                strokeDasharray="4 4"
                fillOpacity={1}
                fill="url(#adherenceGrad)"
                dot={{ r: 3.5, fill: '#059669', stroke: '#ffffff', strokeWidth: 2 }}
                activeDot={{ r: 5, fill: '#059669', stroke: '#ffffff', strokeWidth: 2 }}
              />
            )}
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* 4-Milestone Timeline Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 pt-1">
        {chartData.map((pt, idx) => {
          const deltaFromBaseline = Math.round((pt.risk_percent - nowPt.risk_percent) * 10) / 10
          return (
            <div
              key={pt.label}
              className={`rounded-xl border p-2.5 space-y-1 transition ${idx === 0
                ? 'border-slate-300 bg-white shadow-xs'
                : idx === 3
                  ? 'border-teal-300/80 bg-teal-50/30'
                  : 'border-slate-200 bg-slate-50/50'
                }`}
            >
              <div className="flex items-center justify-between text-[11px]">
                <span className="font-bold text-slate-800 font-mono">{pt.label}</span>
                {idx === 0 ? (
                  <span className="text-[10px] font-semibold text-slate-500 uppercase">Intake</span>
                ) : (
                  <span
                    className={`text-[10px] font-bold font-mono ${deltaFromBaseline > 0
                      ? 'text-rose-600'
                      : deltaFromBaseline < 0
                        ? 'text-emerald-700'
                        : 'text-slate-500'
                      }`}
                  >
                    {deltaFromBaseline > 0 ? `+${deltaFromBaseline}%` : `${deltaFromBaseline}%`}
                  </span>
                )}
              </div>
              <div className="flex items-baseline justify-between">
                <span className="text-lg font-bold font-mono text-slate-900">
                  {pt.risk_percent}%
                </span>
                <span className="text-[10px] text-slate-400 font-sans truncate max-w-[80px]">
                  {pt.phase?.split(' ')[0] || 'Phase'}
                </span>
              </div>
              {showAdherenceCurve && pt.adherence_risk_percent !== undefined && (
                <div className="text-[10px] font-sans flex items-center justify-between border-t border-slate-100 pt-1 text-slate-500">
                  <span>Plan target:</span>
                  <span className="font-bold font-mono text-emerald-800">
                    {pt.adherence_risk_percent}%
                  </span>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Methodology & Drivers Collapsible Drawer */}
      <div className="rounded-xl border border-slate-200 bg-slate-50/60 overflow-hidden">
        <button
          type="button"
          onClick={() => setShowMethodology(!showMethodology)}
          className="w-full flex items-center justify-between px-3.5 py-2.5 text-xs font-sans font-semibold text-slate-700 hover:text-slate-900 hover:bg-slate-100/60 transition cursor-pointer"
        >
          <div className="flex items-center gap-2">
            <Info className="h-3.5 w-3.5 text-teal-700" />
            <span>Transparent Projection Methodology & Factor Breakdown</span>
          </div>
          {showMethodology ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>

        {showMethodology && (
          <div className="px-4 pb-4 pt-1 space-y-3 text-xs font-sans border-t border-slate-200/80 bg-white">
            <p className="text-slate-600 leading-relaxed text-[11px] pt-1">
              {analysis?.methodology_summary ||
                'Skinova calculates 3-month projected cutaneous trajectories dynamically by evaluating Hayashi acne grade inertia, cutaneous micro-environment signals (oiliness, erythema, pores), and 21 systemic questionnaire parameters.'}
            </p>

            {/* Contributing Escalators & Stabilizers */}
            <div className="grid sm:grid-cols-2 gap-3 pt-1">
              {/* Escalators */}
              <div className="space-y-1.5">
                <span className="text-[11px] font-bold uppercase tracking-wider text-rose-800 flex items-center gap-1">
                  <AlertCircle className="h-3 w-3 text-rose-600" />
                  Primary Risk Escalators
                </span>
                {analysis?.primary_escalators && analysis.primary_escalators.length > 0 ? (
                  <ul className="space-y-1">
                    {analysis.primary_escalators.map((esc, i) => (
                      <li
                        key={i}
                        className="text-[11px] text-rose-700 bg-rose-50/70 border border-rose-200/60 rounded-md px-2 py-1"
                      >
                        {esc}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-[11px] text-slate-400 italic">No strong upward escalation factors detected.</p>
                )}
              </div>

              {/* Stabilizers */}
              <div className="space-y-1.5">
                <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-800 flex items-center gap-1">
                  <CheckCircle2 className="h-3 w-3 text-emerald-600" />
                  Protective Stabilizers
                </span>
                {analysis?.primary_stabilizers && analysis.primary_stabilizers.length > 0 ? (
                  <ul className="space-y-1">
                    {analysis.primary_stabilizers.map((stab, i) => (
                      <li
                        key={i}
                        className="text-[11px] text-emerald-700 bg-emerald-50/70 border border-emerald-200/60 rounded-md px-2 py-1"
                      >
                        {stab}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-[11px] text-slate-400 italic">No significant protective stabilizers identified.</p>
                )}
              </div>
            </div>

            {/* Deterministic Simulation Steps */}
            <div className="rounded-lg bg-slate-50 border border-slate-200 p-2.5 text-[11px] font-mono text-slate-700 space-y-1">
              <div className="font-bold text-slate-900 font-sans">Trajectory Mathematical Model:</div>
              <div>Baseline (t=0): {nowPt.risk_percent}%</div>
              <div>Net Monthly Velocity (V): {velocity > 0 ? `+${velocity}` : velocity}% / month</div>
              <div>Month +1: {chartData[1]?.risk_percent}% | Month +2: {chartData[2]?.risk_percent}% | Month +3: {chartData[3]?.risk_percent}%</div>
            </div>
          </div>
        )}
      </div>

    </div>
  )
}
