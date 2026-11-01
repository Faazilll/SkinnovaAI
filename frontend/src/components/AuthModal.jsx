import { useEffect, useRef, useState } from 'react'
import { gsap } from 'gsap'
import { Lock, Mail, ShieldCheck, User, X, Zap } from 'lucide-react'
import { apiLogin, apiRegister } from '../api'

export default function AuthModal({ isOpen, onClose, onAuthSuccess }) {
  const [isRegister, setIsRegister] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const modalRef = useRef(null)

  useEffect(() => {
    if (isOpen && modalRef.current) {
      gsap.fromTo(
        modalRef.current,
        { opacity: 0, scale: 0.95, y: 10 },
        { opacity: 1, scale: 1, y: 0, duration: 0.3, ease: 'power2.out' }
      )
    }
  }, [isOpen])

  if (!isOpen) return null

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      let res
      if (isRegister) {
        res = await apiRegister(email, password, name)
      } else {
        res = await apiLogin(email, password)
      }
      onAuthSuccess(res.user)
      onClose()
    } catch (err) {
      setError(err.message || 'Authentication failed')
    } finally {
      setLoading(false)
    }
  }

  function handleQuickDemo() {
    setEmail('demo@skinova.ai')
    setPassword('password123')
    setIsRegister(false)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-xs">
      <div
        ref={modalRef}
        className="bg-white border border-slate-200 shadow-modal w-full max-w-md rounded-2xl p-6 sm:p-8 space-y-5"
      >
        <div className="flex items-center justify-between border-b border-slate-200 pb-4">
          <div>
            <span className="text-[11px] font-sans text-teal-800 uppercase tracking-wider font-bold">
              SECURITY ACCESS
            </span>
            <h3 className="font-sans text-xl font-bold text-slate-900 mt-0.5">
              {isRegister ? 'Clinician Registration' : 'Clinician Workstation Sign In'}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100 text-slate-500 hover:text-slate-800 transition cursor-pointer"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {isRegister && (
            <div>
              <label className="block text-xs font-sans text-slate-700 mb-1 font-semibold">
                Practitioner Full Name
              </label>
              <div className="relative">
                <User className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
                <input
                  type="text"
                  required
                  className="w-full rounded-lg border border-slate-300 bg-white px-10 py-2.5 text-xs text-slate-900 outline-none focus:border-teal-700 focus:ring-2 focus:ring-teal-700/15 font-sans"
                  placeholder="Dr. Jordan Hayes"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-sans text-slate-700 mb-1 font-semibold">
              Medical Email / Workstation ID
            </label>
            <div className="relative">
              <Mail className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
              <input
                type="email"
                required
                className="w-full rounded-lg border border-slate-300 bg-white px-10 py-2.5 text-xs text-slate-900 outline-none focus:border-teal-700 focus:ring-2 focus:ring-teal-700/15 font-sans"
                placeholder="clinician@hospital.org"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-sans text-slate-700 mb-1 font-semibold">
              Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
              <input
                type="password"
                required
                className="w-full rounded-lg border border-slate-300 bg-white px-10 py-2.5 text-xs text-slate-900 outline-none focus:border-teal-700 focus:ring-2 focus:ring-teal-700/15 font-sans"
                placeholder="••••••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          {error && (
            <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800 font-sans">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-teal-700 hover:bg-teal-800 py-3 text-xs font-bold text-white shadow-sm transition disabled:opacity-60 cursor-pointer"
          >
            {loading ? 'Validating Credentials...' : isRegister ? 'Create Practitioner Profile' : 'Authenticate Workstation'}
          </button>
        </form>

        {/* 1-Click Demo Button */}
        <div className="pt-2 border-t border-slate-200">
          <button
            type="button"
            onClick={handleQuickDemo}
            className="w-full flex items-center justify-center gap-2 rounded-xl border border-slate-300 bg-slate-50 hover:bg-slate-100 py-2 text-xs font-sans font-semibold text-teal-800 transition cursor-pointer"
          >
            <Zap className="h-4 w-4 text-teal-700" />
            <span>Fill 1-Click Clinician Demo Credentials</span>
          </button>
        </div>

        <div className="text-center text-xs text-slate-500">
          {isRegister ? 'Already registered?' : 'Need a clinician account?'}{' '}
          <button
            type="button"
            onClick={() => {
              setIsRegister(!isRegister)
              setError('')
            }}
            className="font-semibold text-teal-800 hover:text-teal-900 hover:underline cursor-pointer"
          >
            {isRegister ? 'Sign in instead' : 'Register new practitioner account'}
          </button>
        </div>
      </div>
    </div>
  )
}
