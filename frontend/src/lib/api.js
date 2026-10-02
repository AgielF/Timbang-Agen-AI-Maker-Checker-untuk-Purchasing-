import { API_BASE_URL } from './constants'

export class ApiError extends Error {
  constructor(message, status, payload) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.payload = payload
  }
}

async function request(path, { method = 'GET', body, signal } = {}) {
  let res
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: body ? JSON.stringify(body) : undefined,
      signal,
    })
  } catch (e) {
    if (e.name === 'AbortError') throw e
    throw new ApiError('Tidak dapat terhubung ke server.', 0, null)
  }

  const text = await res.text()
  let data = null
  if (text) {
    try { data = JSON.parse(text) } catch { data = text }
  }

  if (!res.ok) {
    const detail =
      (typeof data === 'object' && (data?.detail ?? data?.message)) ||
      res.statusText ||
      `HTTP ${res.status}`
    throw new ApiError(String(detail), res.status, data)
  }
  return data
}

export const api = {
  matchThreeWay: (transactionId, { po, gr, invoice }, opts = {}) =>
    request(`/api/v1/audit/transactions/${encodeURIComponent(transactionId)}/match`, {
      method: 'POST',
      body: { po, gr, invoice },
      ...opts,
    }),

  riskReport: (transactionId, payload = {}, opts = {}) =>
    request(`/api/v1/audit/transactions/${encodeURIComponent(transactionId)}/risk-report`, {
      method: 'POST',
      body: {
        has_level2_approval: false,
        has_complete_docs: true,
        ...payload,
      },
      ...opts,
    }),

  createFinding: (payload, opts = {}) =>
    request('/api/v1/audit/findings', { method: 'POST', body: payload, ...opts }),

  getFinding: (id, opts = {}) =>
    request(`/api/v1/audit/findings/${encodeURIComponent(id)}`, opts),
}
