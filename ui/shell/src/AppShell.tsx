import { useEffect, useRef } from 'react'
import { NavLink, Outlet, Link, useLocation } from 'react-router-dom'
import { pageRegistry, DEMO_LABEL, FIXTURE_VERSION } from './fixture/ui00'

const NAV_ICONS: Record<string, string> = {
  '/': '⌂',
  '/capabilities': '⬡',
  '/models': '▣',
  '/jobs': '≡',
  '/evaluations': '☑',
  '/resources': '◔',
  '/updates': '⇪',
  '/settings': '⚙',
}

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <>
      {pageRegistry.map((p) => (
        <NavLink
          key={p.path}
          to={p.path}
          end={p.path === '/'}
          className="nav-link"
          onClick={onNavigate}
        >
          <span className="icon" aria-hidden="true">
            {NAV_ICONS[p.path]}
          </span>
          {p.name}
        </NavLink>
      ))}
    </>
  )
}

export default function AppShell() {
  const dialogRef = useRef<HTMLDialogElement>(null)
  const location = useLocation()

  const openNav = () => dialogRef.current?.showModal()
  const closeNav = () => dialogRef.current?.close()

  /* Single responsive threshold: 880px (same value as CSS). Returning to a
     wider viewport closes the mobile nav layer instead of leaving it modal. */
  useEffect(() => {
    if (typeof window.matchMedia !== 'function') return
    const mq = window.matchMedia('(max-width: 880px)')
    const onChange = () => {
      if (!mq.matches) dialogRef.current?.close()
    }
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [])

  return (
    <div className="app">
      <a href="#main" className="skip-link">
        Skip to content
      </a>

      <header className="topbar">
        <button
          type="button"
          className="icon-btn nav-toggle"
          aria-label="Open navigation"
          onClick={openNav}
        >
          ☰
        </button>
        <div className="brand">
          <span className="name">Hermes Local AI Runtime</span>
          <span className="scope">Operations console</span>
        </div>
        <div className="spacer" />
        <Link to="/settings" className="icon-btn" aria-label="Settings" title="Settings">
          ⚙
        </Link>
      </header>

      <div className="demo-banner" role="status">
        <strong>{DEMO_LABEL}.</strong>
        <span>
          Every value on every page is a simulated fixture ({FIXTURE_VERSION}). No backend is
          installed, no model is downloaded, nothing is live.
        </span>
      </div>

      <div className="body">
        <nav className="sidebar" aria-label="Main navigation">
          <NavLinks />
          <span className="nav-section">Shell</span>
          <span className="note" style={{ padding: '0 10px' }}>
            UI-00 — all pages are prototypes over the same simulated installation.
          </span>
        </nav>

        <main id="main" className="content" key={location.pathname}>
          <Outlet />
        </main>
      </div>

      <dialog ref={dialogRef} className="nav-dialog" aria-label="Navigation">
        <div className="nav-dialog-head">
          <div className="brand">
            <span className="name">Hermes Local AI Runtime</span>
          </div>
          <button type="button" className="icon-btn" onClick={closeNav} aria-label="Close navigation">
            ✕
          </button>
        </div>
        <nav aria-label="Main navigation (mobile)">
          <NavLinks onNavigate={closeNav} />
        </nav>
      </dialog>
    </div>
  )
}
