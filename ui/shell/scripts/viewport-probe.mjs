/**
 * UI-00 viewport probe — headless CDP verification of the served shell.
 *
 * Usage: node scripts/viewport-probe.mjs [baseURL]
 *        (or set PROBE_BASE_URL; defaults to the local loopback server)
 * Default baseURL: http://127.0.0.1:8830/
 *
 * Verifies, on desktop (1280x900) and mobile (390x844):
 *  - every destination renders its h1 and the demo banner;
 *  - no console error / uncaught exception;
 *  - mobile nav dialog opens and closes;
 *  - screenshots saved to scripts/shots/ for human/agent inspection.
 */
import { spawn } from 'node:child_process'
import { readdirSync, existsSync, mkdirSync, writeFileSync } from 'node:fs'
import { rm } from 'node:fs/promises'
import { createServer } from 'node:net'
import { homedir } from 'node:os'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import WebSocket from './ws-mini.mjs'

const BASE = process.argv[2] ?? process.env.PROBE_BASE_URL ?? 'http://127.0.0.1:8830/'
const HERE = dirname(fileURLToPath(import.meta.url))
const SHOTS = join(HERE, 'shots')
mkdirSync(SHOTS, { recursive: true })

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

function findChrome() {
  const base = join(homedir(), '.cache/ms-playwright')
  const found = readdirSync(base)
    .filter((d) => d.startsWith('chromium-'))
    .sort()
    .reverse()
    .map((d) => join(base, d, 'chrome-linux', 'chrome'))
    .concat(
      readdirSync(base)
        .filter((d) => d.startsWith('chromium-'))
        .sort()
        .reverse()
        .map((d) => join(base, d, 'chrome-linux64', 'chrome')),
    )
    .find((p) => existsSync(p))
  if (found) return found
  for (const p of ['/usr/bin/chromium', '/usr/bin/google-chrome']) if (existsSync(p)) return p
  throw new Error('no chromium found')
}

function freePort() {
  return new Promise((resolve) => {
    const s = createServer()
    s.listen(0, '127.0.0.1', () => {
      const p = s.address().port
      s.close(() => resolve(p))
    })
  })
}

const PAGES = [
  { hash: '#/', h1: 'Overview' },
  { hash: '#/capabilities', h1: 'Capabilities' },
  { hash: '#/capabilities/vision.analyze', h1: 'vision.analyze' },
  { hash: '#/models', h1: 'Models' },
  { hash: '#/models/sim-vlm-2b-q4', h1: null },
  { hash: '#/jobs', h1: 'Jobs' },
  { hash: '#/jobs/job_sim_0195', h1: 'job_sim_0195' },
  { hash: '#/evaluations', h1: 'Evaluations' },
  { hash: '#/resources', h1: 'Resources' },
  { hash: '#/updates', h1: 'Updates' },
  { hash: '#/settings', h1: 'Settings' },
]

