/**
 * UI-00 fixture — Hermes Local AI Runtime operations shell.
 *
 * Versioned, simulated installation state. Every value on every page comes
 * from this file. No system probe, no network call, no live metric.
 * The composition is mandated by ui/LOCAL-UI-CONTRACT.md §"UI-00
 * representative data".
 */

export const FIXTURE_VERSION = 'ui00-fixture/1.0.0'

export const DEMO_LABEL = 'Demo state — no runtime connected'

export type PageStatus = 'available' | 'prototype' | 'to-develop'

export interface PageRegistryEntry {
  path: string
  name: string
  status: PageStatus
  purpose: string
}

export const pageRegistry: PageRegistryEntry[] = [
  { path: '/', name: 'Overview', status: 'prototype', purpose: 'Is the runtime ready, what can it do, what needs attention.' },
  { path: '/capabilities', name: 'Capabilities', status: 'prototype', purpose: 'Stable contracts applications call, with routes and limits.' },
  { path: '/models', name: 'Models', status: 'prototype', purpose: 'Model lifecycle from discovery to approval, honestly separated.' },
  { path: '/jobs', name: 'Jobs', status: 'prototype', purpose: 'Every execution with queue, load, run and review state.' },
  { path: '/evaluations', name: 'Evaluations', status: 'prototype', purpose: 'Quality and resource comparisons that justify promotions.' },
  { path: '/resources', name: 'Resources', status: 'prototype', purpose: 'CPU, memory, queue and disk against the declared budget.' },
  { path: '/updates', name: 'Updates', status: 'prototype', purpose: 'Detected candidate updates. Nothing promotes automatically.' },
  { path: '/settings', name: 'Settings', status: 'prototype', purpose: 'Interface preferences and runtime policy, with safe defaults.' },
]

/* ------------------------------------------------------------------ */
/* System                                                              */
/* ------------------------------------------------------------------ */

export const system = {
  runtimeConnected: false,
  runtimeVersion: null as string | null,
  apiListener: '127.0.0.1 (loopback only, planned default)',
  reasons: [
    'No runtime backend is installed yet. This console is the UI-00 shell served with simulated data.',
    'Engine selection (G-03) and resource safety (G-04) gates have not run.',
  ],
  hardwareProfile: {
    id: 'hermes-cpu-8vcpu-16gib',
    cpu: '8 vCPU (x86_64, AVX-512 capable)',
    ram: '16 GiB',
    gpu: 'None',
    note: 'Pinned deployment profile A. Live VM measured slightly higher; budget stays conservative.',
  },
  budget: {
    normalCores: 4,
    burstCores: 6,
    softMemGib: 8,
    hardMemGib: 10,
    heavySlots: 1,
    lightSlots: 2,
    queueMax: 8,
  },
}

/* ------------------------------------------------------------------ */
/* Capabilities                                                        */
/* ------------------------------------------------------------------ */

export type CapabilityAvailability = 'simulated-ready' | 'no-route' | 'blocked-by-gate'

export interface Capability {
  id: string
  version: string
  family: 'text' | 'vision' | 'document' | 'audio' | 'search'
  summary: string
  availability: CapabilityAvailability
  profiles: string[]
  activeRoute: string | null
  sync: string
  limits: string
  dataClassMax: string
  cloudFallback: 'disabled'
  priority: 'P0' | 'P1' | 'P2'
}

