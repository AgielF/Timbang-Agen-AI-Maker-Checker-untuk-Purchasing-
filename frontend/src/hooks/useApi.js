import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../lib/api'

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
