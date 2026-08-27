import { render, screen, within } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { PrefsProvider } from '../src/prefs'
import AppShell from '../src/AppShell'
import Overview from '../src/pages/Overview'
import { CapabilitiesPage, CapabilityDetail } from '../src/pages/Capabilities'
import { ModelsPage, ModelDetail } from '../src/pages/Models'
import { JobsPage, JobDetail } from '../src/pages/Jobs'
import Evaluations from '../src/pages/Evaluations'
import Resources from '../src/pages/Resources'
import Updates from '../src/pages/Updates'
import Settings from '../src/pages/Settings'
import { pageRegistry, DEMO_LABEL, jobs, models } from '../src/fixture/ui00'

function renderAt(path: string) {
  return render(
    <PrefsProvider>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/" element={<AppShell />}>
            <Route index element={<Overview />} />
            <Route path="capabilities" element={<CapabilitiesPage />} />
            <Route path="capabilities/:id" element={<CapabilityDetail />} />
            <Route path="models" element={<ModelsPage />} />
            <Route path="models/:id" element={<ModelDetail />} />
            <Route path="jobs" element={<JobsPage />} />
            <Route path="jobs/:id" element={<JobDetail />} />
            <Route path="evaluations" element={<Evaluations />} />
            <Route path="resources" element={<Resources />} />
            <Route path="updates" element={<Updates />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </MemoryRouter>
    </PrefsProvider>,
  )
}

describe('UI-00 shell', () => {
  it('shows the demo banner on every destination', () => {
    for (const page of pageRegistry) {
      const { unmount } = renderAt(page.path)
      expect(screen.getAllByText(new RegExp(DEMO_LABEL, 'i')).length).toBeGreaterThan(0)
      unmount()
    }
  })

  it('renders all eight destinations in the main navigation', () => {
    renderAt('/')
    const nav = screen.getAllByRole('navigation', { name: /main navigation/i })[0]
    for (const page of pageRegistry) {
      expect(within(nav).getByText(page.name)).toBeInTheDocument()
    }
  })

  it('never claims a live or connected runtime', () => {
    renderAt('/')
    expect(screen.getByText(/not connected/i)).toBeInTheDocument()
    expect(screen.queryByText(/^connected$/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/production[- ]ready/i)).not.toBeInTheDocument()
  })
})

describe('Capabilities', () => {
  it('lists capability contracts with availability', () => {
    renderAt('/capabilities')
    expect(screen.getByText('vision.analyze')).toBeInTheDocument()
    expect(screen.getAllByText(/no approved route/i).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/blocked by gate/i).length).toBeGreaterThan(0)
  })

  it('shows a capability detail with disabled cloud fallback', () => {
    renderAt('/capabilities/vision.analyze')
    expect(screen.getByRole('heading', { name: 'vision.analyze' })).toBeInTheDocument()
    expect(screen.getAllByText(/disabled/i).length).toBeGreaterThan(0)
  })

  it('handles an unknown capability id honestly', () => {
    renderAt('/capabilities/does.not.exist')
    expect(screen.getByText(/unknown capability/i)).toBeInTheDocument()
  })
})

describe('Models', () => {
  it('separates lifecycle states and shows the blocked licence', () => {
    renderAt('/models')
    expect(screen.getByText(/approved \(3\)/i)).toBeInTheDocument()
    expect(screen.getByText(/candidate \(1\)/i)).toBeInTheDocument()
    expect(screen.getByText(/blocked \(1\)/i)).toBeInTheDocument()
    expect(screen.getByText(/research-only licence/i)).toBeInTheDocument()
  })

  it('renders a model detail with provenance and disabled actions', () => {
    const approved = models.find((m) => m.status === 'approved')!
    renderAt(`/models/${approved.id}`)
    expect(screen.getByText(/lifecycle actions/i)).toBeInTheDocument()
    const benchmarkBtn = screen.getByRole('button', { name: /run benchmark/i })
    expect(benchmarkBtn).toBeDisabled()
  })
})

describe('Jobs', () => {
  it('shows succeeded, queued and resource-refused jobs', () => {
    renderAt('/jobs')
    expect(screen.getByText('job_sim_0193')).toBeInTheDocument()
    expect(screen.getAllByText(/succeeded/i).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/queued/i).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/refused — not enough resources/i).length).toBeGreaterThan(0)
  })

  it('explains a resource rejection in plain language and hides payloads', () => {
    const rejected = jobs.find((j) => j.status === 'rejected-resources')!
    renderAt(`/jobs/${rejected.id}`)
    expect(screen.getByText(/why refused\?/i)).toBeInTheDocument()
    expect(screen.getByText(/payload hidden/i)).toBeInTheDocument()
  })
})

describe('Resources', () => {
  it('distinguishes allocation from budget and shows admission events', () => {
    renderAt('/resources')
    expect(screen.getAllByText(/hard/i).length).toBeGreaterThan(0)
    expect(screen.getByText(/recent admission decisions/i)).toBeInTheDocument()
    expect(screen.getAllByText(/no swap device/i).length).toBeGreaterThan(0)
  })
})

describe('Updates', () => {
  it('shows detected updates without any promote button', () => {
    renderAt('/updates')
    expect(screen.getByText(/evaluation required/i)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /promote|update now|install/i })).not.toBeInTheDocument()
  })
})

describe('Evaluations', () => {
  it('shows suites with corpus provenance and a not-run entry', () => {
    renderAt('/evaluations')
    expect(screen.getAllByText(/public synthetic/i).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/not run/i).length).toBeGreaterThan(0)
  })
})

describe('Settings', () => {
  it('offers live interface preferences and locked runtime policy', () => {
    renderAt('/settings')
    expect(screen.getByText(/^Interface$/)).toBeInTheDocument()
    expect(screen.getByRole('group', { name: /density/i })).toBeInTheDocument()
    expect(screen.getByText(/runtime policy is locked/i)).toBeInTheDocument()
    expect(screen.getAllByText(/disabled/i).length).toBeGreaterThan(0)
  })
})
