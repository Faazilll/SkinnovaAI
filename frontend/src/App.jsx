import { useEffect, useRef, useState } from 'react'
import { gsap } from 'gsap'
import Lenis from 'lenis'
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Database,
  Layers,
  Microscope,
  RotateCcw,
  ShieldCheck,
  Sparkles,
  Zap,
} from 'lucide-react'

import {
  apiGetHistory,
  apiGetMe,
  apiLogout,
  apiSaveScan,
  healthCheck,
  predictFusionRecalculate,
  predictFusionUpload,
  predictValidate,
} from './api'

import AnalyticsView from './components/AnalyticsView'
import AuthModal from './components/AuthModal'
import Dashboard from './components/Dashboard'
import HistoryView from './components/HistoryView'
import ImageUpload from './components/ImageUpload'
import Navbar from './components/Navbar'
import ProfileView from './components/ProfileView'
import QuestionnaireForm from './components/QuestionnaireForm'

export const EMPTY_FORM = {
  age: '',
  gender: '',
  menstrual_cycle: '',
  pcos: false,
  thyroid_status: '',
  pregnancy: false,
  medications: '',
  sleep_hours: '',
  diet_quality: '',
  water_intake_liters: '',
  exercise_frequency: '',
  stress_level: '',
  smoking: false,
  alcohol: '',
  skincare_consistency: '',
  location_type: '',
  pollution_level: '',
  sun_exposure: '',
  humidity: '',
  climate: '',
  outdoor_ratio: '',
  ac_heating_exposure: '',
  profile_confirmed: false,
}

export function sanitizeQuestionnaire(f) {
  return {
    age: Number(f.age) || 24,
    gender: f.gender || 'female',
    menstrual_cycle: f.menstrual_cycle || 'regular',
    pcos: Boolean(f.pcos),
    thyroid_status: f.thyroid_status || 'normal',
    pregnancy: Boolean(f.pregnancy),
    medications: f.medications || 'none',
    sleep_hours: f.sleep_hours !== '' && f.sleep_hours !== undefined ? Number(f.sleep_hours) : 7.0,
    diet_quality: f.diet_quality || 'average',
    water_intake_liters: f.water_intake_liters !== '' && f.water_intake_liters !== undefined ? Number(f.water_intake_liters) : 2.0,
    exercise_frequency: f.exercise_frequency || '1-2_week',
    stress_level: f.stress_level !== '' && f.stress_level !== undefined ? Number(f.stress_level) : 5,
    smoking: Boolean(f.smoking),
    alcohol: f.alcohol || 'none',
    skincare_consistency: f.skincare_consistency || 'inconsistent',
    location_type: f.location_type || 'suburban',
    pollution_level: f.pollution_level || 'moderate',
    sun_exposure: f.sun_exposure || 'moderate',
    humidity: f.humidity || 'moderate',
    climate: f.climate || 'temperate',
    outdoor_ratio: f.outdoor_ratio !== '' && f.outdoor_ratio !== undefined ? Number(f.outdoor_ratio) : 0.3,
    ac_heating_exposure: f.ac_heating_exposure || 'moderate',
    profile_confirmed: Boolean(f.profile_confirmed),
  }
}

