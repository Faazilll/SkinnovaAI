import { useEffect, useRef, useState } from 'react'
import { gsap } from 'gsap'
import {
  Calendar,
  ChevronRight,
  Clock,
  FileDown,
  History,
  RotateCcw,
  Trash2,
  TrendingDown,
  TrendingUp,
} from 'lucide-react'
import { apiDeleteScan } from '../api'
import MedicalReportModal from './MedicalReportModal'

export default function HistoryView({
  history = [],
  onReloadScan,
  onRefreshHistory,
  user,
  onOpenAuth,
}) {
  const [selectedScan, setSelectedScan] = useState(null)
  const [deletingId, setDeletingId] = useState(null)
  const [historyReportModalOpen, setHistoryReportModalOpen] = useState(false)
  const [reportScan, setReportScan] = useState(null)
  const containerRef = useRef(null)

  useEffect(() => {
    if (containerRef.current) {
      gsap.fromTo(
        containerRef.current.children,
        { opacity: 0, y: 15 },
        { opacity: 1, y: 0, duration: 0.5, stagger: 0.05, ease: 'power2.out' }
      )
    }
  }, [history])

  async function handleDelete(e, scanId) {
    e.stopPropagation()
    if (!window.confirm('Delete this clinical scan evaluation record?')) return
    setDeletingId(scanId)
    try {
      await apiDeleteScan(scanId)
      if (selectedScan?.id === scanId) setSelectedScan(null)
      onRefreshHistory()
    } catch (err) {
      alert(err.message || 'Failed to delete scan')
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-clinical">
        <div>
          <span className="text-[11px] font-sans font-bold uppercase tracking-wider text-teal-800">
            CHRONOLOGICAL RECORDS
          </span>
          <h2 className="font-sans text-2xl sm:text-3xl font-bold text-slate-900 mt-0.5">
            Patient Evaluation History
          </h2>
          <p className="text-xs text-slate-500 mt-1 font-sans">
            {history.length} documented diagnostic assessment{history.length === 1 ? '' : 's'} in clinical registry
          </p>
        </div>

        {!user && (
          <div className="flex items-center gap-2.5 rounded-xl bg-slate-50 border border-slate-200 px-4 py-2 text-xs text-slate-600">
            <span>💾 Scans cached locally in browser session.</span>
            <button
              onClick={onOpenAuth}
              className="font-semibold text-teal-800 hover:text-teal-900 hover:underline cursor-pointer"
            >
              Sign In to sync across clinical workstations
            </button>
          </div>
        )}
      </div>

      {history.length === 0 ? (
        <div className="bg-white rounded-2xl p-16 text-center border-2 border-dashed border-slate-300 shadow-clinical">
          <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-xl bg-teal-50 border border-teal-200 text-teal-800">
            <History className="h-7 w-7" />
          </div>
          <h3 className="font-sans text-lg font-bold text-slate-900">No Patient Records Yet</h3>
          <p className="mx-auto mt-1 max-w-md text-xs sm:text-sm text-slate-500">
            Run your first multimodal scan in the Clinical Scanner tab to establish baseline skin health and clinical trajectory.
          </p>
        </div>
      ) : (
        <div ref={containerRef} className="grid gap-6 lg:grid-cols-3">
          {/* Timeline Cards List */}
          <div className="lg:col-span-1 space-y-3 max-h-[700px] overflow-y-auto pr-1">
            {history.map((scan) => {
              const isSelected = (selectedScan?.id || history[0]?.id) === scan.id
              const dateStr = scan.created_at
                ? new Date(scan.created_at).toLocaleDateString(undefined, {
                    month: 'short',
                    day: 'numeric',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                  })
                : 'Recent Session'

              return (
                <div
                  key={scan.id}
                  onClick={() => setSelectedScan(scan)}
                  className={`p-4 rounded-xl cursor-pointer transition-all border ${
                    isSelected
                      ? 'bg-teal-50/60 border-2 border-teal-700 shadow-sm'
                      : 'bg-white border-slate-200 hover:border-slate-300 shadow-xs'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs text-teal-800 font-bold">
                      Record #{scan.id}
                    </span>
                    <span className="text-[11px] text-slate-400 font-sans flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {dateStr}
                    </span>
                  </div>

                  <div className="mt-2.5 flex items-center justify-between">
                    <div>
                      <p className="text-[11px] text-slate-500 font-sans">Barrier Health</p>
                      <p className="font-sans text-lg font-bold text-slate-900">
                        {Math.round(scan.skin_health_score ?? 0)}/100
                      </p>
                    </div>

                    <div className="text-right">
                      <p className="text-[11px] text-slate-500 font-sans">Cutaneous Risk</p>
                      <p className="font-sans text-lg font-bold text-rose-700">
                        {Math.round(scan.risk_percent ?? 0)}%
                      </p>
                    </div>
                  </div>

                  <div className="mt-2.5 pt-2 border-t border-slate-100 flex items-center justify-between">
                    <span className="text-xs text-slate-600 truncate max-w-[170px] font-medium font-sans">
                      {scan.severity_label || 'Grade 1: Moderate'}
                    </span>
                    <button
                      type="button"
                      disabled={deletingId === scan.id}
                      onClick={(e) => handleDelete(e, scan.id)}
                      className="text-slate-400 hover:text-rose-600 transition p-1 cursor-pointer"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Selected Record Detail Panel */}
          {(() => {
            const current = selectedScan || history[0]
            if (!current) return null

            return (
              <div className="lg:col-span-2 bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 space-y-6 shadow-clinical">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
                  <div>
                    <span className="text-[11px] font-sans text-teal-800 font-bold uppercase tracking-wider">
                      EVALUATION SUMMARY
                    </span>
                    <h3 className="font-sans text-xl font-bold text-slate-900 mt-0.5">
                      Record #{current.id} Clinical Assessment
                    </h3>
                    <p className="text-xs text-slate-500 font-sans mt-0.5">
                      Documented on {new Date(current.created_at).toLocaleString()}
                    </p>
                  </div>

                  <div className="flex flex-wrap items-center gap-2">
                    <button
                      onClick={() => {
                        setReportScan(current)
                        setHistoryReportModalOpen(true)
                      }}
                      className="flex items-center gap-1.5 rounded-xl bg-teal-700 hover:bg-teal-800 px-3.5 py-2 text-xs font-bold text-white shadow-sm transition cursor-pointer"
                      title="Download official clinical report for this evaluation"
                    >
                      <FileDown className="h-4 w-4" />
                      <span>Download Report</span>
                    </button>

                    <button
                      onClick={() => onReloadScan(current)}
                      className="flex items-center gap-1.5 rounded-xl border border-slate-300 bg-white hover:bg-slate-50 px-3.5 py-2 text-xs font-semibold text-slate-700 shadow-sm transition cursor-pointer"
                    >
                      <RotateCcw className="h-3.5 w-3.5" />
                      <span>Reload into Studio</span>
                    </button>
                  </div>
                </div>

                {/* Score Cards */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="rounded-xl bg-slate-50 p-3.5 border border-slate-200">
                    <p className="text-[11px] font-sans text-slate-500">Barrier Health</p>
                    <p className="text-2xl font-bold text-teal-800 font-mono mt-1">
                      {Math.round(current.skin_health_score ?? 0)}
                    </p>
                  </div>
                  <div className="rounded-xl bg-slate-50 p-3.5 border border-slate-200">
                    <p className="text-[11px] font-sans text-slate-500">Visual Risk</p>
                    <p className="text-2xl font-bold text-rose-700 font-mono mt-1">
                      {Math.round(current.risk_percent ?? 0)}%
                    </p>
                  </div>
                  <div className="rounded-xl bg-slate-50 p-3.5 border border-slate-200">
                    <p className="text-[11px] font-sans text-slate-500">Severity</p>
                    <p className="text-sm font-bold text-slate-900 truncate font-sans mt-2">
                      {current.severity_label || 'Moderate'}
                    </p>
                  </div>
                  <div className="rounded-xl bg-slate-50 p-3.5 border border-slate-200">
                    <p className="text-[11px] font-sans text-slate-500">Hormonal Risk</p>
                    <p className="text-2xl font-bold text-amber-800 font-mono mt-1">
                      {Math.round(current.data_scores?.hormonal ?? 0)}
                    </p>
                  </div>
                </div>

                {/* Notes if available */}
                {current.notes && (
                  <div className="rounded-xl bg-slate-50 border border-slate-200 p-4">
                    <p className="text-[11px] font-sans uppercase text-teal-800 font-bold mb-1">
                      Clinician Observation Notes
                    </p>
                    <p className="text-xs text-slate-700 font-sans leading-relaxed">{current.notes}</p>
                  </div>
                )}

                {/* Drivers */}
                {current.drivers?.length > 0 && (
                  <div>
                    <p className="text-[11px] font-sans uppercase text-slate-500 font-bold mb-2">
                      Top Identified Drivers
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {current.drivers.map((d) => (
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
            )
          })()}
        </div>
      )}

      {/* Historical Scan Medical Report Modal */}
      {reportScan && (
        <MedicalReportModal
          isOpen={historyReportModalOpen}
          onClose={() => {
            setHistoryReportModalOpen(false)
            setReportScan(null)
          }}
          result={{
            skin_health_score: reportScan.skin_health_score,
            final_risk_percent: reportScan.risk_percent,
            gauges: {
              skin_health: reportScan.skin_health_score,
              image_risk: reportScan.risk_percent,
              hormonal: reportScan.data_scores?.hormonal ?? 0,
              lifestyle: reportScan.data_scores?.lifestyle ?? 0,
              environmental: reportScan.data_scores?.environmental ?? 0,
            },
            image: {
              severity: reportScan.severity,
              severity_label: reportScan.severity_label,
              current_skin_condition:
                reportScan.image_attributes?.current_skin_condition || reportScan.severity_label,
              problem_areas: reportScan.image_attributes?.problem_areas || [],
              oiliness: reportScan.image_attributes?.oiliness ?? 0,
              pores: reportScan.image_attributes?.pores ?? 0,
              redness: reportScan.image_attributes?.redness ?? 0,
              dark_spots: reportScan.image_attributes?.dark_spots ?? 0,
              method: reportScan.image_attributes?.method || 'mobilenetv2_acne04_improved',
            },
            data: {
              hormonal_score: reportScan.data_scores?.hormonal ?? 0,
              lifestyle_score: reportScan.data_scores?.lifestyle ?? 0,
              environmental_score: reportScan.data_scores?.environmental ?? 0,
              combined_score: reportScan.data_scores?.combined ?? 0,
              drivers: reportScan.drivers || [],
              method: reportScan.data_scores?.method || 'random_forest_regressor',
            },
            recommendations: reportScan.recommendations || {},
            disclaimer:
              'Skinova is an educational clinical decision-support prototype, not a certified medical device.',
          }}
          user={user}
        />
      )}
    </div>
  )
}
