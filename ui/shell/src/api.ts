/** Relative API helper. Works behind `/apps/local-ai-runtime/` and on loopback. */

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
  ) {
    super(message)
  }
}

function rootUrl(path: string): string {
  const base = new URL('.', window.location.href)
  return new URL(path.replace(/^\//, ''), base).toString()
}

async function parse(response: Response): Promise<unknown> {
  const text = await response.text()
  if (!text) return null
  try {
    return JSON.parse(text)
  } catch {
    return text
  }
}

export async function api<T = unknown>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers)
  if (init.body && !(init.body instanceof Uint8Array) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  const response = await fetch(rootUrl(path), {
    ...init,
    headers,
    credentials: 'include',
  })
  const body = await parse(response)
  if (!response.ok) {
    const err = (body as { error?: { code?: string; message?: string } })?.error
    throw new ApiError(
      response.status,
      err?.code || `HTTP_${response.status}`,
      err?.message || response.statusText,
    )
  }
  return body as T
}

export async function openSession(): Promise<void> {
  await api('/api/v1/console/session')
}

export async function uploadBytes(data: ArrayBuffer, contentType: string): Promise<string> {
  const body = await api<{ upload_id: string }>('/api/v1/uploads', {
    method: 'POST',
    headers: { 'Content-Type': contentType || 'application/octet-stream' },
    body: new Uint8Array(data),
  })
  return body.upload_id
}

const POLICY = {
  data_classification: 'internal',
  cloud_fallback_allowed: false,
  retention: 'none',
}

export async function submitJob(
  capability: string,
  input: Record<string, unknown>,
  profile: string,
  version = '1.0.0',
): Promise<{ job_id: string; status: string }> {
  return api('/api/v1/jobs', {
    method: 'POST',
    body: JSON.stringify({
      capability,
      capability_version: version,
      profile,
      input,
      policy: POLICY,
    }),
  })
}

export async function getJob(jobId: string): Promise<{
  job_id: string
  status: string
  error?: { code?: string; message?: string }
  timing?: Record<string, number>
  route_id?: string
}> {
  return api(`/api/v1/jobs/${jobId}`)
}

export async function getResult(jobId: string): Promise<Record<string, unknown>> {
  return api(`/api/v1/jobs/${jobId}/result`)
}

export async function waitJob(
  jobId: string,
  timeoutMs: number,
  onTick?: (status: string) => void,
): Promise<Record<string, unknown>> {
  const deadline = Date.now() + timeoutMs
  while (Date.now() < deadline) {
    const job = await getJob(jobId)
    onTick?.(job.status)
    if (job.status === 'succeeded') return getResult(jobId)
    if (['failed', 'cancelled', 'rejected'].includes(job.status)) {
      throw new ApiError(
        409,
        job.error?.code || job.status.toUpperCase(),
        job.error?.message || `Job ${job.status}`,
      )
    }
    await new Promise((r) => setTimeout(r, 400))
  }
  throw new ApiError(504, 'TIMEOUT', 'Le job n’a pas fini à temps.')
}
