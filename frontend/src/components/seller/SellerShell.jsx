import { Link } from 'react-router-dom'

// Shared frame for the two seller pages: one header, one content width.
export default function SellerShell({ title, backTo, backLabel, children }) {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <div>
            {backTo && (
              <Link to={backTo} className="text-sm text-blue-700 hover:underline">
                &larr; {backLabel}
              </Link>
            )}
            <h1 className="text-2xl font-bold">{title}</h1>
          </div>
          <span className="text-sm font-semibold text-gray-400">FitOS Seller</span>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-6 py-6">{children}</main>
    </div>
  )
}

export function SectionCard({ title, children, className = '' }) {
  return (
    <section className={`rounded-lg border bg-white p-5 ${className}`}>
      <h3 className="mb-3 text-sm font-semibold text-gray-900">{title}</h3>
      {children}
    </section>
  )
}

export function ErrorBox({ message, onRetry }) {
  return (
    <div className="rounded-lg border border-red-200 bg-red-50 p-5 text-sm">
      <p className="font-semibold text-red-800">Couldn&apos;t load this view</p>
      <p className="mt-1 text-red-700">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-3 rounded-md border border-red-300 bg-white px-3 py-1.5 font-medium text-red-800 hover:bg-red-100"
        >
          Try again
        </button>
      )}
    </div>
  )
}

export function Skeleton({ className = '' }) {
  return <div className={`animate-pulse rounded-lg bg-gray-200 ${className}`} />
}
