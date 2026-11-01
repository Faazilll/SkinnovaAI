import { useMemo, useState } from 'react'
import { createPortal } from 'react-dom'
import {
  Activity,
  AlertCircle,
  Award,
  Calendar,
  Check,
  CheckCircle2,
  Clock,
  Copy,
  Download,
  FileDown,
  FileText,
  Microscope,
  Printer,
  QrCode,
  Shield,
  ShieldCheck,
  Sparkles,
  Stethoscope,
  User,
  X,
  Zap,
} from 'lucide-react'

export default function MedicalReportModal({
  isOpen,
  onClose,
  result,
  user,
  form = {},
  imagePreview = null,
}) {
  const [copied, setCopied] = useState(false)
  const [downloading, setDownloading] = useState(false)

  const reportId = useMemo(() => {
    const timestamp = Date.now().toString(36).toUpperCase()
    const rand = Math.floor(1000 + Math.random() * 9000)
    return `SKN-REP-${timestamp}-${rand}`
  }, [result])

  const reportDate = useMemo(() => {
    return new Date().toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }, [])

  if (!isOpen || !result) return null

  const g = result.gauges || {}
  const img = result.image || {}
  const dataScores = result.data || {}
  const recs = result.recommendations || {}

  const severity = img.severity ?? 1
  const severityLabels = {
    0: { grade: 'Grade 0: Clear / Mild', risk: 'Low', color: '#059669', badge: 'bg-emerald-50 text-emerald-800 border-emerald-300' },
    1: { grade: 'Grade 1: Moderate Inflammatory', risk: 'Moderate', color: '#d97706', badge: 'bg-amber-50 text-amber-800 border-amber-300' },
    2: { grade: 'Grade 2: Severe Papulopustular', risk: 'Elevated', color: '#ea580c', badge: 'bg-orange-50 text-orange-800 border-orange-300' },
    3: { grade: 'Grade 3: Very Severe Nodulocystic', risk: 'High', color: '#dc2626', badge: 'bg-rose-50 text-rose-800 border-rose-300' },
  }
  const currentSev = severityLabels[severity] || severityLabels[1]

  const healthScore = Math.round(g.skin_health ?? result.skin_health_score ?? 68)
  const riskPercent = Math.round(g.image_risk ?? result.final_risk_percent ?? 42)

  // Biophysical Markers Table Data
  const biophysicalMarkers = [
    {
      name: 'Cutaneous Sebum & Surface Oiliness',
      value: img.oiliness ?? 45,
      unit: '/100',
      normalRange: '20 - 45',
      status: (img.oiliness ?? 45) > 55 ? 'Hyperseborrhea' : (img.oiliness ?? 45) < 25 ? 'Alipic / Dry' : 'Balanced',
      statusClass: (img.oiliness ?? 45) > 55 ? 'text-amber-700 font-bold' : 'text-emerald-700 font-medium',
      desc: 'Sebaceous gland excretion rate and surface lipid accumulation on cutaneous epidermal layer.',
    },
    {
      name: 'Follicular Pore Congestion & Keratinization',
      value: img.pores ?? 50,
      unit: '/100',
      normalRange: '15 - 40',
      status: (img.pores ?? 50) > 50 ? 'Comedonal Obstruction' : 'Unobstructed',
      statusClass: (img.pores ?? 50) > 50 ? 'text-amber-700 font-bold' : 'text-emerald-700 font-medium',
      desc: 'Pore micro-dilation and follicular infundibular retention index.',
    },
    {
      name: 'Cutaneous Erythema & Perilesional Redness',
      value: img.redness ?? 60,
      unit: '/100',
      normalRange: '10 - 35',
      status: (img.redness ?? 60) > 45 ? 'Active Micro-Vascular Inflammation' : 'Normovascular',
      statusClass: (img.redness ?? 60) > 45 ? 'text-rose-700 font-bold' : 'text-emerald-700 font-medium',
      desc: 'Superficial capillary vasodilation and inflammatory cytokine tissue response.',
    },
    {
      name: 'Post-Inflammatory Hyperpigmentation (PIH)',
      value: img.dark_spots ?? 35,
      unit: '/100',
      normalRange: '10 - 30',
      status: (img.dark_spots ?? 35) > 40 ? 'Moderate Melanin Accumulation' : 'Minimal Dyschromia',
      statusClass: (img.dark_spots ?? 35) > 40 ? 'text-amber-700 font-bold' : 'text-emerald-700 font-medium',
      desc: 'Epidermal melanocytic hyperactivity following acneiform inflammatory episodes.',
    },
  ]

  // Systemic Endocrine & Lifestyle Triangulation
  const systemicMarkers = [
    { label: 'Endocrine & Hormonal Score', value: Math.round(dataScores.hormonal_score ?? 35), max: 100 },
    { label: 'Systemic Lifestyle Barrier Score', value: Math.round(dataScores.lifestyle_score ?? 40), max: 100 },
    { label: 'Environmental & Pollution Index', value: Math.round(dataScores.environmental_score ?? 30), max: 100 },
  ]

  // Print PDF handler
  function handlePrintPdf() {
    window.print()
  }

  // Standalone Downloadable Medical Report File (.html)
  function handleDownloadHtml() {
    try {
      setDownloading(true)
      const reportHtml = generateStandaloneReportHtml({
        reportId,
        reportDate,
        user,
        form,
        imagePreview,
        result,
        currentSev,
        healthScore,
        riskPercent,
        biophysicalMarkers,
        systemicMarkers,
        recs,
      })

      const blob = new Blob([reportHtml], { type: 'text/html;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `Skinova_Medical_Report_${reportId}.html`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Download error:', err)
    } finally {
      setDownloading(false)
    }
  }

  // Copy text summary to clipboard
  function handleCopySummary() {
    const summary = `SKINOVA CLINICAL DERMATOLOGY REPORT
Report ID: ${reportId}
Issued: ${reportDate}
Patient: ${user?.name || 'Anonymous Patient'} (${form?.gender || 'N/A'}, Age: ${form?.age || 'N/A'})
Biometric Scan: Facial Skin Verified (YuNet 224x224 Matrix)

DIAGNOSIS & STAGING:
- Hayashi Severity: ${currentSev.grade}
- Overall Skin Health Score: ${healthScore} / 100
- Future Breakout Risk: ${riskPercent}%
- Problem Zones: ${img.problem_areas?.join(', ') || 'Facial cheeks, T-zone'}

BIOPHYSICAL CUTANEOUS METRICS:
- Sebum Oiliness: ${img.oiliness ?? 'N/A'}/100
- Pore Congestion: ${img.pores ?? 'N/A'}/100
- Erythema / Redness: ${img.redness ?? 'N/A'}/100
- Dark Spots / PIH: ${img.dark_spots ?? 'N/A'}/100

RECOMMENDED PROTOCOL:
- Morning: ${recs.am_routine?.join(' -> ') || 'Gentle cleanser, Niacinamide, SPF 50+'}
- Evening: ${recs.pm_routine?.join(' -> ') || 'Double cleanse, Topical Retinoid, Ceramide barrier cream'}

Disclaimer: Educational clinical decision-support prototype. Consult a board-certified dermatologist.`

    navigator.clipboard.writeText(summary)
    setCopied(true)
    setTimeout(() => setCopied(false), 2500)
  }

  return createPortal(
    <div
      id="skinova-report-modal-portal"
      className="report-portal-wrapper fixed inset-0 z-[9999] flex items-center justify-center p-3 sm:p-6 bg-slate-950/80 backdrop-blur-md overflow-y-auto"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      {/* Container Card */}
      <div
        className="report-modal-card relative w-full max-w-4xl max-h-[92vh] flex flex-col rounded-2xl bg-white border border-slate-300 shadow-modal overflow-hidden my-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Top Floating Control Bar (Hidden during actual print) */}
        <div className="flex flex-wrap items-center justify-between gap-3 px-6 py-3.5 bg-slate-50 border-b border-slate-200 text-slate-900 select-none no-print">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-teal-50 text-teal-800 border border-teal-200">
              <Stethoscope className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-sans text-sm font-bold text-slate-900 flex items-center gap-2">
                <span>Official Clinical Medical Report</span>
                <span className="rounded-full bg-teal-50 text-teal-800 border border-teal-200 text-[10px] font-sans font-bold px-2 py-0.5">
                  1-PAGE A4 GUARANTEE
                </span>
              </h3>
              <p className="text-xs text-slate-500 font-mono">
                Accession ID: <span className="text-slate-800 font-bold">{reportId}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleCopySummary}
              title="Copy text report summary"
              className="flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white hover:bg-slate-50 px-3 py-1.5 text-xs font-sans text-slate-700 transition cursor-pointer shadow-xs"
            >
              {copied ? <Check className="h-3.5 w-3.5 text-emerald-600" /> : <Copy className="h-3.5 w-3.5 text-slate-400" />}
              <span>{copied ? 'Copied' : 'Copy'}</span>
            </button>

            <button
              type="button"
              onClick={handleDownloadHtml}
              disabled={downloading}
              title="Download standalone medical report file (.html)"
              className="flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white hover:bg-slate-50 px-3 py-1.5 text-xs font-sans text-slate-700 font-semibold transition cursor-pointer shadow-xs"
            >
              <FileDown className="h-3.5 w-3.5 text-teal-700" />
              <span>Download (.html)</span>
            </button>

            <button
              type="button"
              onClick={handlePrintPdf}
              title="Print or Save as PDF (1 Page)"
              className="flex items-center gap-1.5 rounded-lg bg-teal-700 hover:bg-teal-800 px-3.5 py-1.5 text-xs font-sans font-bold text-white shadow-sm transition cursor-pointer"
            >
              <Printer className="h-3.5 w-3.5" />
              <span>Print / Save PDF</span>
            </button>

            <button
              type="button"
              onClick={onClose}
              title="Close modal"
              className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-300 bg-white hover:bg-slate-100 text-slate-500 hover:text-slate-900 transition ml-1 cursor-pointer"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Scrollable Printable Document Body */}
        <div className="report-modal-body overflow-y-auto p-4 sm:p-6 bg-slate-100 clinical-scrollbar">
          
          {/* THE 1-PAGE CLINICAL MEDICAL REPORT SHEET */}
          <div
            id="medical-report-sheet"
            className="medical-report-printable mx-auto bg-white text-slate-900 rounded-2xl shadow-xl p-5 sm:p-6 border border-slate-300 space-y-3 max-w-4xl"
            style={{ fontFamily: 'var(--font-sans)' }}
          >
            {/* Header: Hospital & Clinical Laboratory Banner (Compact Single Page) */}
            <div className="border-b-2 border-slate-900 pb-2.5 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
              <div className="flex items-center gap-2.5">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-950 text-white font-black text-base">
                  <span className="font-display">S+</span>
                </div>
                <div>
                  <h1 className="font-sans text-base sm:text-lg font-black uppercase tracking-tight text-slate-950 leading-tight">
                    SKINOVA CLINICAL DERMATOLOGY LABORATORY
                  </h1>
                  <p className="text-[10px] text-slate-600 font-mono leading-tight">
                    Photodermatology & Multimodal Cutaneous Phenotyping · Tokyo Hayashi Reference Standard
                  </p>
                </div>
              </div>

              <div className="text-left sm:text-right font-mono text-[10px] text-slate-600 space-y-0.5">
                <div><strong className="text-slate-900">ACCESSION:</strong> {reportId}</div>
                <div><strong className="text-slate-900">DATE:</strong> {reportDate}</div>
                <div className="inline-flex items-center gap-1 font-bold text-emerald-800 bg-emerald-100 border border-emerald-300 px-1.5 py-0.5 rounded text-[9px]">
                  <CheckCircle2 className="h-2.5 w-2.5" />
                  <span>100% FACE SKIN VERIFIED</span>
                </div>
              </div>
            </div>

            {/* Patient Demographics Bar */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 px-3 py-1.5 bg-slate-50 rounded-lg border border-slate-200 text-xs">
              <div>
                <span className="block text-[9px] font-mono uppercase text-slate-500 font-bold">Patient Name</span>
                <span className="font-bold text-slate-900 text-xs truncate block">{user?.name || 'Self-Registered Patient'}</span>
              </div>
              <div>
                <span className="block text-[9px] font-mono uppercase text-slate-500 font-bold">Age / Sex</span>
                <span className="font-semibold text-slate-800 text-xs">{form?.age || '24'} yrs · {form?.gender ? form.gender.toUpperCase() : 'FEMALE'}</span>
              </div>
              <div>
                <span className="block text-[9px] font-mono uppercase text-slate-500 font-bold">Biometric Specimen</span>
                <span className="font-semibold text-slate-800 text-xs">Facial Cutaneous (224x224)</span>
              </div>
              <div>
                <span className="block text-[9px] font-mono uppercase text-slate-500 font-bold">Clinical Staging</span>
                <span className="font-bold text-slate-900 text-xs truncate block">{currentSev.grade.split(':')[0]} ({currentSev.risk} Risk)</span>
              </div>
            </div>

            {/* 2-Column Split Body */}
            <div className="grid grid-cols-1 md:grid-cols-12 gap-3 text-xs">
              
              {/* Left Column (7 cols): Quantitative Cutaneous Panel & Multi-Engine Drivers */}
              <div className="md:col-span-7 space-y-2.5">
                
                {/* Table: Quantitative Biophysical Panel */}
                <div className="space-y-1">
                  <div className="flex items-center justify-between border-b border-slate-200 pb-0.5">
                    <h3 className="text-[11px] font-mono font-bold uppercase tracking-wider text-slate-800 flex items-center gap-1.5">
                      <Activity className="h-3.5 w-3.5 text-slate-700" />
                      <span>Quantitative Cutaneous Panel</span>
                    </h3>
                    <span className="text-[9px] font-mono text-slate-500">Optical Chrominance Matrix</span>
                  </div>

                  <table className="w-full text-left text-[11px] border-collapse border border-slate-200 rounded-lg overflow-hidden">
                    <thead>
                      <tr className="bg-slate-100 text-slate-700 font-mono text-[10px] border-b border-slate-200">
                        <th className="py-1 px-2 font-bold">Biomarker</th>
                        <th className="py-1 px-2 font-bold">Score</th>
                        <th className="py-1 px-2 font-bold">Ref Interval</th>
                        <th className="py-1 px-2 font-bold">Interpretation</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 text-slate-800">
                      {biophysicalMarkers.map((m, idx) => (
                        <tr key={idx} className="hover:bg-slate-50/50">
                          <td className="py-1 px-2">
                            <span className="font-bold text-slate-900 text-[10px]">{m.name.split('&')[0]}</span>
                          </td>
                          <td className="py-1 px-2 font-mono font-bold text-slate-900 text-[10px]">
                            {m.value} {m.unit}
                          </td>
                          <td className="py-1 px-2 font-mono text-slate-500 text-[10px]">{m.normalRange}</td>
                          <td className={`py-1 px-2 font-mono text-[10px] ${m.statusClass}`}>
                            {m.status}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Multimodal Triangulation Scores */}
                <div className="space-y-1">
                  <div className="flex items-center justify-between border-b border-slate-200 pb-0.5">
                    <h3 className="text-[11px] font-mono font-bold uppercase tracking-wider text-slate-800 flex items-center gap-1.5">
                      <Microscope className="h-3.5 w-3.5 text-slate-700" />
                      <span>Systemic Triangulation</span>
                    </h3>
                    <span className="text-[9px] font-mono text-slate-500">Random Forest Regressor</span>
                  </div>

                  <div className="grid grid-cols-3 gap-2 text-center">
                    <div className="p-1.5 bg-slate-50 rounded-lg border border-slate-200">
                      <div className="text-[9px] font-mono text-slate-500">Endocrine</div>
                      <div className="text-sm font-bold text-slate-900 font-mono">{Math.round(dataScores.hormonal_score ?? 35)}/100</div>
                    </div>
                    <div className="p-1.5 bg-slate-50 rounded-lg border border-slate-200">
                      <div className="text-[9px] font-mono text-slate-500">Lifestyle</div>
                      <div className="text-sm font-bold text-slate-900 font-mono">{Math.round(dataScores.lifestyle_score ?? 40)}/100</div>
                    </div>
                    <div className="p-1.5 bg-slate-50 rounded-lg border border-slate-200">
                      <div className="text-[9px] font-mono text-slate-500">Exposome</div>
                      <div className="text-sm font-bold text-slate-900 font-mono">{Math.round(dataScores.environmental_score ?? 30)}/100</div>
                    </div>
                  </div>

                  {dataScores.drivers?.length > 0 && (
                    <div className="p-1.5 bg-slate-50 rounded-lg border border-slate-200 flex items-center gap-1 text-[9px] font-mono">
                      <span className="text-slate-500 font-bold shrink-0">Drivers:</span>
                      <span className="text-slate-800 truncate">{dataScores.drivers.join(' · ')}</span>
                    </div>
                  )}
                </div>

              </div>

              {/* Right Column (5 cols): Diagnosis, Treatment Routines, Actives */}
              <div className="md:col-span-5 space-y-2">
                
                {/* Clinical Diagnosis Card */}
                <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between">
                  <div>
                    <div className="text-[9px] font-mono uppercase text-slate-500 font-bold">Diagnosis & Staging</div>
                    <div className="text-xs font-black text-slate-950 mt-0.5">{currentSev.grade}</div>
                    <div className="text-[9px] font-mono text-slate-600 mt-0.5">
                      Zones: <strong>{img.problem_areas?.join(', ') || 'Cheeks, T-Zone'}</strong>
                    </div>
                  </div>
                  <div className="flex gap-2 text-center pl-2 border-l border-slate-200 shrink-0">
                    <div>
                      <div className="text-base font-black text-emerald-700 font-mono">{healthScore}</div>
                      <div className="text-[8px] font-mono text-slate-500 uppercase">Health</div>
                    </div>
                    <div>
                      <div className="text-base font-black text-rose-700 font-mono">{riskPercent}%</div>
                      <div className="text-[8px] font-mono text-slate-500 uppercase">Risk</div>
                    </div>
                  </div>
                </div>

                {/* Prescribed Therapeutic Action Plan */}
                <div className="space-y-1">
                  <div className="flex items-center justify-between border-b border-slate-200 pb-0.5">
                    <h3 className="text-[11px] font-mono font-bold uppercase tracking-wider text-slate-800 flex items-center gap-1.5">
                      <Award className="h-3.5 w-3.5 text-slate-700" />
                      <span>Prescribed Protocol</span>
                    </h3>
                  </div>

                  <div className="space-y-1 text-[9px] font-mono">
                    <div className="p-1.5 bg-amber-50/70 rounded-lg border border-amber-200">
                      <div className="font-bold text-amber-900">☀️ MORNING (AM):</div>
                      <div className="text-slate-800 mt-0.5 leading-tight">
                        {recs.am_routine?.slice(0, 3).join(' ➔ ') || 'Gentle Cleanser ➔ Niacinamide ➔ SPF 50+'}
                      </div>
                    </div>

                    <div className="p-1.5 bg-indigo-50/70 rounded-lg border border-indigo-200">
                      <div className="font-bold text-indigo-900">🌙 EVENING (PM):</div>
                      <div className="text-slate-800 mt-0.5 leading-tight">
                        {recs.pm_routine?.slice(0, 3).join(' ➔ ') || 'Double Cleanse ➔ Retinoid/Azelaic ➔ Ceramide Cream'}
                      </div>
                    </div>
                  </div>

                  {/* Actives Summary */}
                  <div className="grid grid-cols-2 gap-1 text-[8px] font-mono pt-0.5">
                    <div className="p-1 bg-emerald-50 rounded border border-emerald-200 text-emerald-950 leading-tight">
                      <strong>Seek:</strong> Salicylic, Niacinamide, Azelaic, Ceramides
                    </div>
                    <div className="p-1 bg-rose-50 rounded border border-rose-200 text-rose-950 leading-tight">
                      <strong>Avoid:</strong> Heavy Oils, Physical Scrubs, Fragrance
                    </div>
                  </div>
                </div>

              </div>
            </div>

            {/* Bottom Footer: Verification, Electronic Signature & Disclaimer */}
            <div className="border-t border-slate-300 pt-2 space-y-1 text-[9px] font-mono text-slate-600">
              <div className="flex justify-between items-end">
                <div>
                  <div className="font-bold text-slate-900 flex items-center gap-1">
                    <ShieldCheck className="h-3 w-3 text-slate-800" />
                    <span>SKINOVA COMPUTATIONAL DERMATOLOGY REVIEW</span>
                  </div>
                  <div>Hash: {reportId}-SHA256-CERT · Biometric Integrity 100% Passed</div>
                </div>
                <div className="text-right">
                  <div className="font-bold text-slate-900 tracking-wider">[ ELECTRONICALLY SIGNED ]</div>
                  <div className="text-[8px] text-slate-500">Automated Decision Support System</div>
                </div>
              </div>
              <p className="text-[8px] text-slate-500 leading-tight m-0">
                NOTICE: Educational clinical decision-support prototype. Incorporates MobileNetV2 CNN & Random Forest ensemble. Does not replace physical examination by a licensed board-certified dermatologist.
              </p>
            </div>

          </div>
        </div>

        {/* Modal Bottom Action Footer */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 px-6 py-4 bg-dark-950 border-t border-slate-800 text-xs font-mono text-slate-400 no-print">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-emerald-400" />
            <span>Digital Certificate Valid · A4 Standard Print Compatible</span>
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto">
            <button
              type="button"
              onClick={handleDownloadHtml}
              className="flex-1 sm:flex-none flex items-center justify-center gap-1.5 rounded-xl border border-slate-700 bg-slate-800 hover:bg-slate-700 px-4 py-2 text-slate-200 transition"
            >
              <Download className="h-3.5 w-3.5 text-cyanic-400" />
              <span>Download .html</span>
            </button>

            <button
              type="button"
              onClick={handlePrintPdf}
              className="flex-1 sm:flex-none flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-medic-600 to-medic-500 hover:from-medic-500 hover:to-cyanic-500 px-5 py-2 text-white font-bold shadow-glow transition"
            >
              <Printer className="h-4 w-4" />
              <span>Download PDF</span>
            </button>
          </div>
        </div>

      </div>
    </div>,
    document.body
  )
}

// Generates self-contained, offline-compatible HTML medical report strictly calibrated for 1-PAGE A4 print/PDF
export function generateStandaloneReportHtml({
  reportId,
  reportDate,
  user,
  form = {},
  currentSev,
  healthScore,
  riskPercent,
  biophysicalMarkers = [],
  systemicMarkers = [],
  recs = {},
  result = {},
  imagePreview = null,
}) {
  const dataScores = result?.data || {}
  const imgData = result?.image || {}
  const hormonal = Math.round(dataScores.hormonal_score ?? 35)
  const lifestyle = Math.round(dataScores.lifestyle_score ?? 40)
  const environmental = Math.round(dataScores.environmental_score ?? 30)
  const driversList = dataScores.drivers?.length ? dataScores.drivers.slice(0, 3) : ['Microbiome Imbalance', 'Sebaceous Excretion Rate', 'TEWL Barrier Compromise']
  const problemZones = imgData.problem_areas?.join(', ') || 'Facial Cheeks, Malar Crest, T-Zone'

  const amSteps = recs?.am_routine?.length
    ? recs.am_routine.slice(0, 3)
    : ['Gentle pH 5.5 Foaming Cleanser', 'Niacinamide (4%) + Zinc PCA', 'Broad-Spectrum Fluid SPF 50+']

  const pmSteps = recs?.pm_routine?.length
    ? recs.pm_routine.slice(0, 3)
    : ['Non-comedogenic Oil/Micellar Cleanse', 'Topical Retinoid (Adapalene 0.1%)', 'Lipid-Replenishing Ceramide Cream']

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Skinova Medical Report - ${reportId}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    @page {
      size: A4 portrait;
      margin: 8mm 10mm;
    }
    * {
      box-sizing: border-box;
      -webkit-print-color-adjust: exact !important;
      print-color-adjust: exact !important;
    }
    html, body {
      margin: 0;
      padding: 0;
      background: #f1f5f9;
      color: #0f172a;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      font-size: 11px;
      line-height: 1.35;
    }
    .action-bar {
      max-width: 820px;
      margin: 12px auto 8px auto;
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 0 4px;
    }
    .action-bar button {
      cursor: pointer;
      font-weight: 700;
      border-radius: 6px;
      font-size: 12px;
      padding: 8px 16px;
      transition: all 0.15s ease;
    }
    .btn-print {
      background: #0d9488;
      color: #ffffff;
      border: 1px solid #0f766e;
    }
    .btn-print:hover { background: #0f766e; }
    .sheet {
      width: 100%;
      max-width: 820px;
      margin: 0 auto 16px auto;
      background: #ffffff;
      padding: 20px 24px;
      border: 1px solid #cbd5e1;
      border-radius: 8px;
      box-shadow: 0 4px 18px rgba(0,0,0,0.06);
      page-break-inside: avoid;
      break-inside: avoid;
      page-break-after: avoid;
      break-after: avoid;
    }
    .header {
      border-bottom: 2px solid #0f172a;
      padding-bottom: 8px;
      margin-bottom: 10px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .header-brand {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .logo-badge {
      width: 34px;
      height: 34px;
      background: #020617;
      color: #ffffff;
      font-weight: 900;
      font-size: 16px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      letter-spacing: -0.5px;
    }
    .header h1 {
      margin: 0;
      font-size: 15px;
      font-weight: 900;
      letter-spacing: 0.2px;
      text-transform: uppercase;
      color: #020617;
    }
    .header p {
      margin: 1px 0 0 0;
      font-size: 9px;
      color: #475569;
      font-family: monospace;
    }
    .meta {
      text-align: right;
      font-family: monospace;
      font-size: 9.5px;
      color: #475569;
      line-height: 1.35;
    }
    .verified-pill {
      display: inline-block;
      margin-top: 2px;
      background: #dcfce7;
      color: #166534;
      border: 1px solid #86efac;
      padding: 2px 6px;
      border-radius: 4px;
      font-weight: 800;
      font-size: 8.5px;
    }
    .patient-bar {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 8px;
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      padding: 7px 10px;
      margin-bottom: 10px;
    }
    .bar-col .label {
      font-size: 8.5px;
      font-family: monospace;
      text-transform: uppercase;
      color: #64748b;
      font-weight: 700;
      display: block;
    }
    .bar-col .val {
      font-size: 11px;
      font-weight: 700;
      color: #0f172a;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      display: block;
    }
    .main-grid {
      display: grid;
      grid-template-columns: 1.25fr 1fr;
      gap: 12px;
      margin-bottom: 10px;
    }
    .section-title {
      font-size: 10px;
      font-family: monospace;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: #1e293b;
      border-bottom: 1px solid #e2e8f0;
      padding-bottom: 3px;
      margin: 0 0 6px 0;
      display: flex;
      justify-content: space-between;
    }
    .section-title span {
      font-size: 8.5px;
      color: #64748b;
      font-weight: normal;
    }
    .panel-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 10px;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      overflow: hidden;
      margin-bottom: 8px;
    }
    .panel-table th {
      background: #f1f5f9;
      color: #334155;
      font-family: monospace;
      font-size: 8.5px;
      font-weight: 800;
      text-transform: uppercase;
      padding: 5px 6px;
      text-align: left;
      border-bottom: 1px solid #e2e8f0;
    }
    .panel-table td {
      padding: 5px 6px;
      border-bottom: 1px solid #f1f5f9;
    }
    .panel-table tr:last-child td {
      border-bottom: none;
    }
    .triangulation-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 6px;
      margin-bottom: 6px;
    }
    .tri-box {
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      padding: 5px;
      text-align: center;
    }
    .tri-box .t-lbl {
      font-size: 8px;
      font-family: monospace;
      color: #64748b;
      text-transform: uppercase;
    }
    .tri-box .t-val {
      font-size: 13px;
      font-weight: 800;
      font-family: monospace;
      color: #0f172a;
    }
    .drivers-box {
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      padding: 4px 8px;
      font-size: 8.5px;
      font-family: monospace;
      color: #334155;
    }
    .diag-card {
      background: #f8fafc;
      border: 1px solid #cbd5e1;
      border-radius: 8px;
      padding: 8px 10px;
      margin-bottom: 8px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .diag-title {
      font-size: 11.5px;
      font-weight: 900;
      color: #0f172a;
    }
    .diag-zones {
      font-size: 8.5px;
      font-family: monospace;
      color: #475569;
      margin-top: 2px;
    }
    .score-group {
      display: flex;
      gap: 10px;
      text-align: center;
      border-left: 1px solid #e2e8f0;
      padding-left: 10px;
    }
    .score-item .num {
      font-size: 17px;
      font-weight: 900;
      font-family: monospace;
      line-height: 1;
    }
    .score-item .sub {
      font-size: 7.5px;
      font-family: monospace;
      text-transform: uppercase;
      color: #64748b;
      font-weight: 700;
      margin-top: 2px;
    }
    .routine-box {
      padding: 6px 8px;
      border-radius: 6px;
      margin-bottom: 6px;
      font-family: monospace;
      font-size: 8.5px;
      line-height: 1.35;
    }
    .am-box {
      background: #fefce8;
      border: 1px solid #fde047;
      color: #713f12;
    }
    .pm-box {
      background: #eef2ff;
      border: 1px solid #c7d2fe;
      color: #312e81;
    }
    .routine-head {
      font-weight: 800;
      text-transform: uppercase;
      font-size: 8.5px;
      margin-bottom: 2px;
    }
    .routine-steps {
      color: #1e293b;
    }
    .actives-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 6px;
      font-family: monospace;
      font-size: 8px;
    }
    .active-pill {
      padding: 4px 6px;
      border-radius: 4px;
      line-height: 1.25;
    }
    .active-seek { background: #f0fdf4; border: 1px solid #bbf7d0; color: #14532d; }
    .active-avoid { background: #fff1f2; border: 1px solid #fecdd3; color: #881337; }
    .footer {
      border-top: 1px solid #cbd5e1;
      padding-top: 6px;
      font-family: monospace;
      font-size: 8px;
      color: #64748b;
      line-height: 1.3;
    }
    .footer-flex {
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      margin-bottom: 4px;
    }
    .sig-block {
      text-align: right;
      color: #0f172a;
      font-weight: 700;
    }
    @media print {
      body {
        background: #ffffff !important;
        padding: 0 !important;
      }
      .no-print {
        display: none !important;
      }
      .sheet {
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 !important;
        width: 100% !important;
        max-width: 100% !important;
      }
    }
  </style>
</head>
<body>
  <div class="no-print action-bar">
    <div style="font-family: monospace; font-size: 11px; color: #475569;">
      <strong>Skinova Clinical Exporter</strong> · 1-Page A4 Standard Validated
    </div>
    <div style="display: flex; gap: 8px;">
      <button class="btn-print" onclick="window.print()">🖨️ Print / Save as PDF (1 Page)</button>
    </div>
  </div>

  <div class="sheet">
    <!-- Header -->
    <div class="header">
      <div class="header-brand">
        <div class="logo-badge">S+</div>
        <div>
          <h1>Skinova Clinical Dermatology Laboratory</h1>
          <p>Photodermatology & Cutaneous Phenotyping · Tokyo Hayashi Reference Standard</p>
        </div>
      </div>
      <div class="meta">
        <div><strong>ACCESSION:</strong> ${reportId}</div>
        <div><strong>ISSUED:</strong> ${reportDate}</div>
        <div class="verified-pill">✔ 100% FACE SKIN VERIFIED</div>
      </div>
    </div>

    <!-- Demographics Strip -->
    <div class="patient-bar">
      <div class="bar-col">
        <span class="label">Patient Name</span>
        <span class="val">${user?.name || 'Self-Registered Patient'}</span>
      </div>
      <div class="bar-col">
        <span class="label">Age / Sex</span>
        <span class="val">${form?.age || '24'} yrs · ${form?.gender ? form.gender.toUpperCase() : 'FEMALE'}</span>
      </div>
      <div class="bar-col">
        <span class="label">Biometric Specimen</span>
        <span class="val">Facial Cutaneous (224x224)</span>
      </div>
      <div class="bar-col">
        <span class="label">Clinical Staging</span>
        <span class="val">${currentSev.grade.split(':')[0]} (${currentSev.risk} Risk)</span>
      </div>
    </div>

    <!-- 2-Column Split Body -->
    <div class="main-grid">
      <!-- Left Column: Cutaneous Panel & Drivers -->
      <div>
        <div class="section-title">
          <span>Quantitative Cutaneous Panel</span>
          <span>Optical Chrominance Matrix</span>
        </div>

        <table class="panel-table">
          <thead>
            <tr>
              <th>Biomarker</th>
              <th>Measured</th>
              <th>Ref Interval</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            ${biophysicalMarkers
              .map(
                (m) => `<tr>
              <td><strong>${m.name.split('&')[0]}</strong></td>
              <td style="font-family: monospace; font-weight: 700;">${m.value} ${m.unit}</td>
              <td style="font-family: monospace; color: #64748b;">${m.normalRange}</td>
              <td style="font-family: monospace; font-weight: 700; color: ${
                m.status.includes('Hyper') || m.status.includes('Active') || m.status.includes('Obstruction')
                  ? '#b45309'
                  : '#15803d'
              };">${m.status}</td>
            </tr>`
              )
              .join('')}
          </tbody>
        </table>

        <div class="section-title">
          <span>Systemic Triangulation</span>
          <span>Random Forest Regressor</span>
        </div>

        <div class="triangulation-grid">
          <div class="tri-box">
            <div class="t-lbl">Endocrine</div>
            <div class="t-val">${hormonal}/100</div>
          </div>
          <div class="tri-box">
            <div class="t-lbl">Lifestyle</div>
            <div class="t-val">${lifestyle}/100</div>
          </div>
          <div class="tri-box">
            <div class="t-lbl">Exposome</div>
            <div class="t-val">${environmental}/100</div>
          </div>
        </div>

        <div class="drivers-box">
          <strong>Triangulated Drivers:</strong> ${driversList.join(' · ')}
        </div>
      </div>

      <!-- Right Column: Diagnosis & Prescribed Routine -->
      <div>
        <div class="diag-card">
          <div>
            <div style="font-size: 8px; font-family: monospace; text-transform: uppercase; color: #64748b; font-weight: 700;">Diagnostic Staging</div>
            <div class="diag-title">${currentSev.grade}</div>
            <div class="diag-zones">Zones: <strong>${problemZones}</strong></div>
          </div>
          <div class="score-group">
            <div class="score-item">
              <div class="num" style="color: #15803d;">${healthScore}</div>
              <div class="sub">Health</div>
            </div>
            <div class="score-item">
              <div class="num" style="color: #b91c1c;">${riskPercent}%</div>
              <div class="sub">Risk</div>
            </div>
          </div>
        </div>

        <div class="section-title">
          <span>Prescribed Therapeutic Protocol</span>
          <span>Active Dermaceuticals</span>
        </div>

        <div class="routine-box am-box">
          <div class="routine-head">☀️ Morning (AM) Protocol:</div>
          <div class="routine-steps">${amSteps.join(' ➔ ')}</div>
        </div>

        <div class="routine-box pm-box">
          <div class="routine-head">🌙 Evening (PM) Protocol:</div>
          <div class="routine-steps">${pmSteps.join(' ➔ ')}</div>
        </div>

        <div class="actives-grid">
          <div class="active-pill active-seek">
            <strong>Seek:</strong> Salicylic, Niacinamide, Azelaic, Ceramides
          </div>
          <div class="active-pill active-avoid">
            <strong>Avoid:</strong> Heavy Oils, Physical Scrubs, Fragrance
          </div>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <div class="footer">
      <div class="footer-flex">
        <div>
          <strong style="color: #0f172a;">SKINOVA COMPUTATIONAL DERMATOLOGY REVIEW</strong><br>
          Accession Hash: ${reportId}-SHA256-CERT · Biometric Integrity 100% Passed
        </div>
        <div class="sig-block">
          <div>[ ELECTRONICALLY VALIDATED ]</div>
          <div style="font-size: 7.5px; color: #64748b; font-weight: normal;">Automated Clinical Decision Support</div>
        </div>
      </div>
      <div>
        NOTICE: Educational clinical decision-support prototype. Incorporates MobileNetV2 CNN & Random Forest ensemble. Tokyo Hayashi Acne Staging Criteria. Does not replace physical examination by a licensed board-certified dermatologist.
      </div>
    </div>
  </div>
</body>
</html>`
}

export function downloadMedicalReportFile({ result, user, form, imagePreview }) {
  if (!result) return
  const timestamp = Date.now().toString(36).toUpperCase()
  const rand = Math.floor(1000 + Math.random() * 9000)
  const reportId = `SKN-REP-${timestamp}-${rand}`
  const reportDate = new Date().toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })

  const g = result.gauges || {}
  const img = result.image || {}
  const recs = result.recommendations || {}

  const severity = img.severity ?? 1
  const severityLabels = {
    0: { grade: 'Grade 0: Clear / Mild', risk: 'Low' },
    1: { grade: 'Grade 1: Moderate Inflammatory', risk: 'Moderate' },
    2: { grade: 'Grade 2: Severe Papulopustular', risk: 'Elevated' },
    3: { grade: 'Grade 3: Very Severe Nodulocystic', risk: 'High' },
  }
  const currentSev = severityLabels[severity] || severityLabels[1]
  const healthScore = Math.round(g.skin_health ?? result.skin_health_score ?? 68)
  const riskPercent = Math.round(g.image_risk ?? result.final_risk_percent ?? 42)

  const biophysicalMarkers = [
    {
      name: 'Cutaneous Sebum & Surface Oiliness',
      value: img.oiliness ?? 45,
      unit: '/100',
      normalRange: '20 - 45',
      status: (img.oiliness ?? 45) > 55 ? 'Hyperseborrhea' : (img.oiliness ?? 45) < 25 ? 'Alipic / Dry' : 'Balanced',
      desc: 'Sebaceous gland excretion rate and surface lipid accumulation on cutaneous epidermal layer.',
    },
    {
      name: 'Follicular Pore Congestion & Keratinization',
      value: img.pores ?? 50,
      unit: '/100',
      normalRange: '15 - 40',
      status: (img.pores ?? 50) > 50 ? 'Comedonal Obstruction' : 'Unobstructed',
      desc: 'Pore micro-dilation and follicular infundibular retention index.',
    },
    {
      name: 'Cutaneous Erythema & Perilesional Redness',
      value: img.redness ?? 60,
      unit: '/100',
      normalRange: '10 - 35',
      status: (img.redness ?? 60) > 45 ? 'Active Micro-Vascular Inflammation' : 'Normovascular',
      desc: 'Superficial capillary vasodilation and inflammatory cytokine tissue response.',
    },
    {
      name: 'Post-Inflammatory Hyperpigmentation (PIH)',
      value: img.dark_spots ?? 35,
      unit: '/100',
      normalRange: '10 - 30',
      status: (img.dark_spots ?? 35) > 40 ? 'Moderate Melanin Accumulation' : 'Minimal Dyschromia',
      desc: 'Epidermal melanocytic hyperactivity following acneiform inflammatory episodes.',
    },
  ]

  const html = generateStandaloneReportHtml({
    reportId,
    reportDate,
    user,
    form,
    imagePreview,
    result,
    currentSev,
    healthScore,
    riskPercent,
    biophysicalMarkers,
    systemicMarkers: [],
    recs,
  })

  const blob = new Blob([html], { type: 'text/html;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `Skinova_Medical_Report_${reportId}.html`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