export default function App() {
  const [activeTab, setActiveTab] = useState('analyze')
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [allowCloseUp, setAllowCloseUp] = useState(true)
  const [form, setForm] = useState(EMPTY_FORM)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [recalculating, setRecalculating] = useState(false)
  const [error, setError] = useState('')
  const [health, setHealth] = useState(null)
  const [user, setUser] = useState(null)
  const [history, setHistory] = useState([])
  const [authModalOpen, setAuthModalOpen] = useState(false)
  const [toast, setToast] = useState('')
  const [consistencyWarning, setConsistencyWarning] = useState(null)
  const [consistencyConfirmed, setConsistencyConfirmed] = useState(false)

  const lenisRef = useRef(null)
  const heroRef = useRef(null)
  const resultsRef = useRef(null)
  const statsCountersRef = useRef([])
  const isInitialMount = useRef(true)


  // Initialize Lenis Smooth Scrolling and GSAP Ticker Integration
  useEffect(() => {
    const lenis = new Lenis({
      duration: 1.2,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      smoothWheel: true,
      wheelMultiplier: 1.0,
      touchMultiplier: 1.5,
    })
    lenisRef.current = lenis

    function raf(time) {
      lenis.raf(time * 1000)
    }

    gsap.ticker.add(raf)
    gsap.ticker.lagSmoothing(0)

    return () => {
      gsap.ticker.remove(raf)
      lenis.destroy()
    }
  }, [])

  // Initial Data & Health Load
  useEffect(() => {
    healthCheck()
      .then(setHealth)
      .catch(() => setHealth({ status: 'unreachable' }))

    apiGetMe()
      .then((u) => {
        setUser(u)
        refreshHistory()
      })
      .catch(() => {
        refreshHistory()
      })
  }, [])

  // Staggered Hero Animation on Mount
  useEffect(() => {
    if (heroRef.current) {
      gsap.fromTo(
        heroRef.current.children,
        { opacity: 0, y: 30 },
        { opacity: 1, y: 0, duration: 0.9, stagger: 0.12, ease: 'power3.out' }
      )
    }
  }, [])

  function showToast(msg) {
    setToast(msg)
    setTimeout(() => setToast(''), 4500)
  }

  function refreshHistory() {
    apiGetHistory()
      .then(setHistory)
      .catch((e) => console.error('Failed to load history', e))
  }

  function onFile(f) {
    setFile(f)
    setResult(null)
    setConsistencyConfirmed(false)
    setConsistencyWarning(null)
    if (preview) URL.revokeObjectURL(preview)
    setPreview(f ? URL.createObjectURL(f) : null)
  }

  function handleFormChange(newForm) {
    if (newForm.gender !== form.gender) {
      setConsistencyConfirmed(false)
      setConsistencyWarning(null)
    }
    setForm(newForm)
  }

  async function executeAnalysis(sanitizedQuestionnaire) {
    setLoading(true)
    setResult(null)

    try {
      const data = await predictFusionUpload(file, sanitizedQuestionnaire, true)
      setResult(data)

      // Auto-save scan
      await apiSaveScan(data, 'Auto-saved multimodal scan')
      refreshHistory()
      showToast('Multimodal scan evaluated and logged in clinical registry!')

      // Smooth scroll down to results with Lenis
      setTimeout(() => {
        if (resultsRef.current && lenisRef.current) {
          lenisRef.current.scrollTo(resultsRef.current, { offset: -90, duration: 1.4 })
        }
      }, 150)
    } catch (err) {
      setError(err.message || 'Diagnostic fusion evaluation failed')
    } finally {
      setLoading(false)
    }
  }

  async function onAnalyze(e, bypassValidation = false) {
    if (e && e.preventDefault) e.preventDefault()
    setError('')
    if (!file) {
      setError('Please upload or select a clinical facial or skin photograph first.')
      return
    }
    if (file.size > 15 * 1024 * 1024) {
      setError('The selected photo exceeds the 15 MB size limit. Please choose a smaller image.')
      return
    }
    if (!form.age) {
      setError('Please enter your age in the clinical intake form.')
      return
    }
    if (!form.gender) {
      setError('Please select your biological sex in the clinical intake form.')
      return
    }
    if (form.profile_confirmed === false) {
      setError('Please check the confirmation box at the bottom of the questionnaire before proceeding.')
      return
    }

    const sanitizedQuestionnaire = sanitizeQuestionnaire(form)

    // Pre-validation Layer: checks image quality and questionnaire consistency
    if (!bypassValidation && !consistencyConfirmed) {
      setLoading(true)
      try {
        const valRes = await predictValidate(file, sanitizedQuestionnaire, true)
        if (!valRes.valid) {
          setError(valRes.errors?.[0] || 'Image validation failed. Please provide a clear, usable facial photo.')
          setLoading(false)
          return
        }

        if (valRes.consistency_warning && valRes.consistency_warning.has_warning) {
          setConsistencyWarning(valRes.consistency_warning)
          setLoading(false)
          return
        }
      } catch (err) {
        console.warn('Pre-validation check note:', err)
      }
    }

    await executeAnalysis(sanitizedQuestionnaire)
  }

  // Dynamic Live Update: Recalculate fusion & recommendations when questionnaire changes if analysis is already active
  useEffect(() => {
    if (isInitialMount.current) {
      isInitialMount.current = false
      return
    }
    if (!result?.image) return

    // Debounce to allow smooth typing and selection changes
    const timer = setTimeout(async () => {
      try {
        setRecalculating(true)
        const sanitized = sanitizeQuestionnaire(form)
        const updated = await predictFusionRecalculate(result.image, sanitized)
        setResult((prev) => ({
          ...updated,
          image: { ...prev.image, ...updated.image },
        }))
        showToast('Personalized recommendations dynamically updated to match questionnaire!')
      } catch (err) {
        console.error('Failed to dynamic-update recommendations:', err)
      } finally {
        setRecalculating(false)
      }
    }, 350)

    return () => clearTimeout(timer)
  }, [form])

  async function handleRecalculate() {
    if (!result?.image) return
    try {
      setRecalculating(true)
      const sanitized = sanitizeQuestionnaire(form)
      const updated = await predictFusionRecalculate(result.image, sanitized)
      setResult((prev) => ({
        ...updated,
        image: { ...prev.image, ...updated.image },
      }))
      showToast('Personalized recommendations refreshed from questionnaire!')
    } catch (err) {
      showToast('Recalculation error: ' + err.message)
    } finally {
      setRecalculating(false)
    }
  }


  async function handleSaveManual(scanData, notes) {
    try {
      await apiSaveScan(scanData, notes)
      refreshHistory()
      showToast('Evaluation record saved to patient timeline!')
    } catch (err) {
      showToast('Could not save record: ' + err.message)
    }
  }

  function handleReloadScan(scan) {
    const dashboardResult = {
      skin_health_score: scan.skin_health_score,
      final_risk_percent: scan.risk_percent,
      gauges: {
        skin_health: scan.skin_health_score,
        image_risk: scan.risk_percent,
        hormonal: scan.data_scores?.hormonal ?? 0,
        lifestyle: scan.data_scores?.lifestyle ?? 0,
        environmental: scan.data_scores?.environmental ?? 0,
      },
      image: {
        severity: scan.severity,
        severity_label: scan.severity_label,
        current_skin_condition: scan.image_attributes?.current_skin_condition || scan.severity_label,
        problem_areas: scan.image_attributes?.problem_areas || [],
        oiliness: scan.image_attributes?.oiliness ?? 0,
        pores: scan.image_attributes?.pores ?? 0,
        redness: scan.image_attributes?.redness ?? 0,
        dark_spots: scan.image_attributes?.dark_spots ?? 0,
        method: scan.image_attributes?.method || 'mobilenetv2_acne04_improved',
      },
      data: {
        hormonal_score: scan.data_scores?.hormonal ?? 0,
        lifestyle_score: scan.data_scores?.lifestyle ?? 0,
        environmental_score: scan.data_scores?.environmental ?? 0,
        combined_score: scan.data_scores?.combined ?? 0,
        drivers: scan.drivers || [],
        method: scan.data_scores?.method || 'random_forest_regressor',
      },
      trend: scan.trend || [],
      recommendations: scan.recommendations || {},
      disclaimer:
        'Skinova is an educational clinical decision-support prototype, not a certified medical device.',
    }
    setResult(dashboardResult)
    setActiveTab('analyze')

    setTimeout(() => {
      if (resultsRef.current && lenisRef.current) {
        lenisRef.current.scrollTo(resultsRef.current, { offset: -90, duration: 1.2 })
      }
    }, 100)

    showToast(`Loaded Evaluation #${scan.id} into Live Studio`)
  }

  function handleAuthSuccess(authenticatedUser) {
    setUser(authenticatedUser)
    refreshHistory()
    showToast(`Clinician authenticated: ${authenticatedUser.name || authenticatedUser.email}`)
  }

  function handleLogout() {
    apiLogout()
    setUser(null)
    refreshHistory()
    showToast('Signed out of clinical workstation')
  }

  return (
    <div className="min-h-screen text-slate-900 font-sans pb-24 selection:bg-medic-600 selection:text-white medical-grid">
      {/* Toast Notification */}
      {toast && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-3 rounded-xl bg-white border border-slate-200 px-4 py-3 text-xs font-sans font-medium text-slate-800 shadow-elevated">
          <ShieldCheck className="h-4 w-4 text-medic-600 shrink-0" />
          <span>{toast}</span>
        </div>
      )}

      {/* Navigation Bar */}
      <Navbar
        activeTab={activeTab}
        onSelectTab={(tab) => {
          setActiveTab(tab)
          if (lenisRef.current) lenisRef.current.scrollTo(0, { duration: 0.8 })
        }}
        user={user}
        onOpenAuth={() => setAuthModalOpen(true)}
        onLogout={handleLogout}
        health={health}
        historyCount={history.length}
      />

      {/* Main Content Stage */}
      <main className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Tab 1: Scanner & Fusion */}
        {activeTab === 'analyze' && (
          <div className="space-y-8">
            {/* Clinical Workstation Banner */}
            <div
              ref={heroRef}
              className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-clinical transition-all"
            >
              <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
                <div className="max-w-3xl space-y-2.5">
                  <div className="inline-flex items-center gap-2 rounded-full bg-teal-50 border border-teal-200 px-3 py-1 text-[11px] font-sans font-semibold uppercase tracking-wider text-teal-800">
                    <Activity className="h-3.5 w-3.5 text-teal-700" />
                    <span>Clinical Decision Support System</span>
                  </div>

                  <h1 className="font-sans text-2xl sm:text-4xl font-bold text-slate-900 tracking-tight leading-snug">
                    Dual-Model Cutaneous & Systemic Acne Risk Prognosis
                  </h1>

                  <p className="text-xs sm:text-sm text-slate-600 leading-relaxed max-w-2xl font-normal">
                    Fusing validated deep learning visual feature extraction (<span className="text-slate-900 font-semibold font-mono">MobileNetV2 on ACNE04</span>) with systemic endocrine, lifestyle, and exposome risk models (<span className="text-slate-900 font-semibold font-mono">Multi-Output Random Forest</span>) for Hayashi-standardized acne decision support.
                  </p>

                  {/* Clinical Specs Row */}
                  <div className="pt-2 flex flex-wrap gap-4 text-xs text-slate-600">
                    <div className="flex items-center gap-1.5">
                      <span className="h-2 w-2 rounded-full bg-teal-600" />
                      <span className="font-medium">Hayashi Grade 0–3 Scale</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="h-2 w-2 rounded-full bg-sky-600" />
                      <span className="font-medium">21-Biomarker Endocrine Profile</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="h-2 w-2 rounded-full bg-emerald-600" />
                      <span className="font-medium">55% Visual / 45% Systemic Weighting</span>
                    </div>
                  </div>
                </div>


              </div>
            </div>

            {/* Diagnostic Input Stage: Form */}
            <form onSubmit={onAnalyze} className="grid gap-6 lg:grid-cols-2">
              {/* Stage 1: Cutaneous Image Input */}
              <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-7 shadow-clinical flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-4 border-b border-slate-200 pb-3">
                    <div className="flex items-center gap-2.5">
                      <span className="flex h-6 w-6 items-center justify-center rounded-lg bg-teal-100 text-teal-800 font-mono text-xs font-bold">
                        1
                      </span>
                      <h2 className="font-sans text-lg font-bold text-slate-900">
                        Cutaneous Photography
                      </h2>
                    </div>
                    <span className="text-xs font-medium text-slate-500">Module 1 of 2</span>
                  </div>

                  <ImageUpload
                    file={file}
                    preview={preview}
                    onChange={onFile}
                    allowCloseUp={allowCloseUp}
                    onToggleAllowCloseUp={setAllowCloseUp}
                    isScanning={loading}
                  />
                </div>
              </div>

              {/* Stage 2: 21 Systemic Biomarkers Questionnaire */}
              <div id="questionnaire-container" className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-7 shadow-clinical flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-4 border-b border-slate-200 pb-3">
                    <div className="flex items-center gap-2.5">
                      <span className="flex h-6 w-6 items-center justify-center rounded-lg bg-sky-100 text-sky-800 font-mono text-xs font-bold">
                        2
                      </span>
                      <h2 className="font-sans text-lg font-bold text-slate-900">
                        Systemic Biomarkers
                      </h2>
                    </div>
                    <span className="text-xs font-medium text-slate-500">21 Clinical Fields</span>
                  </div>

                  <div className="clinical-scrollbar max-h-[580px] overflow-y-auto pr-3">
                    <QuestionnaireForm values={form} onChange={handleFormChange} />
                  </div>
                </div>
              </div>

              {/* Trigger Button Row */}
              <div className="lg:col-span-2 bg-white border border-slate-200 rounded-2xl p-5 sm:p-6 shadow-clinical flex flex-col sm:flex-row items-center justify-between gap-4">
                <div className="space-y-1">
                  <h3 className="font-sans text-base font-bold text-slate-900 flex items-center gap-2">
                    <Microscope className="h-5 w-5 text-teal-700" />
                    <span>Execute Multimodal Decision Support Computation</span>
                  </h3>
                  <p className="text-xs text-slate-500">
                    Calculates dual-weighted multimodal prognosis combining MobileNetV2 cutaneous grade with systemic endocrine regression.
                  </p>
                </div>

                <div className="w-full sm:w-auto">
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full sm:w-auto flex items-center justify-center gap-2.5 rounded-xl bg-teal-700 hover:bg-teal-800 active:bg-teal-900 px-6 py-3.5 text-xs font-bold text-white shadow-sm transition disabled:opacity-50 tracking-wide font-sans cursor-pointer"
                  >
                    {loading ? (
                      <>
                        <span className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        <span>Fusing Visual & Biomarker Models…</span>
                      </>
                    ) : (
                      <>
                        <Activity className="h-4 w-4" />
                        <span>Compute Clinical Prognosis</span>
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Error Message */}
              {error && (
                <div className="lg:col-span-2 rounded-xl border border-rose-200 bg-rose-50 p-4 text-xs text-rose-800 flex items-center gap-3">
                  <AlertTriangle className="h-4 w-4 shrink-0 text-rose-600" />
                  <span className="font-medium">{error}</span>
                </div>
              )}
            </form>

            {/* Diagnostic Results Section (Ref target for smooth scroll) */}
            <div ref={resultsRef}>
              <Dashboard
                result={result}
                onSaveHistory={handleSaveManual}
                isSaved={Boolean(result)}
                user={user}
                form={form}
                imagePreview={preview}
                recalculating={recalculating}
                onRecalculate={handleRecalculate}
              />

            </div>
          </div>
        )}

        {/* Tab 2: History Timeline */}
        {activeTab === 'history' && (
          <HistoryView
            history={history}
            onReloadScan={handleReloadScan}
            onRefreshHistory={refreshHistory}
            user={user}
            onOpenAuth={() => setAuthModalOpen(true)}
          />
        )}

        {/* Tab 3: Longitudinal Trends */}
        {activeTab === 'analytics' && (
          <AnalyticsView history={history} onSelectTab={setActiveTab} />
        )}

        {/* Tab 4: Clinician Profile */}
        {activeTab === 'profile' && (
          <ProfileView
            user={user}
            onOpenAuth={() => setAuthModalOpen(true)}
            onLogout={handleLogout}
            history={history}
            onSelectTab={setActiveTab}
          />
        )}
      </main>

      {/* Clinician Authentication Modal */}
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        onAuthSuccess={handleAuthSuccess}
      />

      {/* Biological Sex Selection Confirmation Modal */}
      {consistencyWarning && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 animate-fade-in">
          <div className="w-full max-w-md rounded-2xl bg-white border border-slate-200 p-6 shadow-2xl space-y-4">
            <div className="flex items-start gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-amber-100 text-amber-800">
                <AlertTriangle className="h-5 w-5" />
              </div>
              <div className="space-y-1">
                <h3 className="text-base font-bold text-slate-900">
                  {consistencyWarning.title || 'Biological Sex Selection Confirmation'}
                </h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  {consistencyWarning.message}
                </p>
              </div>
            </div>

            {consistencyWarning.detected_feature && (
              <div className="rounded-xl bg-amber-50/80 border border-amber-200 p-3 text-xs text-amber-900 flex items-center justify-between">
                <span className="font-medium text-amber-800">Observation:</span>
                <span className="font-semibold">{consistencyWarning.detected_feature}</span>
              </div>
            )}

            <p className="text-[11px] text-slate-500 leading-relaxed">
              Biological sex is used exclusively to calibrate systemic endocrine pathways (androgen/estrogen dynamics and PCOS risk modeling).
            </p>

            <div className="pt-2 flex flex-col sm:flex-row gap-2.5">
              <button
                type="button"
                onClick={() => {
                  setConsistencyWarning(null)
                  const qEl = document.getElementById('questionnaire-container')
                  if (qEl && lenisRef.current) {
                    lenisRef.current.scrollTo(qEl, { offset: -80, duration: 1.0 })
                  }
                }}
                className="flex-1 rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition shadow-sm cursor-pointer"
              >
                Review Questionnaire
              </button>
              <button
                type="button"
                onClick={() => {
                  setConsistencyConfirmed(true)
                  setConsistencyWarning(null)
                  onAnalyze(null, true)
                }}
                className="flex-1 rounded-xl bg-teal-700 px-4 py-2.5 text-xs font-semibold text-white hover:bg-teal-800 transition shadow-clinical cursor-pointer"
              >
                Confirm & Continue
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
