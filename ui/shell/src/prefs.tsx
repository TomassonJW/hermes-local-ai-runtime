import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'

/** Preference layer only (canon: preferences ≠ saved views ≠ workspace ≠ session). */

export type ThemePref = 'light' | 'dark' | 'system'
export type DensityPref = 'dense' | 'compact' | 'comfortable' | 'spacious'
export type TextSizePref = '90' | '100' | '110' | '120'

export interface Prefs {
  theme: ThemePref
  density: DensityPref
  textSize: TextSizePref
  highContrast: boolean
  reducedMotion: boolean
}

export const DEFAULT_PREFS: Prefs = {
  theme: 'system',
  density: 'compact',
  textSize: '100',
  highContrast: false,
  reducedMotion: false,
}

const STORAGE_KEY = 'hlar-ui00-prefs/v1'

interface PrefsCtx {
  prefs: Prefs
  setPref: <K extends keyof Prefs>(key: K, value: Prefs[K]) => void
  resetPrefs: () => void
}

const Ctx = createContext<PrefsCtx | null>(null)

function loadPrefs(): Prefs {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return DEFAULT_PREFS
    const parsed = JSON.parse(raw) as Partial<Prefs>
    return { ...DEFAULT_PREFS, ...parsed }
  } catch {
    return DEFAULT_PREFS
  }
}

export function PrefsProvider({ children }: { children: ReactNode }) {
  const [prefs, setPrefs] = useState<Prefs>(loadPrefs)

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs))
    } catch {
      /* storage unavailable: prefs stay session-only */
    }
    const root = document.documentElement
    const systemDark =
      typeof window.matchMedia === 'function' &&
      window.matchMedia('(prefers-color-scheme: dark)').matches
    const dark = prefs.theme === 'dark' || (prefs.theme === 'system' && systemDark)
    root.dataset.theme = dark ? 'dark' : 'light'
    root.dataset.density = prefs.density
    root.dataset.textsize = prefs.textSize
    root.dataset.contrast = prefs.highContrast ? 'high' : 'normal'
    root.dataset.motion = prefs.reducedMotion ? 'reduced' : 'normal'
  }, [prefs])

  const value = useMemo<PrefsCtx>(
    () => ({
      prefs,
      setPref: (key, v) => setPrefs((p) => ({ ...p, [key]: v })),
      resetPrefs: () => setPrefs(DEFAULT_PREFS),
    }),
    [prefs],
  )

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}

export function usePrefs(): PrefsCtx {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('usePrefs outside PrefsProvider')
  return ctx
}
