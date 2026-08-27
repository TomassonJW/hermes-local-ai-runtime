import type { ReactNode } from 'react'
import { DEMO_LABEL } from '../fixture/ui00'

/** Status pill: text + dot, never colour-only. */
export function Pill({
  tone,
  children,
}: {
  tone: 'ok' | 'warn' | 'danger' | 'info' | 'neutral'
  children: ReactNode
}) {
  return (
    <span className={`pill ${tone}`}>
      <span className="dot" aria-hidden="true" />
      {children}
    </span>
  )
}

/** Marks a value or block as simulated fixture data. */
export function SimTag({ label = 'simulated' }: { label?: string }) {
  return (
    <span className="sim-tag" title={DEMO_LABEL}>
      <span aria-hidden="true">◌</span>
      {label}
    </span>
  )
}

export function PageHead({
  title,
  purpose,
  children,
}: {
  title: string
  purpose: string
  children?: ReactNode
}) {
  return (
    <header className="page-head">
      <div className="row">
        <h1>{title}</h1>
        {children}
      </div>
      <p className="purpose">{purpose}</p>
    </header>
  )
}

export function Card({
  title,
  sub,
  actions,
  flush,
  children,
}: {
  title?: string
  sub?: string
  actions?: ReactNode
  flush?: boolean
  children: ReactNode
}) {
  return (
    <section className="card">
      {title ? (
        <div className="card-head">
          <h2>{title}</h2>
          {actions}
          {sub ? <span className="sub">{sub}</span> : null}
        </div>
      ) : null}
      <div className={`card-body${flush ? ' flush' : ''}`}>{children}</div>
    </section>
  )
}

/**
 * Explicit non-nominal state (empty / unavailable / blocked / degraded /
 * permission / stale / loading). States explain consequence + next action.
 */
export function StateBox({
  kind,
  title,
  children,
}: {
  kind:
    | 'empty'
    | 'loading'
    | 'unavailable'
    | 'blocked'
    | 'degraded'
    | 'permission'
    | 'stale'
    | 'failure'
  title: string
  children?: ReactNode
}) {
  const icons: Record<string, string> = {
    empty: '∅',
    loading: '…',
    unavailable: '⏻',
    blocked: '⛔',
    degraded: '△',
    permission: '🔒',
    stale: '⌛',
    failure: '✕',
  }
  return (
    <div className="state-box" data-state={kind}>
      <span className="title">
        <span aria-hidden="true">{icons[kind]}</span>
        {title}
      </span>
      {children}
    </div>
  )
}

export function Meter({
  label,
  used,
  max,
  unit,
  tone = 'ok',
  detail,
}: {
  label: string
  used: number
  max: number
  unit: string
  tone?: 'ok' | 'warn'
  detail?: string
}) {
  const pct = max > 0 ? Math.min(100, Math.round((used / max) * 100)) : 0
  return (
    <div className={`meter ${tone}`}>
      <div className="meter-row">
        <span>{label}</span>
        <span>
          {used} / {max} {unit}
        </span>
      </div>
      <div
        className="track"
        role="meter"
        aria-label={label}
        aria-valuenow={used}
        aria-valuemin={0}
        aria-valuemax={max}
      >
        <div className="fill" style={{ width: `${pct}%` }} />
      </div>
      {detail ? <span className="note">{detail}</span> : null}
    </div>
  )
}
