// Concrete fixes, styled as actionable cards rather than a bullet list —
// this panel is the "here's what you do about it" money moment.
export default function SuggestionsPanel({ suggestions }) {
  return (
    <ol className="space-y-2.5">
      {(suggestions ?? []).map((text, index) => (
        <li key={index} className="flex gap-3 rounded-md border bg-gray-50 p-3">
          <span
            className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-blue-600 text-xs font-bold text-white"
            aria-hidden="true"
          >
            {index + 1}
          </span>
          <p className="text-sm text-gray-800">{text}</p>
        </li>
      ))}
    </ol>
  )
}
