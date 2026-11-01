import { useState } from 'react'
import {
  Activity,
  CheckCircle2,
  Droplets,
  HeartPulse,
  Info,
  Moon,
  ShieldAlert,
  Sun,
  Wind,
  Zap,
} from 'lucide-react'

const inputCls =
  'clinical-input w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-xs font-semibold text-slate-900 outline-none focus:border-teal-700 focus:ring-2 focus:ring-teal-700/15 transition shadow-sm cursor-pointer'
const labelCls =
  'block text-[11px] font-sans font-bold uppercase tracking-wider text-slate-700 mb-1'

function Field({ label, icon: Icon, children }) {
  return (
    <label className="block">
      <div className="flex items-center gap-1.5 mb-1.5">
        {Icon && <Icon className="h-3.5 w-3.5 text-teal-700" />}
        <span className={labelCls}>{label}</span>
      </div>
      {children}
    </label>
  )
}

export default function QuestionnaireForm({ values, onChange }) {
  const [activeSection, setActiveSection] = useState('endocrine')
  const set = (key, val) => onChange({ ...values, [key]: val })

  // Quick Archetype Presets
  function applyPreset(presetType) {
    if (presetType === 'balanced') {
      onChange({
        ...values,
        age: 25,
        gender: 'female',
        menstrual_cycle: 'regular',
        pcos: false,
        thyroid_status: 'normal',
        pregnancy: false,
        medications: 'none',
        sleep_hours: 8,
        diet_quality: 'good',
        water_intake_liters: 2.5,
        exercise_frequency: '3-4_week',
        stress_level: 3,
        smoking: false,
        alcohol: 'rare',
        skincare_consistency: 'consistent',
        location_type: 'suburban',
        pollution_level: 'low',
        sun_exposure: 'low',
        humidity: 'moderate',
        climate: 'temperate',
        outdoor_ratio: 0.2,
        ac_heating_exposure: 'moderate',
        profile_confirmed: true,
      })
    } else if (presetType === 'urban_stress') {
      onChange({
        ...values,
        age: 26,
        gender: 'female',
        menstrual_cycle: 'somewhat_irregular',
        pcos: false,
        thyroid_status: 'normal',
        pregnancy: false,
        medications: 'none',
        sleep_hours: 5.5,
        diet_quality: 'poor',
        water_intake_liters: 1.2,
        exercise_frequency: 'none',
        stress_level: 8,
        smoking: false,
        alcohol: 'moderate',
        skincare_consistency: 'inconsistent',
        location_type: 'urban',
        pollution_level: 'high',
        sun_exposure: 'moderate',
        humidity: 'high',
        climate: 'humid_subtropical',
        outdoor_ratio: 0.45,
        ac_heating_exposure: 'high',
        profile_confirmed: true,
      })
    } else if (presetType === 'pcos_flare') {
      onChange({
        ...values,
        age: 24,
        gender: 'female',
        menstrual_cycle: 'irregular',
        pcos: true,
        thyroid_status: 'hypo',
        pregnancy: false,
        medications: 'spironolactone',
        sleep_hours: 6,
        diet_quality: 'average',
        water_intake_liters: 1.8,
        exercise_frequency: '1-2_week',
        stress_level: 7,
        smoking: false,
        alcohol: 'occasional',
        skincare_consistency: 'inconsistent',
        location_type: 'urban',
        pollution_level: 'moderate',
        sun_exposure: 'moderate',
        humidity: 'moderate',
        climate: 'temperate',
        outdoor_ratio: 0.3,
        ac_heating_exposure: 'moderate',
        profile_confirmed: true,
      })
    }
  }

  const sections = [
    { id: 'endocrine', label: '1. Endocrine & Hormonal', icon: HeartPulse, count: '6 fields' },
    { id: 'lifestyle', label: '2. Lifestyle & Stress', icon: Moon, count: '8 fields' },
    { id: 'exposome', label: '3. Exposome & Climate', icon: Wind, count: '7 fields' },
  ]

  return (
    <div className="space-y-4">
      {/* Clinical Independence Notice */}
      <div className="rounded-xl border border-teal-200 bg-teal-50/70 p-3 text-xs text-slate-700">
        <div className="flex items-center gap-2 font-semibold text-teal-900 mb-0.5">
          <Info className="h-4 w-4 shrink-0 text-teal-700" />
        </div>
        <p className="text-[11px] leading-relaxed text-slate-600">
          Your questionnaire responses help Skinova estimate hormonal, lifestyle, and environmental risk factors associated with skin health.
        </p>
      </div>

      {/* Quick Archetype Preset Buttons */}
      <div className="flex flex-wrap items-center gap-1.5 p-2 rounded-xl bg-slate-50 border border-slate-200">
        <span className="text-[11px] font-sans font-medium text-slate-500 px-1 flex items-center gap-1">
          <Zap className="h-3.5 w-3.5 text-teal-700" /> Preset Scenarios:
        </span>
        <button
          type="button"
          onClick={() => applyPreset('balanced')}
          className="rounded-lg border border-emerald-300 bg-emerald-50 hover:bg-emerald-100 px-2.5 py-1 text-[11px] font-sans font-semibold text-emerald-800 transition cursor-pointer"
        >
          Baseline Optimal
        </button>
        <button
          type="button"
          onClick={() => applyPreset('urban_stress')}
          className="rounded-lg border border-amber-300 bg-amber-50 hover:bg-amber-100 px-2.5 py-1 text-[11px] font-sans font-semibold text-amber-800 transition cursor-pointer"
        >
          High-Stress Urban
        </button>
        <button
          type="button"
          onClick={() => applyPreset('pcos_flare')}
          className="rounded-lg border border-rose-300 bg-rose-50 hover:bg-rose-100 px-2.5 py-1 text-[11px] font-sans font-semibold text-rose-800 transition cursor-pointer"
        >
          PCOS / Endocrine Flare
        </button>
        <button
          type="button"
          onClick={() => onChange({
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
          })}
          className="rounded-lg border border-slate-300 bg-white hover:bg-slate-100 px-2.5 py-1 text-[11px] font-sans text-slate-600 transition ml-auto cursor-pointer"
        >
          Reset
        </button>
      </div>

      {/* Section Switcher Tabs */}
      <div className="grid grid-cols-3 gap-1 p-1 rounded-xl bg-slate-100 border border-slate-200">
        {sections.map((sec) => {
          const Icon = sec.icon
          const isActive = activeSection === sec.id
          return (
            <button
              key={sec.id}
              type="button"
              onClick={() => setActiveSection(sec.id)}
              className={`flex flex-col sm:flex-row items-center justify-center gap-1.5 py-2 px-2 rounded-lg text-xs font-semibold transition cursor-pointer ${isActive
                ? 'bg-white text-teal-800 shadow-sm border border-slate-200/80 font-bold'
                : 'text-slate-600 hover:text-slate-900'
                }`}
            >
              <Icon className={`h-3.5 w-3.5 ${isActive ? 'text-teal-700' : 'text-slate-500'}`} />
              <span className="truncate">{sec.label.split('. ')[1]}</span>
            </button>
          )
        })}
      </div>

      {/* Section 1: Endocrine & Hormonal */}
      {activeSection === 'endocrine' && (
        <div className="grid gap-4 sm:grid-cols-2 animate-rise">
          <Field label="Age" icon={Activity}>
            <input
              type="number"
              min="10"
              max="95"
              placeholder="Enter age (e.g. 24)"
              style={{ color: '#000000', backgroundColor: '#ffffff' }}
              className={inputCls}
              value={values.age ?? ''}
              onChange={(e) => {
                const raw = e.target.value
                if (raw === '') {
                  set('age', '')
                } else {
                  const num = parseInt(raw, 10)
                  set('age', isNaN(num) ? '' : num)
                }
              }}
            />
          </Field>

          <Field label="Biological Sex">
            <select
              style={{ color: '#000000', backgroundColor: '#ffffff' }}
              className={inputCls}
              value={values.gender || ''}
              onChange={(e) => set('gender', e.target.value)}
            >
              <option value="" disabled className="text-slate-400 font-normal">-- Select Biological Sex --</option>
              <option value="female" className="text-black bg-white font-bold">Female</option>
              <option value="male" className="text-black bg-white font-bold">Male</option>
              <option value="other" className="text-black bg-white font-bold">Other / Non-Binary</option>
            </select>
          </Field>

          <Field label="Menstrual Cycle">
            <select
              style={{ color: '#000000', backgroundColor: '#ffffff' }}
              className={inputCls}
              value={values.menstrual_cycle || ''}
              onChange={(e) => set('menstrual_cycle', e.target.value)}
            >
              <option value="" disabled className="text-slate-400 font-normal">-- Select Menstrual Cycle --</option>
              <option value="regular" className="text-black bg-white font-bold">Regular (28±4 days)</option>
              <option value="somewhat_irregular" className="text-black bg-white font-bold">Somewhat Irregular</option>
              <option value="irregular" className="text-black bg-white font-bold">Noticeably Irregular</option>
              <option value="absent" className="text-black bg-white font-bold">Absent / Amenorrhea</option>
              <option value="na" className="text-black bg-white font-bold">N/A (Male / Post-menopausal)</option>
            </select>
          </Field>

          <Field label="Thyroid Status">
            <select
              style={{ color: '#000000', backgroundColor: '#ffffff' }}
              className={inputCls}
              value={values.thyroid_status || ''}
              onChange={(e) => set('thyroid_status', e.target.value)}
            >
              <option value="" disabled className="text-slate-400 font-normal">-- Select Thyroid Status --</option>
              <option value="normal" className="text-black bg-white font-bold">Euthyroid (Normal)</option>
              <option value="hypo" className="text-black bg-white font-bold">Hypothyroidism</option>
              <option value="hyper" className="text-black bg-white font-bold">Hyperthyroidism</option>
            </select>
          </Field>

          <Field label="Prescription Medications">
            <select
              style={{ color: '#000000', backgroundColor: '#ffffff' }}
              className={inputCls}
              value={values.medications || ''}
              onChange={(e) => set('medications', e.target.value)}
            >
              <option value="" disabled className="text-slate-400 font-normal">-- Select Prescription Medications --</option>
              <option value="none" className="text-black bg-white font-bold">None</option>
              <option value="steroids" className="text-black bg-white font-bold">Systemic Steroids</option>
              <option value="isotretinoin" className="text-black bg-white font-bold">Oral Isotretinoin</option>
              <option value="spironolactone" className="text-black bg-white font-bold">Spironolactone</option>
              <option value="birth_control" className="text-black bg-white font-bold">Oral Contraceptives</option>
              <option value="antibiotics" className="text-black bg-white font-bold">Oral Antibiotics</option>
              <option value="other" className="text-black bg-white font-bold">Other</option>
            </select>
          </Field>

          <div className="space-y-3 pt-2">
            <label className="flex items-center gap-2.5 cursor-pointer text-xs text-slate-200 font-medium">
              <input
                type="checkbox"
                checked={Boolean(values.pcos)}
                onChange={(e) => set('pcos', e.target.checked)}
                className="rounded border-slate-400 bg-white text-medic-600 focus:ring-medic-500 h-4 w-4"
              />
              <span>Diagnosed PCOS (Polycystic Ovary)</span>
            </label>

            <label className="flex items-center gap-2.5 cursor-pointer text-xs text-slate-200 font-medium">
              <input
                type="checkbox"
                checked={Boolean(values.pregnancy)}
                onChange={(e) => set('pregnancy', e.target.checked)}
                className="rounded border-slate-400 bg-white text-medic-600 focus:ring-medic-500 h-4 w-4"
              />
              <span>Currently Pregnant / Postpartum</span>
            </label>
          </div>
        </div>
      )}

      {/* Section 2: Lifestyle & Stress */}
      {activeSection === 'lifestyle' && (
        <div className="space-y-4 animate-rise">
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <div className="flex justify-between items-center mb-1">
                <span className={labelCls}>Nightly Sleep Duration</span>
                <span className="font-mono text-xs text-medic-300 font-bold">
                  {values.sleep_hours !== '' && values.sleep_hours !== undefined ? `${values.sleep_hours} hrs` : '-- Slide to set --'}
                </span>
              </div>
              <input
                type="range"
                min="4"
                max="11"
                step="0.5"
                value={values.sleep_hours || 7}
                onChange={(e) => set('sleep_hours', Number(e.target.value))}
                className="w-full accent-medic-500 h-2 bg-slate-700 rounded-lg cursor-pointer"
              />
            </div>

            <div>
              <div className="flex justify-between items-center mb-1">
                <span className={labelCls}>Daily Water Hydration</span>
                <span className="font-mono text-xs text-cyanic-300 font-bold">
                  {values.water_intake_liters !== '' && values.water_intake_liters !== undefined ? `${values.water_intake_liters} L` : '-- Slide to set --'}
                </span>
              </div>
              <input
                type="range"
                min="0.5"
                max="4.5"
                step="0.1"
                value={values.water_intake_liters || 2.0}
                onChange={(e) => set('water_intake_liters', Number(e.target.value))}
                className="w-full accent-cyanic-400 h-2 bg-slate-700 rounded-lg cursor-pointer"
              />
            </div>

            <div>
              <div className="flex justify-between items-center mb-1">
                <span className={labelCls}>Perceived Stress (1-10)</span>
                <span className="font-mono text-xs text-amber-300 font-bold">
                  {values.stress_level !== '' && values.stress_level !== undefined ? `${values.stress_level} / 10` : '-- Slide to set --'}
                </span>
              </div>
              <input
                type="range"
                min="1"
                max="10"
                value={values.stress_level || 5}
                onChange={(e) => set('stress_level', Number(e.target.value))}
                className="w-full accent-amber-400 h-2 bg-slate-700 rounded-lg cursor-pointer"
              />
            </div>

            <Field label="Dietary Quality">
              <select
                style={{ color: '#000000', backgroundColor: '#ffffff' }}
                className={inputCls}
                value={values.diet_quality || ''}
                onChange={(e) => set('diet_quality', e.target.value)}
              >
                <option value="" disabled className="text-slate-400 font-normal">-- Select Dietary Quality --</option>
                <option value="good" className="text-black bg-white font-bold">Whole Foods / High Antioxidant</option>
                <option value="average" className="text-black bg-white font-bold">Balanced / Mixed Average</option>
                <option value="poor" className="text-black bg-white font-bold">High Glycemic / Dairy Heavy</option>
              </select>
            </Field>

            <Field label="Physical Exercise">
              <select
                style={{ color: '#000000', backgroundColor: '#ffffff' }}
                className={inputCls}
                value={values.exercise_frequency || ''}
                onChange={(e) => set('exercise_frequency', e.target.value)}
              >
                <option value="" disabled className="text-slate-400 font-normal">-- Select Exercise Frequency --</option>
                <option value="none" className="text-black bg-white font-bold">Sedentary (Rarely)</option>
                <option value="1-2_week" className="text-black bg-white font-bold">1-2 Days / Week</option>
                <option value="3-4_week" className="text-black bg-white font-bold">3-4 Days / Week</option>
                <option value="daily" className="text-black bg-white font-bold">Daily Moderate / Intense</option>
              </select>
            </Field>

            <Field label="Skincare Routine Adherence">
              <select
                style={{ color: '#000000', backgroundColor: '#ffffff' }}
                className={inputCls}
                value={values.skincare_consistency || ''}
                onChange={(e) => set('skincare_consistency', e.target.value)}
              >
                <option value="" disabled className="text-slate-400 font-normal">-- Select Skincare Adherence --</option>
                <option value="consistent" className="text-black bg-white font-bold">Strictly Consistent AM/PM</option>
                <option value="inconsistent" className="text-black bg-white font-bold">Intermittent / Inconsistent</option>
                <option value="none" className="text-black bg-white font-bold">No Defined Skincare Protocol</option>
              </select>
            </Field>

            <Field label="Alcohol Consumption">
              <select
                style={{ color: '#000000', backgroundColor: '#ffffff' }}
                className={inputCls}
                value={values.alcohol || ''}
                onChange={(e) => set('alcohol', e.target.value)}
              >
                <option value="" disabled className="text-slate-400 font-normal">-- Select Alcohol Consumption --</option>
                <option value="none" className="text-black bg-white font-bold">None</option>
                <option value="occasional" className="text-black bg-white font-bold">Occasional (1-2 / mo)</option>
                <option value="moderate" className="text-black bg-white font-bold">Moderate (Weekly)</option>
                <option value="heavy" className="text-black bg-white font-bold">Frequent / Daily</option>
              </select>
            </Field>

            <div className="pt-2">
              <label className="flex items-center gap-2.5 cursor-pointer text-xs text-slate-200 font-medium">
                <input
                  type="checkbox"
                  checked={Boolean(values.smoking)}
                  onChange={(e) => set('smoking', e.target.checked)}
                  className="rounded border-slate-400 bg-white text-medic-600 focus:ring-medic-500 h-4 w-4"
                />
                <span>Active Smoking or Nicotine Vaping</span>
              </label>
            </div>
          </div>
        </div>
      )}

      {/* Section 3: Exposome & Climate */}
      {activeSection === 'exposome' && (
        <div className="grid gap-4 sm:grid-cols-2 animate-rise">
          <Field label="Living Environment">
            <select
              style={{ color: '#000000', backgroundColor: '#ffffff' }}
              className={inputCls}
              value={values.location_type || ''}
              onChange={(e) => set('location_type', e.target.value)}
            >
              <option value="" disabled className="text-slate-400 font-normal">-- Select Living Environment --</option>
              <option value="urban" className="text-black bg-white font-bold">Dense Metropolitan Urban</option>
              <option value="suburban" className="text-black bg-white font-bold">Suburban</option>
              <option value="rural" className="text-black bg-white font-bold">Rural / Forested</option>
            </select>
          </Field>

          <Field label="Particulate Air Pollution (AQI)">
            <select
              style={{ color: '#000000', backgroundColor: '#ffffff' }}
              className={inputCls}
              value={values.pollution_level || ''}
              onChange={(e) => set('pollution_level', e.target.value)}
            >
              <option value="" disabled className="text-slate-400 font-normal">-- Select Air Pollution Level --</option>
              <option value="low" className="text-black bg-white font-bold">Low (AQI 0-50)</option>
              <option value="moderate" className="text-black bg-white font-bold">Moderate (AQI 51-100)</option>
              <option value="high" className="text-black bg-white font-bold">High (AQI 101-150)</option>
              <option value="very_high" className="text-black bg-white font-bold">Severe / Industrial (AQI 150+)</option>
            </select>
          </Field>

          <Field label="Solar UV Exposure">
            <select
              style={{ color: '#000000', backgroundColor: '#ffffff' }}
              className={inputCls}
              value={values.sun_exposure || ''}
              onChange={(e) => set('sun_exposure', e.target.value)}
            >
              <option value="" disabled className="text-slate-400 font-normal">-- Select Solar UV Exposure --</option>
              <option value="low" className="text-black bg-white font-bold">Low (Primarily Indoors)</option>
              <option value="moderate" className="text-black bg-white font-bold">Moderate (1-2 hrs daily)</option>
              <option value="high" className="text-black bg-white font-bold">High (Extended direct sun)</option>
            </select>
          </Field>

          <Field label="Ambient Humidity">
            <select
              style={{ color: '#000000', backgroundColor: '#ffffff' }}
              className={inputCls}
              value={values.humidity || ''}
              onChange={(e) => set('humidity', e.target.value)}
            >
              <option value="" disabled className="text-slate-400 font-normal">-- Select Ambient Humidity --</option>
              <option value="low" className="text-black bg-white font-bold">Dry / Arid (&lt; 35%)</option>
              <option value="moderate" className="text-black bg-white font-bold">Temperate (35-65%)</option>
              <option value="high" className="text-black bg-white font-bold">Humid / Tropical (&gt; 65%)</option>
            </select>
          </Field>

          <Field label="Climate Classification">
            <select
              style={{ color: '#000000', backgroundColor: '#ffffff' }}
              className={inputCls}
              value={values.climate || ''}
              onChange={(e) => set('climate', e.target.value)}
            >
              <option value="" disabled className="text-slate-400 font-normal">-- Select Climate --</option>
              <option value="temperate" className="text-black bg-white font-bold">Temperate</option>
              <option value="humid_subtropical" className="text-black bg-white font-bold">Humid Subtropical</option>
              <option value="arid" className="text-black bg-white font-bold">Arid / Desert</option>
              <option value="tropical" className="text-black bg-white font-bold">Tropical</option>
              <option value="continental" className="text-black bg-white font-bold">Continental / Cold</option>
            </select>
          </Field>

          <Field label="HVAC / Artificial Air Conditioning">
            <select
              style={{ color: '#000000', backgroundColor: '#ffffff' }}
              className={inputCls}
              value={values.ac_heating_exposure || ''}
              onChange={(e) => set('ac_heating_exposure', e.target.value)}
            >
              <option value="" disabled className="text-slate-400 font-normal">-- Select HVAC Exposure --</option>
              <option value="low" className="text-black bg-white font-bold">Minimal AC / Natural Air</option>
              <option value="moderate" className="text-black bg-white font-bold">Moderate Indoor HVAC</option>
              <option value="high" className="text-black bg-white font-bold">Continuous Artificial Air Conditioning</option>
            </select>
          </Field>
        </div>
      )}

      {/* Confirmation Checkbox */}
      <div className="pt-3 border-t border-slate-200">
        <label className="flex items-start gap-2.5 cursor-pointer text-xs text-slate-700 font-medium">
          <input
            type="checkbox"
            checked={Boolean(values.profile_confirmed)}
            onChange={(e) => set('profile_confirmed', e.target.checked)}
            className="mt-0.5 rounded border-slate-300 bg-white text-teal-700 focus:ring-teal-700 h-4 w-4"
          />
          <span className="leading-snug">
            I confirm these 21 biomarker fields represent the current clinical intake baseline. Fused output will formulate a Hayashi-standardized 3-month prognosis.
          </span>
        </label>
      </div>
    </div>
  )
}
