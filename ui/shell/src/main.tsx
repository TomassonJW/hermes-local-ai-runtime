import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { createHashRouter, RouterProvider } from 'react-router-dom'
import './styles/app.css'
import { PrefsProvider } from './prefs'
import AppShell from './AppShell'
import Overview from './pages/Overview'
import { CapabilitiesPage, CapabilityDetail } from './pages/Capabilities'
import { ModelsPage, ModelDetail } from './pages/Models'
import { JobsPage, JobDetail } from './pages/Jobs'
import Evaluations from './pages/Evaluations'
import Resources from './pages/Resources'
import Updates from './pages/Updates'
import Settings from './pages/Settings'

/* Hash routing keeps the shell servable from any static file server without
   rewrite rules — appropriate for a UI-00 preview surface. */
export const router = createHashRouter([
  {
    path: '/',
    element: <AppShell />,
    children: [
      { index: true, element: <Overview /> },
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
      <RouterProvider router={router} />
    </PrefsProvider>
  </StrictMode>,
)
