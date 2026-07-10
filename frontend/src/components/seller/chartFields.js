// Which size-chart fields each garment type needs — mirrors the backend's
// backend/app/core/fields.py. The dress's bust measurement lives in the DB's
// `chest` column, so we relabel it for display.
const REQUIRED_FIELDS = {
  shirt: ['chest', 'waist', 'sleeve'],
  top: ['chest', 'waist', 'sleeve'],
  jeans: ['waist', 'hips', 'inseam'],
  pants: ['waist', 'hips', 'inseam'],
  dress: ['chest', 'waist', 'hips'],
}

export function requiredFieldsFor(category) {
  return REQUIRED_FIELDS[(category || '').toLowerCase()] ?? ['chest', 'waist']
}

export function fieldLabel(category, field) {
  if ((category || '').toLowerCase() === 'dress' && field === 'chest') return 'bust'
  return field
}