async function main() {
  const chrome = findChrome()
  const port = await freePort()
  const profile = `/tmp/hlar-probe-${Date.now()}`
  const browser = spawn(
    chrome,
    [
      '--headless=new',
      '--no-sandbox',
      '--disable-gpu',
      '--disable-dev-shm-usage',
      `--remote-debugging-port=${port}`,
      `--user-data-dir=${profile}`,
      'about:blank',
    ],
    { stdio: 'ignore' },
  )

  const problems = []
  try {
    let ws = null
    for (let i = 0; i < 50; i++) {
      await sleep(200)
      try {
        const res = await fetch(`http://127.0.0.1:${port}/json`)
        const tabs = await res.json()
        const page = tabs.find((t) => t.type === 'page')
        if (page) {
          ws = new WebSocket(page.webSocketDebuggerUrl)
          await ws.open()
          break
        }
      } catch {
        /* retry */
      }
    }
    if (!ws) throw new Error('CDP unreachable')

    let id = 0
    const pending = new Map()
    const consoleErrors = []
    ws.onMessage((raw) => {
      const msg = JSON.parse(raw)
      if (msg.id && pending.has(msg.id)) {
        pending.get(msg.id)(msg)
        pending.delete(msg.id)
      } else if (msg.method === 'Runtime.exceptionThrown') {
        consoleErrors.push(`exception: ${msg.params.exceptionDetails?.exception?.description ?? 'unknown'}`)
      } else if (msg.method === 'Runtime.consoleAPICalled' && msg.params.type === 'error') {
        consoleErrors.push(`console.error: ${(msg.params.args ?? []).map((a) => a.value ?? a.description ?? '').join(' ')}`)
      } else if (msg.method === 'Log.entryAdded' && msg.params.entry.level === 'error') {
        consoleErrors.push(`log: ${msg.params.entry.text}`)
      }
    })
    const send = (method, params = {}) =>
      Promise.race([
        new Promise((resolve) => {
          const mid = ++id
          pending.set(mid, resolve)
          ws.send(JSON.stringify({ id: mid, method, params }))
        }),
        sleep(10000).then(() => {
          throw new Error(`timeout: ${method}`)
        }),
      ])
    const evaluate = async (expr) => {
      const res = await send('Runtime.evaluate', { expression: expr, returnByValue: true })
      if (res.result?.exceptionDetails) {
        throw new Error(`evaluate failed: ${res.result.exceptionDetails.exception?.description}`)
      }
      return res.result?.result?.value
    }
    const shot = async (name) => {
      const res = await send('Page.captureScreenshot', { format: 'png' })
      writeFileSync(join(SHOTS, name), Buffer.from(res.result.data, 'base64'))
    }

    await send('Runtime.enable')
    await send('Log.enable')
    await send('Page.enable')

    /* ---------- Desktop pass ---------- */
    await send('Emulation.setDeviceMetricsOverride', { width: 1280, height: 900, deviceScaleFactor: 1, mobile: false })
    await send('Page.navigate', { url: BASE })
    await sleep(2500)

    for (const p of PAGES) {
      await evaluate(`location.hash = ${JSON.stringify(p.hash)}`)
      await sleep(700)
      const info = await evaluate(`(() => {
        const h1 = document.querySelector('main h1')
        const banner = document.querySelector('.demo-banner')
        const sidebarVisible = (() => {
          const el = document.querySelector('.sidebar')
          return el ? getComputedStyle(el).display !== 'none' : false
        })()
        return JSON.stringify({ h1: h1 ? h1.textContent : null, banner: !!banner, sidebarVisible })
      })()`)
      const { h1, banner, sidebarVisible } = JSON.parse(info)
      if (p.h1 && h1 !== p.h1) problems.push(`desktop ${p.hash}: h1 "${h1}" != "${p.h1}"`)
      if (p.h1 === null && !h1) problems.push(`desktop ${p.hash}: no h1 rendered`)
      if (!banner) problems.push(`desktop ${p.hash}: demo banner missing`)
      if (!sidebarVisible) problems.push(`desktop ${p.hash}: sidebar not visible`)
    }
    await evaluate(`location.hash = '#/'`)
    await sleep(700)
    await shot('desktop-overview.png')
    await evaluate(`location.hash = '#/models'`)
    await sleep(700)
    await shot('desktop-models.png')
    await evaluate(`location.hash = '#/resources'`)
    await sleep(700)
    await shot('desktop-resources.png')
    await evaluate(`location.hash = '#/jobs/job_sim_0195'`)
    await sleep(700)
    await shot('desktop-job-rejected.png')

    /* Dark theme check */
    await evaluate(`location.hash = '#/settings'`)
    await sleep(700)
    await evaluate(`(() => {
      const btns = [...document.querySelectorAll('.seg button')]
      const dark = btns.find((b) => b.textContent.trim() === 'Dark')
      if (dark) dark.click()
      return true
    })()`)
    await sleep(500)
    const theme = await evaluate(`document.documentElement.dataset.theme`)
    if (theme !== 'dark') problems.push(`settings: dark theme did not apply (got "${theme}")`)
    await shot('desktop-settings-dark.png')
    await evaluate(`(() => {
      const btns = [...document.querySelectorAll('.seg button')]
      const sys = btns.find((b) => b.textContent.trim() === 'System')
      if (sys) sys.click()
      return true
    })()`)
    await sleep(300)

    /* ---------- Mobile pass ---------- */
    await send('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 3, mobile: true })
    await send('Page.navigate', { url: BASE })
    await sleep(2500)

    const mobileInfo = JSON.parse(
      await evaluate(`(() => {
        const sidebar = document.querySelector('.sidebar')
        const toggle = document.querySelector('.nav-toggle')
        const overflowX = document.documentElement.scrollWidth > document.documentElement.clientWidth
        return JSON.stringify({
          sidebarHidden: sidebar ? getComputedStyle(sidebar).display === 'none' : true,
          toggleVisible: toggle ? getComputedStyle(toggle).display !== 'none' : false,
          overflowX,
        })
      })()`),
    )
    if (!mobileInfo.sidebarHidden) problems.push('mobile: sidebar should be hidden')
    if (!mobileInfo.toggleVisible) problems.push('mobile: nav toggle not visible')
    if (mobileInfo.overflowX) problems.push('mobile: horizontal overflow on overview')
    await shot('mobile-overview.png')

    await evaluate(`document.querySelector('.nav-toggle').click()`)
    await sleep(500)
    const dialogOpen = await evaluate(`(() => {
      const d = document.querySelector('dialog.nav-dialog')
      return d ? d.open : false
    })()`)
    if (!dialogOpen) problems.push('mobile: nav dialog did not open')
    await shot('mobile-nav-open.png')
    await evaluate(`(() => {
      const links = [...document.querySelectorAll('dialog.nav-dialog .nav-link')]
      const jobs = links.find((l) => l.textContent.includes('Jobs'))
      if (jobs) jobs.click()
      return true
    })()`)
    await sleep(700)
    const afterNav = JSON.parse(
      await evaluate(`(() => {
        const d = document.querySelector('dialog.nav-dialog')
        const h1 = document.querySelector('main h1')
        const overflowX = document.documentElement.scrollWidth > document.documentElement.clientWidth
        return JSON.stringify({ dialogClosed: d ? !d.open : true, h1: h1 ? h1.textContent : null, overflowX })
      })()`),
    )
    if (!afterNav.dialogClosed) problems.push('mobile: nav dialog stayed open after navigation')
    if (afterNav.h1 !== 'Jobs') problems.push(`mobile: expected Jobs page, got "${afterNav.h1}"`)
    if (afterNav.overflowX) problems.push('mobile: horizontal overflow on jobs')
    await shot('mobile-jobs.png')

    if (consoleErrors.length > 0) {
      for (const e of consoleErrors) problems.push(`console: ${e}`)
    }
  } finally {
    browser.kill('SIGTERM')
    await sleep(200)
    await rm(profile, { recursive: true, force: true }).catch(() => {})
  }

  if (problems.length) {
    console.log('PROBE: FAIL')
    for (const p of problems) console.log(' -', p)
    process.exitCode = 1
  } else {
    console.log('PROBE: PASS — all pages render, banner everywhere, no console errors, mobile nav OK')
    console.log('shots in', SHOTS)
  }
}

main().catch((e) => {
  console.error('PROBE ERROR:', e.message)
  process.exitCode = 2
})
