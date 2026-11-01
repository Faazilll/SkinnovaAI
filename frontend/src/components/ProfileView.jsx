import {
  Calendar,
  CheckCircle,
  FileText,
  Key,
  LogOut,
  ShieldCheck,
  User,
} from 'lucide-react'

export default function ProfileView({
  user,
  onOpenAuth,
  onLogout,
  history = [],
  onSelectTab,
}) {
  if (!user) {
    return (
      <div className="bg-white border border-slate-200 shadow-clinical rounded-2xl p-10 text-center max-w-xl mx-auto space-y-4">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-teal-50 border border-teal-200 text-teal-800">
          <User className="h-8 w-8" />
        </div>
        <div>
          <span className="text-[11px] font-sans text-teal-800 uppercase tracking-wider font-bold">
            GUEST CLINICAL SESSION
          </span>
          <h3 className="font-sans text-2xl font-bold text-slate-900 mt-1">
            Sign In to Clinical Registry
          </h3>
          <p className="mt-1.5 text-xs sm:text-sm text-slate-500 leading-relaxed font-sans">
            Authenticate with clinician credentials to synchronize evaluation histories, unlock encrypted database storage, and record longitudinal treatment responses.
          </p>
        </div>

        <div className="pt-2 flex justify-center">
          <button
            onClick={onOpenAuth}
            className="rounded-xl bg-teal-700 hover:bg-teal-800 px-6 py-2.5 text-xs font-semibold text-white shadow-sm transition cursor-pointer"
          >
            Authenticate / Register Now
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Profile Header */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-6 shadow-clinical">
        <div className="flex items-center gap-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-teal-700 text-xl font-bold text-white shadow-sm">
            {(user.name || user.email || 'U')[0].toUpperCase()}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="font-sans text-xl sm:text-2xl font-bold text-slate-900">
                {user.name || 'Clinician Account'}
              </h2>
              <span className="rounded-full bg-emerald-50 border border-emerald-200 px-2 py-0.5 text-[10px] font-sans font-bold text-emerald-800">
                Authorized Practitioner
              </span>
            </div>
            <p className="text-xs text-slate-500 font-mono mt-0.5">{user.email}</p>
          </div>
        </div>

        <button
          onClick={onLogout}
          className="flex items-center gap-2 rounded-xl border border-rose-200 bg-rose-50 px-4 py-2 text-xs font-semibold text-rose-800 hover:bg-rose-100 transition cursor-pointer"
        >
          <LogOut className="h-4 w-4" />
          <span>Sign Out</span>
        </button>
      </div>

      {/* Grid Specs */}
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="bg-white border border-slate-200 rounded-2xl p-5 space-y-1.5 shadow-clinical">
          <p className="text-[11px] font-sans text-slate-500 uppercase font-bold">Registry Status</p>
          <p className="font-sans text-lg font-bold text-slate-900 flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-teal-700" />
            <span>SQLite Active</span>
          </p>
          <p className="text-xs text-slate-400 font-sans">Persistent database storage</p>
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-5 space-y-1.5 shadow-clinical">
          <p className="text-[11px] font-sans text-slate-500 uppercase font-bold">Total Documented Scans</p>
          <p className="font-sans text-lg font-bold text-teal-800 font-mono">
            {history.length} records
          </p>
          <p className="text-xs text-slate-400 font-sans">Stored in patient timeline</p>
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-5 space-y-1.5 shadow-clinical">
          <p className="text-[11px] font-sans text-slate-500 uppercase font-bold">Member Since</p>
          <p className="font-sans text-base font-bold text-slate-800 font-sans">
            {user.created_at ? new Date(user.created_at).toLocaleDateString() : 'Active 2026'}
          </p>
          <p className="text-xs text-slate-400 font-sans">Verified account credential</p>
        </div>
      </div>
    </div>
  )
}
