import { useCallback, useEffect, useRef, useState } from 'react'
import { api, riskReportFromFiles } from '../lib/api'
import { API_BASE_URL } from '../lib/constants'

export function useApi(fn) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const abortRef = useRef(null)

  const run = useCallback(
    async (...args) => {
      abortRef.current?.abort()
      const controller = new AbortController()
      abortRef.current = controller

      setLoading(true)
      setError(null)
      try {
        const result = await fn(...args, { signal: controller.signal })
        setData(result)
        return result
      } catch (e) {
        if (e.name === 'AbortError') return
        setError(e)
        throw e
      } finally {
        if (!controller.signal.aborted) setLoading(false)
      }
    },
    [fn]
  )

  const reset = useCallback(() => {
    setData(null)
    setError(null)
    setLoading(false)
  }, [])

  useEffect(() => () => abortRef.current?.abort(), [])

  return { data, error, loading, run, reset }
}

export const useMatchThreeWay = () => useApi(api.matchThreeWay)
export const useRiskReport = () => useApi(api.riskReport)

export function useRiskReportFromFiles() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const abortRef = useRef(null)

  const reset = useCallback(() => {
    abortRef.current?.abort()
    abortRef.current = null
    setData(null)
    setError(null)
    setLoading(false)
  }, [])

  const submit = useCallback(async (txId, files, options = {}) => {
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller
    let timedOut = false
    const timeoutId = setTimeout(() => {
      timedOut = true
      controller.abort()
    }, 120_000)

    setLoading(true)
    setError(null)
    setData(null)

    try {
      const result = await riskReportFromFiles(txId, files, {
        ...options,
        signal: controller.signal,
      })
      setData(result)
      return result
    } catch (cause) {
      if (cause?.name === 'AbortError' && !timedOut) return undefined
      if (cause?.name === 'AbortError') {
        const timeoutError = new Error('Request timeout, coba lagi.')
        setError(timeoutError)
        throw timeoutError
      }
      const requestError = cause instanceof Error
        ? cause
        : new Error('Terjadi kesalahan saat memproses dokumen.')
      setError(requestError)
      throw requestError
    } finally {
      clearTimeout(timeoutId)
      if (abortRef.current === controller) {
        abortRef.current = null
        setLoading(false)
      }
    }
  }, [])

  useEffect(() => () => abortRef.current?.abort(), [])

  return { data, loading, error, submit, reset }
}

export function useMakerRecommendation() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const abortRef = useRef(null)

  const submit = useCallback(async (itemName, file) => {
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller

    const timeoutId = setTimeout(() => controller.abort(), 120_000)

    setLoading(true)
    setError(null)
    setData(null)

    try {
      const form = new FormData()
      form.append('item_name', itemName)
      form.append('file', file)

      let res
      try {
        res = await fetch(`${API_BASE_URL}/api/v1/procurement/items/recommend-with-file`, {
          method: 'POST',
          body: form,
          signal: controller.signal,
        })
      } catch (e) {
        if (e.name === 'AbortError') {
          setError('Request timeout, coba lagi')
          return
        }
        throw e
      }

      const text = await res.text()
      let payload = null
      if (text) {
        try { payload = JSON.parse(text) } catch { payload = text }
      }

      if (!res.ok) {
        const detail =
          (typeof payload === 'object' && (payload?.detail ?? payload?.message)) ||
          res.statusText ||
          `HTTP ${res.status}`
        setError(String(detail))
        return
      }

      setData(payload)
    } catch (e) {
      setError(e?.message ?? 'Terjadi kesalahan.')
    } finally {
      clearTimeout(timeoutId)
      if (abortRef.current === controller) setLoading(false)
    }
  }, [])

  useEffect(() => () => abortRef.current?.abort(), [])

  return { data, loading, error, submit }
}
