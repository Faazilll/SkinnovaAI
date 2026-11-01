import { useState } from 'react'
import {
  Activity,
  AlertCircle,
  Binary,
  BrainCircuit,
  Calculator,
  ChevronDown,
  ChevronUp,
  Clock,
  Cpu,
  Database,
  Eye,
  FileSpreadsheet,
  FileText,
  HelpCircle,
  Info,
  Layers,
  Microscope,
  Scale,
  ShieldAlert,
} from 'lucide-react'

export default function FusionBreakdown({ result }) {
  const [expandedDetails, setExpandedDetails] = useState(true)

  if (!result) return null

  const img = result.image || {}
  const data = result.data || {}
  const breakdown = result.fusion_breakdown || {}
  const weights = result.weights || { image: 0.55, data: 0.45 }

  const imageRisk = Number(img.risk_percent ?? result.gauges?.image_risk ?? 50)
  const dataCombined = Number(data.combined_score ?? 50)
  const finalRisk = Number(result.final_risk_percent ?? 50)
  const healthScore = Number(result.skin_health_score ?? 50)

  // Calculated arithmetic steps
  const visualContrib = (imageRisk * weights.image).toFixed(2)
  const systemicContrib = (dataCombined * weights.data).toFixed(2)
  const unclampedSum = (imageRisk * weights.image + dataCombined * weights.data).toFixed(2)

  // Probabilities distribution
  const probs = img.class_probabilities || {}
  const classNames = {
    '0': 'Clear / Mild',
    '1': 'Moderate',
    '2': 'Severe',
    '3': 'Very Severe',
  }

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 space-y-6 shadow-clinical">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full bg-teal-50 border border-teal-200 px-3 py-0.5 text-[11px] font-sans font-semibold uppercase tracking-wider text-teal-800">
            <Layers className="h-3.5 w-3.5 text-teal-700" />
            <span>Multimodal Decision Support Architecture</span>
          </div>
          <h3 className="font-sans text-xl sm:text-2xl font-bold text-slate-900 mt-1 flex items-center gap-2">
            <span>Transparent Multimodal Fusion Breakdown</span>
          </h3>
          <p className="text-xs text-slate-500 font-sans mt-0.5">
            Separating computer vision inference from systemic biomarker rules with complete mathematical transparency.
          </p>
        </div>

        <button
          type="button"
          onClick={() => setExpandedDetails(!expandedDetails)}
          className="self-start md:self-auto flex items-center gap-1.5 rounded-xl border border-slate-300 bg-white hover:bg-slate-50 px-3.5 py-2 text-xs font-sans font-medium text-slate-700 shadow-sm transition cursor-pointer"
        >
          {expandedDetails ? (
            <>
              <ChevronUp className="h-4 w-4 text-slate-500" />
              <span>Compact View</span>
            </>
          ) : (
            <>
              <ChevronDown className="h-4 w-4 text-slate-500" />
              <span>Inspect Full Arithmetic</span>
            </>
          )}
        </button>
      </div>

      {/* 3 Distinct Component Output Cards */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Component 1: Trained Image Model Assessment */}
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-5 flex flex-col justify-between space-y-4">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="inline-flex items-center gap-1.5 rounded-md bg-teal-100/70 border border-teal-200 px-2 py-0.5 text-[10px] font-sans font-bold uppercase tracking-wider text-teal-800">
                <BrainCircuit className="h-3.5 w-3.5 text-teal-700" />
                <span>Component 1 of 3</span>
              </span>
              <span className="text-[11px] font-mono text-slate-500">Trained CNN</span>
            </div>

            <div>
              <h4 className="font-sans text-base font-bold text-slate-900">
                Visual Lesion Model
              </h4>
              <p className="text-xs text-slate-500 font-sans mt-0.5">
                Model: <span className="text-slate-800 font-semibold font-mono">{img.method || 'MobileNetV2 ACNE04'}</span>
              </p>
            </div>

            {/* Classification & Confidence */}
            <div className="rounded-lg bg-white border border-slate-200 p-3 space-y-2 font-mono text-xs shadow-sm">
              <div className="flex justify-between items-center">
                <span className="text-slate-500 font-sans">Hayashi Grade:</span>
                <span className="text-teal-800 font-bold">
                  Grade {img.severity}: {img.severity_label}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-500 font-sans">Visual Risk Contribution:</span>
                <span className="text-slate-900 font-bold">{imageRisk}%</span>
              </div>
              <div className="flex justify-between items-center text-[11px]">
                <span className="text-slate-500 font-sans">Face Detector:</span>
                <span className={img.face_detected ? 'text-emerald-700 font-bold' : 'text-amber-700 font-bold'}>
                  {img.face_detected ? 'YuNet ONNX Face BBox' : 'Center Crop Fallback'}
                </span>
              </div>
            </div>

            {/* Softmax Probability Bars */}
            {Object.keys(probs).length > 0 && (
              <div className="space-y-1.5 pt-1">
                <span className="text-[10px] font-sans text-slate-500 uppercase tracking-wider font-bold">
                  Softmax Probability Distribution:
                </span>
                {Object.entries(probs).map(([k, v]) => (
                  <div key={k} className="space-y-0.5">
                    <div className="flex justify-between text-[11px] font-mono text-slate-700">
                      <span>
                        G{k} ({classNames[k] || k}):
                      </span>
                      <span className="font-semibold">{(Number(v) * 100).toFixed(1)}%</span>
                    </div>
                    <div className="h-1.5 w-full bg-slate-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-teal-700 rounded-full"
                        style={{ width: `${Math.min(100, Number(v) * 100)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="pt-2 border-t border-slate-200 text-[11px] text-slate-500 font-sans">
            <span>Empirical CNN inference on ACNE04 facial benchmark split.</span>
          </div>
        </div>

        {/* Component 2: Questionnaire Assessment */}
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-5 flex flex-col justify-between space-y-4">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="inline-flex items-center gap-1.5 rounded-md bg-sky-100/70 border border-sky-200 px-2 py-0.5 text-[10px] font-sans font-bold uppercase tracking-wider text-sky-800">
                <FileSpreadsheet className="h-3.5 w-3.5 text-sky-700" />
                <span>Component 2 of 3</span>
              </span>
              <span className="text-[11px] font-mono text-slate-500">ML / Regressor</span>
            </div>

            <div>
              <h4 className="font-sans text-base font-bold text-slate-900">Systemic Biomarkers</h4>
              <p className="text-xs text-slate-500 font-sans mt-0.5">
                Model: <span className="text-slate-800 font-semibold font-mono">{data.method || 'Random Forest Regressor'}</span>
              </p>
            </div>

            {/* Category Subscores */}
            <div className="rounded-lg bg-white border border-slate-200 p-3 space-y-2 font-mono text-xs shadow-sm">
              <div className="flex justify-between items-center">
                <span className="text-slate-500 font-sans">Endocrine & Hormonal:</span>
                <span className="text-amber-800 font-bold">{data.hormonal_score ?? 0} / 100</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-500 font-sans">Systemic Lifestyle:</span>
                <span className="text-sky-800 font-bold">{data.lifestyle_score ?? 0} / 100</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-500 font-sans">Exposome & Climate:</span>
                <span className="text-teal-800 font-bold">{data.environmental_score ?? 0} / 100</span>
              </div>
              <div className="flex justify-between items-center pt-1 border-t border-slate-200 text-slate-900 font-bold">
                <span className="font-sans">Systemic Combined:</span>
                <span>{dataCombined} / 100</span>
              </div>
            </div>

            {/* Contributing Drivers */}
            {data.drivers?.length > 0 && (
              <div className="space-y-1.5 pt-1">
                <span className="text-[10px] font-sans text-slate-500 uppercase tracking-wider font-bold">
                  Top Contributing Risk Drivers:
                </span>
                <div className="flex flex-wrap gap-1">
                  {data.drivers.slice(0, 4).map((d) => (
                    <span
                      key={d}
                      className="rounded-md bg-white border border-slate-200 px-2 py-0.5 text-[11px] font-sans text-slate-700 shadow-xs"
                    >
                      {d}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="pt-2 border-t border-slate-200 text-[11px] text-slate-500 font-sans">
            <span>Multi-system risk vector mapped from 21 patient biomarker inputs.</span>
          </div>
        </div>

        {/* Component 3: Final Multimodal Fusion Synthesis */}
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-5 flex flex-col justify-between space-y-4">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="inline-flex items-center gap-1.5 rounded-md bg-emerald-100/70 border border-emerald-200 px-2 py-0.5 text-[10px] font-sans font-bold uppercase tracking-wider text-emerald-800">
                <Calculator className="h-3.5 w-3.5 text-emerald-700" />
                <span>Component 3 of 3</span>
              </span>
              <span className="text-[11px] font-mono text-slate-500">Synthesis Engine</span>
            </div>

            <div>
              <h4 className="font-sans text-base font-bold text-slate-900">Multimodal Fusion</h4>
              <p className="text-xs text-slate-500 font-sans mt-0.5">
                Formula: <span className="text-teal-800 font-semibold font-mono">0.55 Visual + 0.45 Systemic</span>
              </p>
            </div>

            {/* Final outputs card */}
            <div className="rounded-lg bg-white border border-slate-200 p-3 space-y-2 font-mono text-xs shadow-sm">
              <div className="flex justify-between items-center">
                <span className="text-slate-500 font-sans">Fused Final Risk:</span>
                <span className="text-rose-700 font-extrabold text-sm">{finalRisk}%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-500 font-sans">Skin Barrier Health:</span>
                <span className="text-teal-800 font-extrabold text-sm">{healthScore} / 100</span>
              </div>
              <div className="flex justify-between items-center text-[11px]">
                <span className="text-slate-500 font-sans">Assigned Weights:</span>
                <span className="text-slate-700 font-semibold">55% Visual / 45% Systemic</span>
              </div>
            </div>

            {/* Weight Rationale */}
            <div className="rounded-lg bg-white border border-slate-200 p-2.5 text-[11px] font-sans text-slate-600 leading-relaxed space-y-1 shadow-xs">
              <span className="text-[10px] text-teal-800 font-bold uppercase font-mono">Weight Rationale:</span>
              <p>
                Visual signal receives 55% weight reflecting direct cutaneous lesion morphology. Systemic risk receives 45% to capture underlying hormonal and lifestyle drivers.
              </p>
            </div>
          </div>

          <div className="pt-2 border-t border-slate-200 text-[11px] text-slate-500 font-sans">
            <span>Deterministic mathematical synthesis & 3-month trajectory projection.</span>
          </div>
        </div>
      </div>

      {/* Expanded Real Arithmetic Step-by-Step Breakdown */}
      {expandedDetails && (
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-5 space-y-4">
          <div className="flex items-center gap-2 text-xs font-sans font-bold text-slate-900 uppercase tracking-wider pb-2 border-b border-slate-200">
            <Binary className="h-4 w-4 text-teal-700" />
            <span>Exact Mathematical Execution & Arithmetic Ledger</span>
          </div>

          <div className="grid gap-4 md:grid-cols-2 text-xs">
            {/* Step 1: Final Risk Formula Arithmetic */}
            <div className="rounded-lg bg-white border border-slate-200 p-4 space-y-2.5 shadow-sm font-mono">
              <span className="text-teal-800 font-bold font-sans text-xs flex items-center gap-1.5">
                <span>1. Final Risk Percentage Formula</span>
              </span>
              <div className="p-2 rounded bg-slate-50 border border-slate-200 text-slate-800 text-[11px]">
                <code>FinalRisk = clamp(0.55 * ImageRisk + 0.45 * DataCombined, 0, 100)</code>
              </div>
              <div className="space-y-1 text-slate-600 text-[11px]">
                <div className="flex justify-between">
                  <span>Visual Component:</span>
                  <span className="text-slate-900 font-semibold">0.55 * {imageRisk}% = {visualContrib}%</span>
                </div>
                <div className="flex justify-between">
                  <span>Systemic Component:</span>
                  <span className="text-slate-900 font-semibold">0.45 * {dataCombined}% = {systemicContrib}%</span>
                </div>
                <div className="flex justify-between pt-1 border-t border-slate-200 font-semibold text-slate-800">
                  <span>Unclamped Weighted Sum:</span>
                  <span>{unclampedSum}%</span>
                </div>
                <div className="flex justify-between text-teal-800 font-bold">
                  <span>Clamped Final Risk:</span>
                  <span>{finalRisk}%</span>
                </div>
              </div>
            </div>

            {/* Step 2: Skin Health Score Arithmetic */}
            <div className="rounded-lg bg-white border border-slate-200 p-4 space-y-2.5 shadow-sm font-mono">
              <span className="text-teal-800 font-bold font-sans text-xs flex items-center gap-1.5">
                <span>2. Skin Barrier Health Score Formula</span>
              </span>
              <div className="p-2 rounded bg-slate-50 border border-slate-200 text-slate-800 text-[11px]">
                <code>SkinHealth = clamp(100.0 - FinalRisk + LifestyleBonus + EnvBonus, 0, 100)</code>
              </div>
              <div className="space-y-1 text-slate-600 text-[11px]">
                <div className="flex justify-between">
                  <span>Base Inverse Risk:</span>
                  <span>100.0 - {finalRisk} = {(100.0 - finalRisk).toFixed(1)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Lifestyle Bonus (if &lt; 40):</span>
                  <span>
                    {data.lifestyle_score < 40
                      ? `+${((40 - data.lifestyle_score) * 0.08).toFixed(2)}`
                      : '0.0 (Score \u2265 40)'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Environmental Bonus (if &lt; 40):</span>
                  <span>
                    {data.environmental_score < 40
                      ? `+${((40 - data.environmental_score) * 0.05).toFixed(2)}`
                      : '0.0 (Score \u2265 40)'}
                  </span>
                </div>
                <div className="flex justify-between pt-1 border-t border-slate-200 text-teal-800 font-bold">
                  <span>Final Skin Health Score:</span>
                  <span>{healthScore} / 100</span>
                </div>
              </div>
            </div>
          </div>

        </div>
      )}
    </div>
  )
}
