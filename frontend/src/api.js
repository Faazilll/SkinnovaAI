const API_BASE = import.meta.env.VITE_API_URL || '/api'

const TOKEN_KEY = 'skinova_auth_token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token)
  } else {
    localStorage.removeItem(TOKEN_KEY)
  }
}

function authHeaders() {
  const token = getToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export async function predictValidate(file, questionnaire, requireFace = true) {
  const form = new FormData()
  form.append('file', file)
  form.append('questionnaire_json', JSON.stringify(questionnaire))
  form.append('require_face', String(requireFace))

  const headers = authHeaders()

  const res = await fetch(`${API_BASE}/predict/validate`, {
    method: 'POST',
    headers,
    body: form,
  })

  if (!res.ok) {
    const text = await res.text()
    let detail = text
    try {
      detail = JSON.parse(text).detail || text
    } catch {
      /* keep text */
    }
    throw new Error(detail || `Validation failed (${res.status})`)
  }
  return res.json()
}

export async function predictFusionUpload(file, questionnaire, requireFace = true) {
  const form = new FormData()
  form.append('file', file)
  form.append('questionnaire_json', JSON.stringify(questionnaire))
  form.append('require_face', String(requireFace))

  const headers = authHeaders()

  const res = await fetch(`${API_BASE}/predict/fusion/upload`, {
    method: 'POST',
    headers,
    body: form,
  })

  if (!res.ok) {
    const text = await res.text()
    let detail = text
    try {
      detail = JSON.parse(text).detail || text
    } catch {
      /* keep text */
    }
    throw new Error(detail || `Request failed (${res.status})`)
  }
  return res.json()
}

export async function predictFusionRecalculate(image, questionnaire) {
  const headers = {
    'Content-Type': 'application/json',
    ...authHeaders(),
  }

  const res = await fetch(`${API_BASE}/predict/fusion/recalculate`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ image, questionnaire }),
  })

  if (!res.ok) {
    const text = await res.text()
    let detail = text
    try {
      detail = JSON.parse(text).detail || text
    } catch {
      /* keep text */
    }
    throw new Error(detail || `Recalculation failed (${res.status})`)
  }
  return res.json()
}


export async function predictImage(file, requireFace = true) {
  const form = new FormData()
  form.append('file', file)
  form.append('require_face', String(requireFace))

  const headers = authHeaders()

  const res = await fetch(`${API_BASE}/predict/image`, {
    method: 'POST',
    headers,
    body: form,
  })

  if (!res.ok) {
    const text = await res.text()
    let detail = text
    try {
      detail = JSON.parse(text).detail || text
    } catch {
      /* keep text */
    }
    throw new Error(detail || `Image prediction failed (${res.status})`)
  }
  return res.json()
}

export async function healthCheck() {
  const res = await fetch(`${API_BASE}/health`)
  return res.json()
}

// Auth API
export async function apiRegister(email, password, name = '') {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, name }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || 'Registration failed')
  if (data.token) setToken(data.token)
  return data
}

export async function apiLogin(email, password) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || 'Login failed')
  if (data.token) setToken(data.token)
  return data
}

export async function apiGetMe() {
  const token = getToken()
  if (!token) return null
  const res = await fetch(`${API_BASE}/auth/me`, {
    headers: authHeaders(),
  })
  if (!res.ok) {
    setToken(null)
    return null
  }
  const data = await res.json()
  return data.user
}

export function apiLogout() {
  setToken(null)
}

// History API
export async function apiGetHistory() {
  const res = await fetch(`${API_BASE}/history`, {
    headers: authHeaders(),
  })
  if (!res.ok) {
    // Fallback to localStorage for guest
    try {
      return JSON.parse(localStorage.getItem('skinova_guest_scans') || '[]')
    } catch {
      return []
    }
  }
  const data = await res.json()
  return data.scans || []
}

export async function apiSaveScan(scanData, notes = '') {
  const token = getToken()
  // Save locally as backup for guest
  try {
    const local = JSON.parse(localStorage.getItem('skinova_guest_scans') || '[]')
    const guestItem = {
      id: Date.now(),
      created_at: new Date().toISOString(),
      severity: scanData.image?.severity ?? 0,
      severity_label: scanData.image?.severity_label || 'Clear / Mild',
      risk_percent: scanData.final_risk_percent ?? scanData.image?.risk_percent ?? 0,
      skin_health_score: scanData.skin_health_score ?? 80,
      image_attributes: {
        oiliness: scanData.image?.oiliness ?? 0,
        pores: scanData.image?.pores ?? 0,
        redness: scanData.image?.redness ?? 0,
        dark_spots: scanData.image?.dark_spots ?? 0,
        current_skin_condition: scanData.image?.current_skin_condition,
        problem_areas: scanData.image?.problem_areas || [],
        method: scanData.image?.method || 'improved_model',
      },
      data_scores: {
        hormonal: scanData.data?.hormonal_score ?? 0,
        lifestyle: scanData.data?.lifestyle_score ?? 0,
        environmental: scanData.data?.environmental_score ?? 0,
        combined: scanData.data?.combined_score ?? 0,
      },
      drivers: scanData.data?.drivers || [],
      trend: scanData.trend || [],
      recommendations: scanData.recommendations || {},
      notes,
    }
    local.unshift(guestItem)
    localStorage.setItem('skinova_guest_scans', JSON.stringify(local.slice(0, 30)))
  } catch (e) {
    console.error('Local backup failed', e)
  }

  if (!token) return { status: 'saved_locally' }

  const res = await fetch(`${API_BASE}/history`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
    body: JSON.stringify({ scan_data: scanData, notes }),
  })
  return res.json()
}

export async function apiDeleteScan(scanId) {
  // Delete from local backup
  try {
    const local = JSON.parse(localStorage.getItem('skinova_guest_scans') || '[]')
    const filtered = local.filter((s) => s.id !== scanId)
    localStorage.setItem('skinova_guest_scans', JSON.stringify(filtered))
  } catch {}

  const token = getToken()
  if (!token) return { status: 'deleted_locally' }

  const res = await fetch(`${API_BASE}/history/${scanId}`, {
    method: 'DELETE',
    headers: authHeaders(),
  })
  return res.json()
}
