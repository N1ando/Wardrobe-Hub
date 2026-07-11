import { Link } from 'react-router-dom'

export default function SellerShell({ title, backTo, backLabel, children }) {
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-ink/10 bg-surface">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-5">
          <div>
            {backTo && (
              <Link to={backTo} className="text-sm text-accent hover:underline">
                &larr; {backLabel}
              </Link>
            )}
            <h1 className="font-serif-strong text-4xl font-bold tracking-tight text-ink mt-1">{title}</h1>
          </div>
          <span className="text-sm font-semibold text-muted">Wardrobe-Hub Seller</span>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-6 py-8">{children}</main>
    </div>
  )
}

export function SectionCard({ title, children, className = '' }) {
  return (
    <section className={`rounded-xl border border-ink/10 bg-surface p-6 shadow-[var(--shadow-soft)] ${className}`}>
      <h3 className="font-serif-strong mb-4 text-lg font-bold text-ink">{title}</h3>
      {children}
    </section>
  )
}

export function ErrorBox({ message, onRetry }) {
  return (
    <div className="rounded-xl border border-red-200 bg-red-50 p-5 text-sm">
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
  return <div className={`animate-pulse rounded-xl bg-ink/10 ${className}`} />
}