export const capabilities: Capability[] = [
  {
    id: 'vision.analyze',
    version: '1',
    family: 'vision',
    summary: 'Answer an open question about one image.',
    availability: 'simulated-ready',
    profiles: ['fast', 'balanced', 'accurate'],
    activeRoute: 'vision-balanced@sim',
    sync: 'Sync under 1 image ≤ 4 MP, otherwise async job',
    limits: '1 image, ≤ 8k context, 60 s timeout',
    dataClassMax: 'Confidential',
    cloudFallback: 'disabled',
    priority: 'P0',
  },
  {
    id: 'document.ocr',
    version: '1',
    family: 'document',
    summary: 'Read the text printed on image pages.',
    availability: 'simulated-ready',
    profiles: ['fast', 'balanced'],
    activeRoute: 'ocr-cpu-standard@sim',
    sync: 'Sync for 1 page, async for multi-page',
    limits: '≤ 40 pages per job, 120 s timeout',
    dataClassMax: 'Confidential',
    cloudFallback: 'disabled',
    priority: 'P0',
  },
  {
    id: 'text.embed',
    version: '1',
    family: 'text',
    summary: 'Turn text into vectors the caller stores itself.',
    availability: 'simulated-ready',
    profiles: ['balanced'],
    activeRoute: 'embed-multilingual@sim',
    sync: 'Sync ≤ 64 texts per batch',
    limits: '≤ 8k characters per text, dimensions declared in result',
    dataClassMax: 'Confidential',
    cloudFallback: 'disabled',
    priority: 'P0',
  },
  {
    id: 'text.extract_structured',
    version: '1',
    family: 'text',
    summary: 'Fill a caller-provided JSON schema from text.',
    availability: 'no-route',
    profiles: ['balanced', 'accurate'],
    activeRoute: null,
    sync: 'Async by default',
    limits: 'Schema ≤ 64 fields, 4k context',
    dataClassMax: 'Confidential',
    cloudFallback: 'disabled',
    priority: 'P0',
  },
  {
    id: 'search.rerank',
    version: '1',
    family: 'search',
    summary: 'Reorder search candidates for one query.',
    availability: 'no-route',
    profiles: ['fast'],
    activeRoute: null,
    sync: 'Sync ≤ 100 candidates',
    limits: '≤ 100 candidates, each ≤ 2k characters',
    dataClassMax: 'Confidential',
    cloudFallback: 'disabled',
    priority: 'P0',
  },
  {
    id: 'audio.transcribe',
    version: '1',
    family: 'audio',
    summary: 'Transcribe a bounded audio file to text.',
    availability: 'blocked-by-gate',
    profiles: ['balanced'],
    activeRoute: null,
    sync: 'Always async',
    limits: '≤ 90 min audio, chunked, cancellable',
    dataClassMax: 'Confidential',
    cloudFallback: 'disabled',
    priority: 'P1',
  },
]

/* ------------------------------------------------------------------ */
/* Models                                                              */
/* ------------------------------------------------------------------ */

export type ModelStatus =
  | 'discovered'
  | 'candidate'
  | 'compatible'
  | 'benchmarked'
  | 'approved'
  | 'deprecated'
  | 'blocked'

export interface ModelEntry {
  id: string
  alias: string | null
  family: string
  status: ModelStatus
  licence: string
  licenceOk: boolean | null
  sizeGib: number | null
  quant: string | null
  engines: string[]
  loaded: 'loaded' | 'unloaded' | 'not-installed'
  capabilities: string[]
  updateCandidate: boolean
  note: string
}

export const models: ModelEntry[] = [
  {
    id: 'sim-vlm-2b-q4',
    alias: 'vision-balanced',
    family: 'Compact vision-language model (~2B)',
    status: 'approved',
    licence: 'Apache-2.0',
    licenceOk: true,
    sizeGib: 1.9,
    quant: 'Q4_K_M',
    engines: ['llama.cpp (candidate)'],
    loaded: 'unloaded',
    capabilities: ['vision.analyze', 'vision.classify'],
    updateCandidate: true,
    note: 'Simulated approved route for the vision family. Lazy-loaded, 5 min TTL in the simulated policy.',
  },
  {
    id: 'sim-ocr-standard',
    alias: 'ocr-cpu-standard',
    family: 'OCR pipeline (detector + recognizer)',
    status: 'approved',
    licence: 'Apache-2.0',
    licenceOk: true,
    sizeGib: 0.3,
    quant: null,
    engines: ['specialist worker'],
    loaded: 'loaded',
    capabilities: ['document.ocr'],
    updateCandidate: false,
    note: 'Simulated resident OCR worker; small footprint keeps it loaded.',
  },
  {
    id: 'sim-embed-multi',
    alias: 'embed-multilingual',
    family: 'Multilingual embedding model',
    status: 'approved',
    licence: 'MIT',
    licenceOk: true,
    sizeGib: 0.5,
    quant: 'INT8',
    engines: ['ONNX runtime (candidate)'],
    loaded: 'loaded',
    capabilities: ['text.embed'],
    updateCandidate: false,
    note: 'Simulated. Declares 768 dimensions, normalised vectors.',
  },
  {
    id: 'sim-text-1b',
    alias: null,
    family: 'Small text model (~1B)',
    status: 'candidate',
    licence: 'Apache-2.0',
    licenceOk: true,
    sizeGib: 0.8,
    quant: 'Q5_K_M',
    engines: ['llama.cpp (candidate)'],
    loaded: 'not-installed',
    capabilities: ['text.classify', 'text.extract_structured'],
    updateCandidate: false,
    note: 'Candidate only. Not used by any application. Needs benchmark before any route.',
  },
  {
    id: 'sim-vlm-7b',
    alias: null,
    family: 'Larger vision-language model (~7B)',
    status: 'blocked',
    licence: 'Research-only licence',
    licenceOk: false,
    sizeGib: 4.6,
    quant: 'Q4_K_M',
    engines: ['llama.cpp (candidate)'],
    loaded: 'not-installed',
    capabilities: ['vision.analyze'],
    updateCandidate: false,
    note: 'Blocked: licence does not allow this deployment. Cannot download, execute or route.',
  },
  {
    id: 'sim-whisper-small',
    alias: null,
    family: 'Speech-to-text (small)',
    status: 'discovered',
    licence: 'MIT',
    licenceOk: true,
    sizeGib: null,
    quant: null,
    engines: ['whisper.cpp (candidate)'],
    loaded: 'not-installed',
    capabilities: ['audio.transcribe'],
    updateCandidate: false,
    note: 'Metadata only. Audio work is gated behind G-08.',
  },
]

