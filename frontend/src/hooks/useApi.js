import { useCallback, useEffect, useState } from 'react'

// Tiny fetch-state hook: every seller page renders exactly one of
// loading skeleton / designed error box / data. No spinner can hang:
// the promise either resolves, rejects, or the user retries.
export function useApi(fetcher, deps) {
  const [state, setState] = useState({ data: null, loading: true, error: null })
  const [tick, setTick] = useState(0)

  useEffect(() => {
    let alive = true
    setState({ data: null, loading: true, error: null })
    fetcher()
      .then((data) => alive && setState({ data, loading: false, error: null }))
      .catch((error) => alive && setState({ data: null, loading: false, error }))
    return () => {
      alive = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick])

  const reload = useCallback(() => setTick((t) => t + 1), [])
  return { ...state, reload }
}
