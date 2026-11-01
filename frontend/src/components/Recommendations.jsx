import { useState } from 'react'
import {
  AlertTriangle,
  BookOpen,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  FileCheck2,
  Heart,
  HelpCircle,
  Info,
  Pill,
  Scale,
  Shield,
  ShieldAlert,
  Sparkles,
  Stethoscope,
  Target,
  Trees,
} from 'lucide-react'

export default function Recommendations({ recommendations = {} }) {
  const entries = Object.entries(recommendations)
  const [expandedIndex, setExpandedIndex] = useState({})

  function toggleEvidence(key) {
    setExpandedIndex((prev) => ({
      ...prev,
      [key]: !prev[key],
    }))
  }

  const categoryIcons = {
    'Skin Care Routine': Pill,
    'Diet': Sparkles,
    'Lifestyle Changes': Heart,
    'Stress Management': Scale,
    'Environmental Protection': Trees,
    'When to See a Dermatologist': Stethoscope,
  }

  return (
    <div className="space-y-6">
      {/* Action Plan Grid */}
      <div className="grid gap-6 md:grid-cols-2">
        {entries.map(([title, items], i) => {
          const isDermCategory = title.toLowerCase().includes('dermatologist')
          const IconComp = categoryIcons[title] || Stethoscope

          return (
            <div
              key={title}
              className={`rounded-2xl p-6 transition-all duration-200 flex flex-col justify-between shadow-clinical ${
                isDermCategory
                  ? 'border-2 border-rose-200 bg-rose-50/40'
                  : 'bg-white border border-slate-200 hover:border-slate-300'
              }`}
            >
              <div>
                {/* Category Header */}
                <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-200">
                  <div className="flex items-center gap-3">
                    <span
                      className={`flex h-8 w-8 items-center justify-center rounded-lg border text-xs font-bold ${
                        isDermCategory
                          ? 'bg-rose-100 border-rose-200 text-rose-800'
                          : 'bg-teal-50 border border-teal-200 text-teal-800'
                      }`}
                    >
                      <IconComp className="h-4 w-4" />
                    </span>
                    <div>
                      <h4 className="font-sans text-base font-bold text-slate-900 capitalize">
                        {title.replace(/_/g, ' ')}
                      </h4>
                      <span className="text-xs text-slate-500 font-sans">
                        {isDermCategory ? 'Clinical Referral Guidelines' : 'Evidence-Linked Guidance'}
                      </span>
                    </div>
                  </div>

                  <span
                    className={`rounded-full px-2.5 py-0.5 text-[10px] font-sans font-bold uppercase tracking-wider border ${
                      isDermCategory
                        ? 'bg-rose-100 border-rose-300 text-rose-800'
                        : 'bg-slate-100 border-slate-200 text-slate-700'
                    }`}
                  >
                    {isDermCategory ? 'Clinical Referral' : 'Patient Self-Care'}
                  </span>
                </div>

                {/* Recommendations List */}
                <ul className="space-y-3">
                  {(items || []).map((item, idx) => {
                    const text = typeof item === 'string' ? item : item.text
                    const reason = typeof item === 'object' ? item.reason : null
                    const whyShown = typeof item === 'object' ? item.why_shown || item.reason : null
                    const triggerInput = typeof item === 'object' ? item.trigger_input : null
                    const evidenceSource = typeof item === 'object' ? item.evidence_source : null
                    const adviceType =
                      typeof item === 'object'
                        ? item.advice_type || (isDermCategory ? 'Clinical Escalation' : 'General Educational Guidance')
                        : 'General Educational Guidance'

                    const itemKey = `${title}_${idx}`
                    const isExpanded = !!expandedIndex[itemKey]
                    const isClinical = adviceType === 'Clinical Escalation'

                    return (
                      <li
                        key={idx}
                        className={`rounded-xl p-3.5 border transition ${
                          isClinical
                            ? 'bg-white border-rose-200 shadow-xs'
                            : 'bg-slate-50/60 border-slate-200 shadow-xs'
                        }`}
                      >
                        <div className="flex gap-2.5 items-start">
                          {isClinical ? (
                            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-rose-600" />
                          ) : (
                            <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-teal-700" />
                          )}

                          <div className="space-y-2 flex-1">
                            {/* Recommendation Text */}
                            <p className="font-semibold text-xs text-slate-900 leading-relaxed font-sans">
                              {text}
                            </p>

                            {/* Specific Summary Reason */}
                            {reason && reason !== text && (
                              <p className="text-[11px] text-teal-800 font-medium font-sans">
                                ↳ {reason}
                              </p>
                            )}

                            {/* Badges Row: Advice Type & Trigger Tag */}
                            <div className="flex flex-wrap items-center gap-1.5 pt-0.5">
                              <span
                                className={`rounded px-2 py-0.5 text-[10px] font-sans font-bold uppercase tracking-wider border ${
                                  isClinical
                                    ? 'bg-rose-50 border-rose-200 text-rose-800'
                                    : 'bg-emerald-50 border-emerald-200 text-emerald-800'
                                }`}
                              >
                                {adviceType}
                              </span>

                              {triggerInput && (
                                <span className="inline-flex items-center gap-1 rounded bg-white border border-slate-200 px-2 py-0.5 text-[11px] font-sans text-slate-600">
                                  <Target className="h-3 w-3 text-slate-400 shrink-0" />
                                  <span title={triggerInput}>
                                    {triggerInput}
                                  </span>
                                </span>
                              )}
                            </div>

                            {/* Why shown / clinical rationale */}
                            {whyShown && (
                              <div className="text-xs text-slate-600 leading-relaxed font-sans bg-white rounded-lg p-2.5 border border-slate-200">
                                <span className="font-bold text-slate-800 block text-[10px] uppercase tracking-wider mb-0.5">
                                  Clinical Rationale:
                                </span>
                                <span>{whyShown}</span>
                              </div>
                            )}


                            {/* Evidence Source Expandable Drawer */}
                            {evidenceSource && (
                              <div className="pt-0.5">
                                <button
                                  type="button"
                                  onClick={() => toggleEvidence(itemKey)}
                                  className="flex items-center gap-1.5 text-[11px] font-sans font-semibold text-teal-800 hover:text-teal-900 transition cursor-pointer"
                                >
                                  <BookOpen className="h-3.5 w-3.5 text-teal-700" />
                                  <span>View Clinical Literature Citation</span>
                                  {isExpanded ? (
                                    <ChevronUp className="h-3.5 w-3.5" />
                                  ) : (
                                    <ChevronDown className="h-3.5 w-3.5" />
                                  )}
                                </button>

                                {isExpanded && (
                                  <div className="mt-2 rounded-lg bg-teal-50/50 border border-teal-200 p-3 text-xs text-slate-700 font-sans space-y-1">
                                    <div className="flex items-center gap-1.5 font-bold text-teal-900">
                                      <FileCheck2 className="h-4 w-4 text-teal-700" />
                                      <span>Peer-Reviewed Evidence Citation</span>
                                    </div>
                                    <p className="text-xs text-slate-700 leading-relaxed italic">
                                      {evidenceSource}
                                    </p>
                                    <p className="text-[10px] text-slate-500 pt-1 border-t border-teal-200/60">
                                      Referenced guidelines: AAD Acne Guidelines 2024 / JAAD / Cochrane Reviews.
                                    </p>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      </li>
                    )
                  })}
                </ul>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
