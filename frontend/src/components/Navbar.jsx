import { useEffect, useRef } from 'react'
import { gsap } from 'gsap'
import {
  Activity,
  Calendar,
  ChevronRight,
  Database,
  History,
  Layers,
  LineChart,
  LogOut,
  Microscope,
  ShieldCheck,
  User,
} from 'lucide-react'

export default function Navbar({
  activeTab,
  onSelectTab,
  user,
  onOpenAuth,
  onLogout,
  health,
  historyCount = 0,
}) {
  const navRef = useRef(null)

  useEffect(() => {
    if (navRef.current) {
      gsap.fromTo(
        navRef.current,
        { y: -15, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.6, ease: 'power2.out' }
      )
    }
  }, [])

  const navItems = [
    { id: 'analyze', label: 'Clinical Scanner', icon: Microscope, badge: null },
    { id: 'history', label: 'Patient Registry', icon: History, badge: historyCount },
    { id: 'analytics', label: 'Longitudinal Trends', icon: LineChart, badge: null },
    { id: 'profile', label: 'Practitioner Profile', icon: User, badge: null },
  ]

  return (
    <header
      ref={navRef}
      className="sticky top-3 z-50 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 mb-6"
    >
      <div className="bg-white/95 border border-slate-200 shadow-clinical rounded-2xl px-4 sm:px-6 py-3 transition-all backdrop-blur-md">
        <div className="flex items-center justify-between gap-4">
          {/* Clinical Brand Identity */}
          <div
            className="flex cursor-pointer items-center gap-3 group select-none"
            onClick={() => onSelectTab('analyze')}
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-teal-700 text-white shadow-sm transition">
              <Activity className="h-5 w-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-sans text-lg font-bold tracking-tight text-slate-900">
                  Skinova
                </span>
                <span className="rounded bg-teal-50 border border-teal-200 px-1.5 py-0.5 text-[10px] font-mono font-semibold tracking-wide text-teal-800">
                  CLINICAL DSS v2.4
                </span>
              </div>
              <p className="text-[11px] font-medium text-slate-500 flex items-center gap-1.5">
                <span>Multimodal Dermatology Intelligence</span>
                <span className="h-1 w-1 rounded-full bg-slate-300" />
                <span className="text-teal-700 font-mono text-[10px]">Dual-Engine</span>
              </p>
            </div>
          </div>

          {/* Clinical Desktop Navigation Tabs */}
          <nav className="hidden md:flex items-center gap-1 p-1 rounded-xl bg-slate-100 border border-slate-200">
            {navItems.map((tab) => {
              const Icon = tab.icon
              const isActive = activeTab === tab.id
              return (
                <button
                  key={tab.id}
                  onClick={() => onSelectTab(tab.id)}
                  className={`flex items-center gap-2 rounded-lg px-3.5 py-1.5 text-xs font-semibold transition-all ${
                    isActive
                      ? 'bg-white text-teal-800 shadow-sm border border-slate-200/80 font-bold'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/50'
                  }`}
                >
                  <Icon className={`h-4 w-4 ${isActive ? 'text-teal-700' : 'text-slate-500'}`} />
                  <span>{tab.label}</span>
                  {tab.badge !== null && tab.badge > 0 && (
                    <span
                      className={`ml-1 rounded-full px-1.5 py-0.2 text-[10px] font-mono font-bold ${
                        isActive
                          ? 'bg-teal-100 text-teal-800'
                          : 'bg-slate-200 text-slate-700'
                      }`}
                    >
                      {tab.badge}
                    </span>
                  )}
                </button>
              )
            })}
          </nav>

          {/* Right Status & Auth Bar */}
          <div className="flex items-center gap-3">


            {user ? (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => onSelectTab('profile')}
                  className="flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-800 transition hover:bg-slate-100"
                >
                  <div className="flex h-5 w-5 items-center justify-center rounded-full bg-teal-700 text-[10px] font-bold text-white shadow-sm">
                    {(user.name || user.email || 'U')[0].toUpperCase()}
                  </div>
                  <span className="max-w-[110px] truncate text-slate-800 font-medium">
                    {user.name || user.email}
                  </span>
                </button>
                <button
                  onClick={onLogout}
                  title="Sign out"
                  className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100 border border-slate-200 text-slate-600 transition hover:bg-rose-50 hover:border-rose-200 hover:text-rose-700"
                >
                  <LogOut className="h-4 w-4" />
                </button>
              </div>
            ) : (
              <button
                onClick={onOpenAuth}
                className="flex items-center gap-2 rounded-xl bg-teal-700 hover:bg-teal-800 px-4 py-2 text-xs font-semibold text-white shadow-sm transition"
              >
                <User className="h-3.5 w-3.5" />
                <span>Clinician Sign In</span>
              </button>
            )}
          </div>
        </div>

        {/* Mobile Sub-Navigation Bar */}
        <div className="mt-2.5 pt-2 border-t border-slate-200 flex md:hidden overflow-x-auto gap-1 justify-around">
          {navItems.map((tab) => {
            const Icon = tab.icon
            const isActive = activeTab === tab.id
            return (
              <button
                key={tab.id}
                onClick={() => onSelectTab(tab.id)}
                className={`flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-[11px] font-medium transition ${
                  isActive
                    ? 'bg-teal-700 text-white shadow-sm font-semibold'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <Icon className="h-3.5 w-3.5" />
                <span>{tab.label}</span>
                {tab.badge !== null && tab.badge > 0 && (
                  <span className="text-[10px] opacity-80">({tab.badge})</span>
                )}
              </button>
            )
          })}
        </div>
      </div>
    </header>
  )
}
