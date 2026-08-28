import { useEffect, useRef } from 'react'
import { NavLink, Outlet, Link, useLocation } from 'react-router-dom'
import { NAV } from './catalog'
import { useRuntime } from './runtime'

const NAV_ICONS: Record<string, string> = {
  '/': '▶',
  '/overview': '⌂',
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
      {NAV.map((p) => (
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
  const { connected, loading, resources } = useRuntime()
  const mem = resources ? `${(resources.admission.mem_available_mib / 1024).toFixed(1)} Gio` : null
  const heavy = resources?.admission.heavy_leases ?? 0

  const openNav = () => dialogRef.current?.showModal()
  const closeNav = () => dialogRef.current?.close()

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
        Aller au contenu
      </a>

      <header className="topbar">
        <button type="button" className="icon-btn nav-toggle" aria-label="Ouvrir la navigation" onClick={openNav}>
          ☰
        </button>
        <div className="brand">
          <span className="name">IA locale</span>
          <span className="scope">console</span>
        </div>
        <div className="spacer" />
        {connected && mem ? (
          <span className="live-chip" title="Mémoire encore disponible sur la machine">
            {mem} libres · {heavy ? 'job lourd en cours' : 'aucun job lourd'}
          </span>
        ) : null}
        <Link to="/settings" className="icon-btn" aria-label="Réglages" title="Réglages">
          ⚙
        </Link>
        <a href="/" className="icon-btn" aria-label="Retour au Hub" title="Retour au Hub">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path
              d="M4 10.5 12 4l8 6.5V20a1 1 0 0 1-1 1h-5.5v-6h-3v6H5a1 1 0 0 1-1-1v-9.5Z"
              stroke="currentColor"
              strokeWidth="1.75"
              strokeLinejoin="round"
            />
          </svg>
        </a>
      </header>

      <div className={`demo-banner ${connected ? 'live' : 'off'}`} role="status">
        {loading ? (
          <span>Connexion au runtime…</span>
        ) : connected ? (
          <>
            <strong>Runtime allumé.</strong>
            <span>Loopback seulement. Pas de cloud. Les modèles se chargent au premier essai, puis se déchargent.</span>
          </>
        ) : (
          <>
            <strong>Runtime éteint.</strong>
            <span>Aucun chiffre n’est simulé. Les pages d’essai restent vides tant que le moteur n’écoute pas.</span>
          </>
        )}
      </div>

      <div className="body">
        <nav className="sidebar" aria-label="Navigation principale">
          <NavLinks />
        </nav>

        <main id="main" className="content" key={location.pathname}>
          <Outlet />
        </main>
      </div>

      <dialog ref={dialogRef} className="nav-dialog" aria-label="Navigation">
        <div className="nav-dialog-head">
          <div className="brand">
            <span className="name">IA locale</span>
          </div>
          <button type="button" className="icon-btn" onClick={closeNav} aria-label="Fermer la navigation">
            ✕
          </button>
        </div>
        <nav aria-label="Navigation principale (mobile)">
          <NavLinks onNavigate={closeNav} />
        </nav>
      </dialog>
    </div>
  )
}
