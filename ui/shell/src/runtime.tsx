import {
  createContext,
  createElement,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { api, openSession } from './api'

export interface Capability {
  id: string
  version: string
  profiles: string[]
  routes: { profile: string; engine: string; resource_class: string }[]
  status: string
}

export interface Resources {
  admission: {
    heavy_leases: number
    light_leases: number
    queued: number
    queue_max: number
    mem_available_mib: number
    memory_floor_mib: number
  }
  budget: {
    heavy_slots: number
    light_slots: number
    queue_max: number
    memory_floor_available_mib: number
    hard_memory_mib: number
  }
  loadavg: number[]
  hardware_profile: string
}

export interface JobRow {
  job_id: string
  capability: string
  profile: string
  status: string
  route_id?: string | null
  created_at?: number
  timing?: Record<string, number>
  error?: { code?: string; message?: string }
}

interface RuntimeState {
  connected: boolean
  loading: boolean
  error: string | null
  capabilities: Capability[]
  resources: Resources | null
  jobs: JobRow[]
  refresh: () => void
}

const Ctx = createContext<RuntimeState>({
  connected: false,
  loading: true,
  error: null,
  capabilities: [],
  resources: null,
  jobs: [],
  refresh: () => undefined,
})

export function useRuntime() {
  return useContext(Ctx)
}

export function RuntimeProvider({ children }: { children: ReactNode }) {
  const [loading, setLoading] = useState(true)
  const [connected, setConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [capabilities, setCapabilities] = useState<Capability[]>([])
  const [resources, setResources] = useState<Resources | null>(null)
  const [jobs, setJobs] = useState<JobRow[]>([])

  const refresh = () => {
    let cancelled = false
    setLoading(true)
    ;(async () => {
      try {
        await openSession()
        const [caps, res, jobList] = await Promise.all([
          api<{ capabilities: Capability[] }>('/api/v1/capabilities'),
          api<Resources>('/api/v1/resources'),
          api<{ jobs: JobRow[] }>('/api/v1/jobs'),
        ])
        if (cancelled) return
        setCapabilities(caps.capabilities)
        setResources(res)
        setJobs(jobList.jobs)
        setConnected(true)
        setError(null)
      } catch (err) {
        if (cancelled) return
        setConnected(false)
        setCapabilities([])
        setResources(null)
        setJobs([])
        setError(err instanceof Error ? err.message : 'Runtime injoignable')
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }

  useEffect(() => {
    const stop = refresh()
    const timer = window.setInterval(() => {
      if (document.hidden) return
      openSession()
        .then(() =>
          Promise.all([
            api<Resources>('/api/v1/resources'),
            api<{ jobs: JobRow[] }>('/api/v1/jobs'),
          ]),
        )
        .then(([res, jobList]) => {
          setResources(res)
          setJobs(jobList.jobs)
          setConnected(true)
          setError(null)
        })
        .catch(() => {
          setConnected(false)
        })
    }, 2000)
    return () => {
      stop()
      window.clearInterval(timer)
    }
  }, [])

  const value = useMemo(
    () => ({ connected, loading, error, capabilities, resources, jobs, refresh }),
    [connected, loading, error, capabilities, resources, jobs],
  )
  return createElement(Ctx.Provider, { value }, children)
}
