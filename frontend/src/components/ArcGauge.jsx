import { useEffect, useRef } from 'react'
import { gsap } from 'gsap'

export default function ArcGauge({
  value = 0,
  label,
  max = 100,
  color = '#0f766e',
  size = 150,
}) {
  const numberRef = useRef(null)
  const circleRef = useRef(null)

  const stroke = 10
  const r = (size - stroke) / 2
  const circ = 2 * Math.PI * r
  const pct = Math.max(0, Math.min(1, value / max))
  const sweep = 0.75
  const dash = circ * sweep
  const targetOffset = dash * (1 - pct)

  useEffect(() => {
    const valObj = { val: 0 }
    if (numberRef.current) {
      gsap.to(valObj, {
        val: value,
        duration: 1.2,
        ease: 'power2.out',
        onUpdate: () => {
          if (numberRef.current) {
            numberRef.current.textContent = Math.round(valObj.val)
          }
        },
      })
    }

    if (circleRef.current) {
      gsap.fromTo(
        circleRef.current,
        { strokeDashoffset: dash },
        {
          strokeDashoffset: targetOffset,
          duration: 1.3,
          ease: 'power2.out',
        }
      )
    }
  }, [value, dash, targetOffset])

  // Clinical status badge calculation
  let statusText = 'Normal'
  let statusColor = 'text-teal-800 bg-teal-50 border-teal-200'
  if (label.toLowerCase().includes('health')) {
    if (value >= 75) {
      statusText = 'Optimal'
      statusColor = 'text-emerald-800 bg-emerald-50 border-emerald-200'
    } else if (value >= 50) {
      statusText = 'Fair'
      statusColor = 'text-amber-800 bg-amber-50 border-amber-200'
    } else {
      statusText = 'Depleted'
      statusColor = 'text-rose-800 bg-rose-50 border-rose-200'
    }
  } else {
    // Risk score
    if (value <= 25) {
      statusText = 'Low'
      statusColor = 'text-emerald-800 bg-emerald-50 border-emerald-200'
    } else if (value <= 55) {
      statusText = 'Moderate'
      statusColor = 'text-amber-800 bg-amber-50 border-amber-200'
    } else {
      statusText = 'Elevated'
      statusColor = 'text-rose-800 bg-rose-50 border-rose-200'
    }
  }

  const gradientId = `gauge-grad-${label.replace(/\s+/g, '-').toLowerCase()}`

  return (
    <div className="flex flex-col items-center group select-none" style={{ width: size }}>
      <div className="relative">
        <svg width={size} height={size * 0.8} viewBox={`0 0 ${size} ${size * 0.8}`}>
          <defs>
            <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor={color} stopOpacity="0.85" />
              <stop offset="100%" stopColor={color} stopOpacity="1" />
            </linearGradient>
          </defs>

          <g transform={`translate(${size / 2}, ${size / 2}) rotate(135)`}>
            {/* Background Track */}
            <circle
              r={r}
              fill="none"
              stroke="#e2e8f0"
              strokeWidth={stroke}
              strokeDasharray={`${dash} ${circ}`}
              strokeLinecap="round"
            />
            {/* Animated Value Arc */}
            <circle
              ref={circleRef}
              r={r}
              fill="none"
              stroke={`url(#${gradientId})`}
              strokeWidth={stroke}
              strokeDasharray={`${dash} ${circ}`}
              strokeDashoffset={dash}
              strokeLinecap="round"
            />
          </g>

          {/* Number Display */}
          <text
            x="50%"
            y="57%"
            textAnchor="middle"
            className="fill-slate-900 font-mono font-bold tracking-tight"
            style={{ fontSize: size * 0.22 }}
          >
            <tspan ref={numberRef}>0</tspan>
          </text>
          <text
            x="50%"
            y="72%"
            textAnchor="middle"
            className="fill-slate-400 font-mono"
            style={{ fontSize: size * 0.085 }}
          >
            / {max}
          </text>
        </svg>
      </div>

      <p className="mt-1 text-center text-xs font-semibold text-slate-700 tracking-wide">
        {label}
      </p>

      <span
        className={`mt-1 rounded-full border px-2.5 py-0.5 text-[10px] font-mono font-bold uppercase tracking-wider ${statusColor}`}
      >
        {statusText}
      </span>
    </div>
  )
}