/* ------------------------------------------------------------------ */
/* Workers                                                             */
/* ------------------------------------------------------------------ */

export interface WorkerEntry {
  id: string
  kind: string
  state: 'ready' | 'stopped' | 'starting'
  model: string | null
  memMib: number
  leases: number
}

export const workers: WorkerEntry[] = [
  { id: 'worker-ocr-1', kind: 'OCR specialist', state: 'ready', model: 'ocr-cpu-standard', memMib: 410, leases: 0 },
  { id: 'worker-embed-1', kind: 'Embedding (ONNX)', state: 'ready', model: 'embed-multilingual', memMib: 620, leases: 0 },
  { id: 'worker-vlm-1', kind: 'Vision LLM (llama.cpp)', state: 'stopped', model: 'vision-balanced', memMib: 0, leases: 0 },
]

/* ------------------------------------------------------------------ */
/* Jobs                                                                */
/* ------------------------------------------------------------------ */

export type JobStatus = 'succeeded' | 'queued' | 'rejected-resources' | 'running' | 'failed' | 'cancelled'

export interface JobEntry {
  id: string
  consumer: string
  capability: string
  profile: string
  status: JobStatus
  submitted: string
  queuedMs: number | null
  loadMs: number | null
  runMs: number | null
  resourceClass: 'tiny' | 'light' | 'medium' | 'heavy'
  route: string | null
  reviewRequired: boolean
  warnings: string[]
  detail: string
}

export const jobs: JobEntry[] = [
  {
    id: 'job_sim_0193',
    consumer: 'demo-app',
    capability: 'document.ocr',
    profile: 'balanced',
    status: 'succeeded',
    submitted: '2026-08-27 21:14 (simulated)',
    queuedMs: 40,
    loadMs: 0,
    runMs: 2900,
    resourceClass: 'light',
    route: 'ocr-cpu-standard@sim',
    reviewRequired: false,
    warnings: [],
    detail: 'Single synthetic invoice page. Text extracted, no low-confidence region. Payload is never shown here.',
  },
  {
    id: 'job_sim_0194',
    consumer: 'demo-app',
    capability: 'vision.analyze',
    profile: 'balanced',
    status: 'queued',
    submitted: '2026-08-27 21:16 (simulated)',
    queuedMs: null,
    loadMs: null,
    runMs: null,
    resourceClass: 'heavy',
    route: 'vision-balanced@sim',
    reviewRequired: false,
    warnings: ['Vision model is unloaded; first run pays a cold-load delay.'],
    detail: 'Waiting for the single heavy slot. Position 1 in queue (simulated).',
  },
  {
    id: 'job_sim_0195',
    consumer: 'demo-batch',
    capability: 'vision.analyze',
    profile: 'accurate',
    status: 'rejected-resources',
    submitted: '2026-08-27 21:17 (simulated)',
    queuedMs: null,
    loadMs: null,
    runMs: null,
    resourceClass: 'heavy',
    route: null,
    reviewRequired: false,
    warnings: [],
    detail: 'Refused before start: accepting it would exceed the memory budget while a heavy job is queued. The runtime refuses explicitly instead of starting and hoping.',
  },
]

/* ------------------------------------------------------------------ */
/* Evaluations                                                         */
/* ------------------------------------------------------------------ */

