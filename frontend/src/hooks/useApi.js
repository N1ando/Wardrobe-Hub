import { useCallback, useEffect, useState } from 'react'

// Tiny fetch-state hook: every seller page renders exactly one of
// loading skeleton / designed error box / data. No spinner can hang:
// the promise either resolves, rejects, or the user retries.
export function useApi(fetcher, deps) {
  const [tick, setTick] = useState(0)
  // Each settled result carries the request key it answered. While the
  // stored key differs from the current one (deps changed or reload bumped
  // tick), the hook reports loading — no state reset inside the effect.
  const [result, setResult] = useState(null)
  const key = JSON.stringify([...deps, tick])

  useEffect(() => {
    let alive = true
    fetcher()
      .then((data) => alive && setResult({ key, data, error: null }))
      .catch((error) => alive && setResult({ key, data: null, error }))
    return () => {
      alive = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick])

  const reload = useCallback(() => setTick((t) => t + 1), [])
  const settled = result !== null && result.key === key
  return {
    data: settled ? result.data : null,
    loading: !settled,
    error: settled ? result.error : null,
    reload,
  }
}
