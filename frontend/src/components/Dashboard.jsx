import { useEffect, useRef, useState } from 'react'
import { gsap } from 'gsap'
import {
  Activity,
  AlertCircle,
  BookmarkCheck,
  Check,
  Cpu,
  Download,
  FileDown,
  FileText,
  Flame,
  Layers,
  Printer,
  RefreshCw,
  RotateCcw,
  Save,
  Share2,
  Shield,
  Sparkles,
} from 'lucide-react'
import ArcGauge from './ArcGauge'
import FusionBreakdown from './FusionBreakdown'
import MedicalReportModal, { downloadMedicalReportFile } from './MedicalReportModal'
import Recommendations from './Recommendations'
import TrendChart from './TrendChart'

export default function Dashboard({
  result,
  onSaveHistory,
  isSaved = false,
  user = null,
  form = {},
  imagePreview = null,
  recalculating = false,
  onRecalculate = null,
}) {

  const [notes, setNotes] = useState('')
  const [savedLocally, setSavedLocally] = useState(isSaved)
  const [reportModalOpen, setReportModalOpen] = useState(false)
  const dashboardRef = useRef(null)

  useEffect(() => {
    if (result && dashboardRef.current) {
      gsap.fromTo(
        dashboardRef.current,
        { opacity: 0, y: 20 },
        { opacity: 1, y: 0, duration: 0.6, ease: 'power2.out' }
      )
    }
  }, [result])

  if (!result) return null

  const g = result.gauges || {}
  const img = result.image || {}
  const method = img.method || 'mobilenetv2_acne04_improved'
  const severity = img.severity ?? 1

  function handleSave() {
    if (onSaveHistory) {
      onSaveHistory(result, notes)
      setSavedLocally(true)
    }
  }

  // Hayashi Severity Descriptions (Clinical Hospital Palettes)
  const severityConfigs = {
    0: { label: 'Grade 0: Clear / Mild', badge: 'text-emerald-800 border-emerald-200 bg-emerald-50' },
    1: { label: 'Grade 1: Moderate Inflammatory', badge: 'text-amber-800 border-amber-200 bg-amber-50' },
    2: { label: 'Grade 2: Severe Papulopustular', badge: 'text-orange-800 border-orange-200 bg-orange-50' },
    3: { label: 'Grade 3: Very Severe Nodulocystic', badge: 'text-rose-800 border-rose-200 bg-rose-50' },
  }
  const currentSev = severityConfigs[severity] || severityConfigs[1]

  const signalMetrics = [
    { label: 'Sebum Oiliness', val: img.oiliness ?? 45, max: 100, color: 'bg-teal-600' },
    { label: 'Pore Congestion', val: img.pores ?? 50, max: 100, color: 'bg-sky-600' },
    { label: 'Erythema / Redness', val: img.redness ?? 60, max: 100, color: 'bg-rose-500' },
    { label: 'Dark Spots / PIH', val: img.dark_spots ?? 35, max: 100, color: 'bg-amber-500' },
  ]

  return (
    <section ref={dashboardRef} className="space-y-6 print:space-y-4">
      {/* Top Clinical Action Toolbar */}
      <div className="bg-white border border-slate-200 rounded-2xl p-4 sm:p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-clinical">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-teal-50 border border-teal-200 text-teal-800">
            <Cpu className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-sans text-xs font-bold text-slate-900 uppercase tracking-wider">
                Clinical Prognosis Complete
              </span>
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
            </div>
            <p className="text-xs text-slate-500 font-sans">
              Validated Multimodal Synthesis · <span className="text-teal-800 font-medium font-mono">{method}</span>
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2.5 w-full sm:w-auto">
          <button
            onClick={() => {
              downloadMedicalReportFile({ result, user, form, imagePreview })
              setReportModalOpen(true)
            }}
            className="flex-1 sm:flex-none flex items-center justify-center gap-2 rounded-xl bg-teal-700 hover:bg-teal-800 px-4 py-2.5 text-xs font-bold text-white shadow-sm transition cursor-pointer"
            title="Download full clinical pathology/dermatology medical report (.html file)"
          >
            <FileDown className="h-4 w-4" />
            <span>Download Medical Report</span>
          </button>

          <button
            onClick={() => setReportModalOpen(true)}
            className="flex items-center justify-center gap-2 rounded-xl border border-slate-300 bg-white hover:bg-slate-50 px-3.5 py-2.5 text-xs font-semibold text-slate-700 shadow-sm transition cursor-pointer"
            title="Preview report & Print to PDF"
          >
            <Printer className="h-4 w-4 text-slate-600" />
            <span>Preview & Print PDF</span>
          </button>

          <button
            onClick={handleSave}
            disabled={savedLocally}
            className={`flex-1 sm:flex-none flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-xs font-semibold shadow-sm transition cursor-pointer ${
              savedLocally
                ? 'bg-emerald-50 text-emerald-800 border border-emerald-200 cursor-default'
                : 'bg-white hover:bg-slate-50 text-slate-700 border border-slate-300'
            }`}
          >
            {savedLocally ? <BookmarkCheck className="h-4 w-4 text-emerald-700" /> : <Save className="h-4 w-4" />}
            <span>{savedLocally ? 'Logged in Registry' : 'Save Record'}</span>
          </button>
        </div>
      </div>

      {/* Main Gauges & Severity Card */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 space-y-6 shadow-clinical">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-5">
          <div>
            <span className="text-[11px] font-sans uppercase tracking-wider text-teal-800 font-bold">
              DERMATOLOGICAL EVALUATION
            </span>
            <h2 className="font-sans text-2xl sm:text-3xl font-bold text-slate-900 mt-0.5">
              Multi-Engine Cutaneous Assessment
            </h2>
            <div className="flex flex-wrap items-center gap-2 mt-2">
              <span className={`rounded-full border px-3 py-0.5 text-xs font-sans font-bold ${currentSev.badge}`}>
                {img.current_skin_condition || currentSev.label}
              </span>
              {img.problem_areas?.length > 0 && (
                <div className="flex items-center gap-1.5 text-xs text-slate-600 font-sans">
                  <span className="text-slate-400">Involved Anatomical Zones:</span>
                  <span className="text-slate-800 font-medium">{img.problem_areas.join(', ')}</span>
                </div>
              )}
            </div>
          </div>

          <div className="rounded-xl bg-slate-50 border border-slate-200 p-3 font-sans text-xs text-slate-600 space-y-1">
            <div className="flex justify-between gap-4">
              <span className="text-slate-400">Vision CNN:</span>
              <span className="text-slate-900 font-semibold font-mono">MobileNetV2 (69.01%)</span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-slate-400">Data Engine:</span>
              <span className="text-slate-900 font-semibold font-mono">Multi-Output RF</span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-slate-400">Fusion Weights:</span>
              <span className="text-teal-800 font-bold font-mono">55% Visual / 45% Systemic</span>
            </div>
          </div>
        </div>

        {/* 5 Animated Gauges Row */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-6 justify-items-center pt-2">
          <ArcGauge
            value={g.skin_health ?? result.skin_health_score ?? 68}
            label="Skin Barrier Health"
            color="#0f766e"
            size={160}
          />
          <ArcGauge
            value={g.image_risk ?? result.final_risk_percent ?? 42}
            label="Visual Cutaneous Risk"
            color="#e11d48"
            size={160}
          />
          <ArcGauge
            value={g.hormonal ?? result.data?.hormonal_score ?? 35}
            label="Endocrine & Hormonal"
            color="#d97706"
            size={160}
          />
          <ArcGauge
            value={g.lifestyle ?? result.data?.lifestyle_score ?? 40}
            label="Systemic Lifestyle"
            color="#0284c7"
            size={160}
          />
          <ArcGauge
            value={g.environmental ?? result.data?.environmental_score ?? 30}
            label="Exposome & Climate"
            color="#0d9488"
            size={160}
          />
        </div>
      </div>

      {/* Transparent Multimodal Fusion Breakdown */}
      <FusionBreakdown result={result} />

      {/* Trajectory & Cutaneous Signals Grid */}
      <div className="grid gap-6 lg:grid-cols-5">
        {/* 3-Month Trajectory Area Chart */}
        <div className="lg:col-span-3 bg-white border border-slate-200 rounded-2xl p-6 sm:p-7 space-y-4 shadow-clinical">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-[11px] font-sans uppercase tracking-wider text-teal-800 font-bold">
                PROJECTION TRAJECTORY
              </span>
              <h3 className="font-sans text-lg font-bold text-slate-900 mt-0.5">
                3-Month Future Risk Trend
              </h3>
            </div>
            <span className="rounded-full bg-teal-50 border border-teal-200 px-2.5 py-0.5 text-[10px] font-sans font-bold text-teal-800">
              Intervention Forecast Model
            </span>
          </div>

          <TrendChart
            data={result.trend}
            analysis={result.trend_analysis}
            disclaimer={result.trend_disclaimer}
            finalRisk={result.final_risk_percent}
          />
        </div>

        {/* Cutaneous Biomarker Signals Detail */}
        <div className="lg:col-span-2 bg-white border border-slate-200 rounded-2xl p-6 sm:p-7 space-y-4 shadow-clinical">
          <div>
            <span className="text-[11px] font-sans uppercase tracking-wider text-sky-800 font-bold">
              COMPUTER VISION SIGNALS
            </span>
            <h3 className="font-sans text-lg font-bold text-slate-900 mt-0.5">
              Cutaneous Attribute Matrix
            </h3>
          </div>

          {/* Signal meters */}
          <div className="space-y-3.5 pt-1">
            {signalMetrics.map((sig) => (
              <div key={sig.label} className="space-y-1">
                <div className="flex justify-between items-center text-xs">
                  <span className="text-slate-700 font-medium">{sig.label}</span>
                  <span className="text-slate-900 font-bold font-mono">{Math.round(sig.val)} / {sig.max}</span>
                </div>
                <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden">
                  <div
                    className={`h-full rounded-full ${sig.color} transition-all duration-1000 shadow-sm`}
                    style={{ width: `${Math.min(100, Math.max(5, sig.val))}%` }}
                  />
                </div>
              </div>
            ))}
          </div>

          {/* Top Risk Drivers */}
          {result.data?.drivers?.length > 0 && (
            <div className="pt-3 border-t border-slate-200">
              <p className="text-[11px] font-sans uppercase tracking-wider text-slate-500 mb-1.5 font-bold">
                Primary Contributing Drivers
              </p>
              <div className="flex flex-wrap gap-1.5">
                {result.data.drivers.map((d) => (
                  <span
                    key={d}
                    className="rounded-lg bg-slate-50 border border-slate-200 px-2.5 py-1 text-xs font-sans text-slate-700"
                  >
                    • {d}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Clinical Recommendations Section */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 pb-3">
          <div>
            <span className="text-[11px] font-sans uppercase tracking-wider text-teal-800 font-bold">
              ACTIONABLE CLINICAL STRATEGY
            </span>
            <h3 className="font-sans text-xl font-bold text-slate-900 mt-0.5">
              Personalized Clinical Action Plan
            </h3>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {recalculating ? (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 border border-amber-200 px-3 py-1 text-xs font-semibold text-amber-800 animate-pulse">
                <RefreshCw className="h-3.5 w-3.5 text-amber-600 animate-spin" />
                <span>Syncing with Questionnaire Updates…</span>
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 border border-emerald-200 px-3 py-1 text-xs font-semibold text-emerald-800">
                <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                <span>Live Questionnaire Sync Active</span>
              </span>
            )}

            {onRecalculate && (
              <button
                type="button"
                onClick={onRecalculate}
                disabled={recalculating}
                className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 px-2.5 py-1 text-xs font-semibold text-slate-700 shadow-2xs transition disabled:opacity-50 cursor-pointer"
                title="Recalculate recommendations from current questionnaire responses"
              >
                <RotateCcw className={`h-3.5 w-3.5 text-teal-700 ${recalculating ? 'animate-spin' : ''}`} />
                <span>Refresh Plan</span>
              </button>
            )}
          </div>
        </div>

        {/* Explainability Callout Banner */}
        <div className="rounded-xl border border-teal-200/80 bg-teal-50/50 p-3.5 text-xs text-slate-700 font-sans flex items-start gap-2.5">
          <Sparkles className="h-4 w-4 shrink-0 text-teal-700 mt-0.5" />
          <p className="leading-relaxed">
            <strong className="text-teal-950 font-bold">Tailored to your specific profile:</strong> Recommendations below reflect your visual biomarkers (<span className="text-teal-900 font-semibold">{currentSev.label}</span>, Sebum: <span className="font-mono font-semibold">{Math.round(img.oiliness ?? 0)}%</span>, Redness: <span className="font-mono font-semibold">{Math.round(img.redness ?? 0)}%</span>) alongside your systemic hormonal, lifestyle, and exposome answers. Modifying any questionnaire fields above will instantly re-evaluate and update this plan.
          </p>
        </div>

        <Recommendations recommendations={result.recommendations} />
      </div>


      {/* Clinical Memo / Note Attachment */}
      <div className="bg-white border border-slate-200 rounded-2xl p-4 sm:p-5 flex flex-col sm:flex-row gap-3 items-center shadow-clinical">
        <div className="flex-1 w-full">
          <input
            type="text"
            placeholder="Add clinical observation notes (e.g. 'Patient started 2.5% benzoyl peroxide topical wash; follow up in 4 weeks')..."
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="w-full rounded-xl border border-slate-300 bg-slate-50 px-4 py-2.5 text-xs text-slate-900 outline-none focus:border-teal-700 focus:bg-white transition placeholder:text-slate-400 font-sans"
          />
        </div>
        <button
          onClick={handleSave}
          disabled={savedLocally}
          className="w-full sm:w-auto rounded-xl bg-teal-700 hover:bg-teal-800 px-5 py-2.5 text-xs font-semibold text-white shadow-sm transition disabled:opacity-60 whitespace-nowrap cursor-pointer"
        >
          {savedLocally ? '✓ Logged to Registry' : 'Save with Notes'}
        </button>
      </div>


      {/* Official Downloadable Clinical Medical Report Modal */}
      <MedicalReportModal
        isOpen={reportModalOpen}
        onClose={() => setReportModalOpen(false)}
        result={result}
        user={user}
        form={form}
        imagePreview={imagePreview}
      />
    </section>
  )
}
