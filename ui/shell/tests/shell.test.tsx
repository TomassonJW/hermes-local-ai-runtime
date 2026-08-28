import { render, screen, within, fireEvent } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { PrefsProvider } from '../src/prefs'
import { RuntimeProvider } from '../src/runtime'
import AppShell from '../src/AppShell'
import Try from '../src/pages/Try'
import Overview from '../src/pages/Overview'
import { JobsPage } from '../src/pages/Jobs'
import Resources from '../src/pages/Resources'
import Settings from '../src/pages/Settings'
import { NAV } from '../src/catalog'

function renderAt(path: string) {
  return render(
    <PrefsProvider>
      <RuntimeProvider>
        <MemoryRouter initialEntries={[path]}>
          <Routes>
            <Route path="/" element={<AppShell />}>
              <Route index element={<Try />} />
              <Route path="overview" element={<Overview />} />
              <Route path="jobs" element={<JobsPage />} />
              <Route path="resources" element={<Resources />} />
              <Route path="settings" element={<Settings />} />
            </Route>
          </Routes>
        </MemoryRouter>
      </RuntimeProvider>
    </PrefsProvider>,
  )
}

describe('UI-01 disconnected', () => {
  it('shows an honest off banner, not simulated jobs', async () => {
    renderAt('/')
    expect((await screen.findAllByText(/runtime éteint/i)).length).toBeGreaterThan(0)
    expect(screen.queryByText(/job_sim_/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/production[- ]ready/i)).not.toBeInTheDocument()
  })

  it('lists the essayer destination first', () => {
    renderAt('/')
    const nav = screen.getAllByRole('navigation', { name: /navigation principale/i })[0]
    expect(within(nav).getByText('Essayer')).toBeInTheDocument()
    expect(NAV[0].path).toBe('/')
  })
})

describe('UI-01 live try', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input)
        if (url.includes('/console/session')) {
          return new Response(JSON.stringify({ principal: 'console' }), { status: 200 })
        }
        if (url.includes('/capabilities')) {
          return new Response(
            JSON.stringify({
              capabilities: [
                {
                  id: 'text.generate',
                  version: '1.0.0',
                  profiles: ['balanced'],
                  routes: [{ profile: 'balanced', engine: 'dummy', resource_class: 'light' }],
                  status: 'available',
                },
              ],
            }),
            { status: 200 },
          )
        }
        if (url.includes('/resources')) {
          return new Response(
            JSON.stringify({
              admission: {
                heavy_leases: 0,
                light_leases: 0,
                queued: 0,
                queue_max: 8,
                mem_available_mib: 12000,
                memory_floor_mib: 4096,
              },
              budget: {
                heavy_slots: 1,
                light_slots: 2,
                queue_max: 8,
                memory_floor_available_mib: 4096,
                hard_memory_mib: 10240,
              },
              loadavg: [0.2, 0.2, 0.2],
              hardware_profile: 'hermes-cpu-8vcpu-16gib',
            }),
            { status: 200 },
          )
        }
        if (url.endsWith('/api/v1/jobs') && (!init || !init.method || init.method === 'GET')) {
          return new Response(JSON.stringify({ jobs: [] }), { status: 200 })
        }
        if (url.endsWith('/api/v1/jobs') && init?.method === 'POST') {
          return new Response(JSON.stringify({ job_id: 'job_live_1', status: 'queued' }), { status: 202 })
        }
        if (url.includes('/api/v1/jobs/job_live_1/result')) {
          return new Response(JSON.stringify({ result: { text: 'bonjour' } }), { status: 200 })
        }
        if (url.includes('/api/v1/jobs/job_live_1')) {
          return new Response(JSON.stringify({ job_id: 'job_live_1', status: 'succeeded' }), { status: 200 })
        }
        return new Response('nope', { status: 404 })
      }),
    )
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('lets the operator pick a function and run text.generate', async () => {
    renderAt('/')
    expect(await screen.findByText(/runtime allumé/i)).toBeInTheDocument()
    const writeBtn = await screen.findByRole('button', { name: /écrire un texte/i })
    fireEvent.click(writeBtn)
    const box = await screen.findByLabelText(/^texte$/i)
    fireEvent.change(box, { target: { value: 'hello' } })
    fireEvent.click(screen.getByRole('button', { name: /^lancer$/i }))
    expect((await screen.findAllByText(/bonjour/i)).length).toBeGreaterThan(0)
  })
})

describe('Settings', () => {
  it('keeps live interface preferences', () => {
    renderAt('/settings')
    expect(screen.getByText(/^Interface$/)).toBeInTheDocument()
    expect(screen.getByRole('group', { name: /density/i })).toBeInTheDocument()
  })
})
