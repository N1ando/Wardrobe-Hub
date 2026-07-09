const STORAGE_KEY = "wardrobehub_profile"

export function saveFitProfile({ measurements, fitPref }) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({ measurements, fitPref }))
}

export function getFitProfile() {
  const raw = localStorage.getItem(STORAGE_KEY)
  return raw ? JSON.parse(raw) : null
}

export function clearFitProfile() {
  localStorage.removeItem(STORAGE_KEY)
}