export interface EvaluationEntry {
  id: string
  suite: string
  corpus: 'public-synthetic' | 'private-local' | 'holdout'
  target: string
  ranAt: string
  verdict: 'pass' | 'regression' | 'not-run'
  summary: string
}

export const evaluations: EvaluationEntry[] = [
  {
    id: 'eval_sim_007',
    suite: 'OCR exactness — printed pages',
    corpus: 'public-synthetic',
    target: 'ocr-cpu-standard@sim',
    ranAt: '2026-08-26 (simulated)',
    verdict: 'pass',
    summary: 'Simulated: 98.1% character accuracy on synthetic printed fixtures. Above the 97% promotion bar.',
  },
  {
    id: 'eval_sim_008',
    suite: 'Vision — document field questions',
    corpus: 'public-synthetic',
    target: 'vision-balanced@sim',
    ranAt: '2026-08-26 (simulated)',
    verdict: 'pass',
    summary: 'Simulated: answers the asked question on 41/50 fixture cases, abstains honestly on 6, wrong on 3.',
  },
  {
    id: 'eval_sim_009',
    suite: 'Vision — update candidate comparison',
    corpus: 'public-synthetic',
    target: 'vision-balanced rev. 2026-08 (update candidate)',
    ranAt: 'not run',
    verdict: 'not-run',
    summary: 'Required before the detected update can be promoted. Promotion stays blocked until this passes.',
  },
]

/* ------------------------------------------------------------------ */
/* Resources                                                           */
/* ------------------------------------------------------------------ */

export const resources = {
  pressure: 'normal' as 'normal' | 'elevated' | 'critical',
  cpu: { allocatedCores: 8, budgetNormal: 4, budgetBurst: 6, usedCores: 0.7 },
  memory: { allocatedGib: 16, softGib: 8, hardGib: 10, usedGib: 1.1, estimatedNextLoadGib: 2.1 },
  swap: { present: false, note: 'No swap device on the target VM. Overcommit fails hard; admission must refuse first.' },
  queue: { depth: 1, max: 8, oldestWaitS: 12 },
  disk: { modelStoreGib: 2.7, quotaGib: 30, freeGib: 56 },
  events: [
    { at: '21:17 (simulated)', kind: 'admission-refused', text: 'vision.analyze (accurate) refused: would exceed memory budget.' },
    { at: '21:16 (simulated)', kind: 'queue', text: 'vision.analyze (balanced) queued: heavy slot busy with pending load.' },
    { at: '20:41 (simulated)', kind: 'unload', text: 'vision-balanced unloaded after 5 min idle (TTL policy).' },
  ],
}

/* ------------------------------------------------------------------ */
/* Updates                                                             */
/* ------------------------------------------------------------------ */

export interface UpdateEntry {
  id: string
  target: string
  kind: 'model-revision' | 'engine-version' | 'licence-change'
  detected: string
  status: 'detected' | 'evaluation-required' | 'blocked'
  diskDeltaGib: number | null
  summary: string
}

export const updates: UpdateEntry[] = [
  {
    id: 'upd_sim_001',
    target: 'vision-balanced (sim-vlm-2b-q4)',
    kind: 'model-revision',
    detected: '2026-08-27 (simulated)',
    status: 'evaluation-required',
    diskDeltaGib: 2.0,
    summary: 'Upstream revision 2026-08 detected. Not promoted. Requires the comparison suite (eval_sim_009) and an explicit operator decision.',
  },
  {
    id: 'upd_sim_002',
    target: 'sim-vlm-7b',
    kind: 'licence-change',
    detected: '2026-08-25 (simulated)',
    status: 'blocked',
    diskDeltaGib: null,
    summary: 'Candidate stays blocked: research-only licence is incompatible with this deployment. No download permitted.',
  },
]

/* ------------------------------------------------------------------ */
/* Settings                                                            */
/* ------------------------------------------------------------------ */

export const policySettings = {
  cloudFallback: {
    enabled: false,
    note: 'Disabled by default. Enabling it is an explicit product decision per consumer and data class, never a silent retry.',
  },
  payloadLogging: {
    enabled: false,
    note: 'Request content is never logged. Only metadata (IDs, durations, statuses) is recorded.',
  },
  networkExposure: {
    value: 'Loopback only (planned default)',
    note: 'No public listener. Private tailnet exposure would be a separate explicit mission.',
  },
  retention: {
    payloads: 'None',
    metadata: '30 days (simulated default)',
  },
}
