import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { createHashRouter, RouterProvider } from 'react-router-dom'
import './styles/app.css'
import { PrefsProvider } from './prefs'
import { RuntimeProvider } from './runtime'
import AppShell from './AppShell'
import Try from './pages/Try'
import Overview from './pages/Overview'
import { CapabilitiesPage, CapabilityDetail } from './pages/Capabilities'
import { ModelsPage, ModelDetail } from './pages/Models'
import { JobsPage, JobDetail } from './pages/Jobs'
import Evaluations from './pages/Evaluations'
import Resources from './pages/Resources'
import Updates from './pages/Updates'
import Settings from './pages/Settings'

export const router = createHashRouter([
  {
    path: '/',
    element: <AppShell />,
    children: [
      { index: true, element: <Try /> },
      { path: 'overview', element: <Overview /> },
      { path: 'capabilities', element: <CapabilitiesPage /> },
      { path: 'capabilities/:id', element: <CapabilityDetail /> },
      { path: 'models', element: <ModelsPage /> },
      { path: 'models/:id', element: <ModelDetail /> },
      { path: 'jobs', element: <JobsPage /> },
      { path: 'jobs/:id', element: <JobDetail /> },
      { path: 'evaluations', element: <Evaluations /> },
      { path: 'resources', element: <Resources /> },
      { path: 'updates', element: <Updates /> },
      { path: 'settings', element: <Settings /> },
    ],
  },
])

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <PrefsProvider>
      <RuntimeProvider>
        <RouterProvider router={router} />
      </RuntimeProvider>
    </PrefsProvider>
  </StrictMode>,
)
