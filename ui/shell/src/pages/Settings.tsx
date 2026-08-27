import { Card, PageHead, Pill, SimTag, StateBox } from '../components/ui'
import { usePrefs, DEFAULT_PREFS } from '../prefs'
import type { DensityPref, TextSizePref, ThemePref } from '../prefs'
import { policySettings, pageRegistry } from '../fixture/ui00'

const THEMES: { value: ThemePref; label: string }[] = [
  { value: 'light', label: 'Light' },
  { value: 'dark', label: 'Dark' },
  { value: 'system', label: 'System' },
]

const DENSITIES: { value: DensityPref; label: string }[] = [
  { value: 'dense', label: 'Dense' },
  { value: 'compact', label: 'Compact readable' },
  { value: 'comfortable', label: 'Comfortable' },
  { value: 'spacious', label: 'Spacious' },
]

const TEXT_SIZES: { value: TextSizePref; label: string }[] = [
  { value: '90', label: '90%' },
  { value: '100', label: '100%' },
  { value: '110', label: '110%' },
  { value: '120', label: '120%' },
]

export default function Settings() {
  const { prefs, setPref, resetPrefs } = usePrefs()
  const p = policySettings

  return (
    <>
      <PageHead
        title="Settings"
        purpose="Interface preferences apply immediately and are real. Runtime policy sections show the planned safe defaults and are read-only in UI-00."
      />

      <Card
        title="Interface"
        sub="Stored in this browser only. These controls work now."
        actions={<Pill tone="ok">live</Pill>}
      >
        <div className="field">
          <label id="lbl-theme">Theme</label>
          <div className="seg" role="group" aria-labelledby="lbl-theme">
            {THEMES.map((t) => (
              <button
                key={t.value}
                type="button"
                aria-pressed={prefs.theme === t.value}
                onClick={() => setPref('theme', t.value)}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>

        <div className="field">
          <label id="lbl-text">Text size</label>
          <div className="seg" role="group" aria-labelledby="lbl-text">
            {TEXT_SIZES.map((t) => (
              <button
                key={t.value}
                type="button"
                aria-pressed={prefs.textSize === t.value}
                onClick={() => setPref('textSize', t.value)}
              >
                {t.label}
              </button>
            ))}
          </div>
          <span className="hint">Changes the type scale without inflating every spacing.</span>
        </div>

        <div className="field">
          <label id="lbl-density">Density</label>
          <div className="seg" role="group" aria-labelledby="lbl-density">
            {DENSITIES.map((d) => (
              <button
                key={d.value}
                type="button"
                aria-pressed={prefs.density === d.value}
                onClick={() => setPref('density', d.value)}
              >
                {d.label}
              </button>
            ))}
          </div>
          <span className="hint">
            Adjusts row heights and paddings, independent from text size (density-profile/v1).
          </span>
        </div>

        <div className="field">
          <label>
            <input
              type="checkbox"
              checked={prefs.highContrast}
              onChange={(e) => setPref('highContrast', e.target.checked)}
            />{' '}
            Stronger contrast
          </label>
          <label>
            <input
              type="checkbox"
              checked={prefs.reducedMotion}
              onChange={(e) => setPref('reducedMotion', e.target.checked)}
            />{' '}
            Reduce motion
          </label>
        </div>

        <div>
          <button
            type="button"
            className="btn"
            onClick={resetPrefs}
            disabled={JSON.stringify(prefs) === JSON.stringify(DEFAULT_PREFS)}
          >
            Reset interface preferences
          </button>
        </div>
      </Card>

      <div className="grid cols-2">
        <Card
          title="Privacy and retention"
          sub="Planned defaults — read-only until a runtime exists"
          actions={<SimTag label="planned policy" />}
        >
          <dl className="kv">
            <dt>Request content logging</dt>
            <dd>
              <Pill tone="ok">off</Pill> {p.payloadLogging.note}
            </dd>
            <dt>Payload retention</dt>
            <dd>{p.retention.payloads}</dd>
            <dt>Metadata retention</dt>
            <dd>{p.retention.metadata}</dd>
          </dl>
        </Card>

        <Card
          title="Cloud fallback"
          sub="Planned defaults — read-only until a runtime exists"
          actions={<SimTag label="planned policy" />}
        >
          <dl className="kv">
            <dt>Status</dt>
            <dd>
              <Pill tone="ok">disabled</Pill>
            </dd>
            <dt>Meaning</dt>
            <dd>{p.cloudFallback.note}</dd>
          </dl>
        </Card>
      </div>

      <div className="grid cols-2">
        <Card
          title="API and network"
          sub="Planned defaults — read-only until a runtime exists"
          actions={<SimTag label="planned policy" />}
        >
          <dl className="kv">
            <dt>Listener</dt>
            <dd>{p.networkExposure.value}</dd>
            <dt>Note</dt>
            <dd>{p.networkExposure.note}</dd>
          </dl>
        </Card>

        <Card title="About" sub="This console">
          <dl className="kv">
            <dt>Product</dt>
            <dd>Hermes Local AI Runtime — operations console</dd>
            <dt>Stage</dt>
            <dd>UI-00 shell, simulated data only</dd>
            <dt>Pages</dt>
            <dd>
              {pageRegistry.length} destinations, all marked{' '}
              <Pill tone="info">prototype</Pill>
            </dd>
          </dl>
        </Card>
      </div>

      <StateBox kind="permission" title="Runtime policy is locked">
        Route defaults, resource budgets, model store paths and backup policy become editable in the
        real console, each change showing its impact and rollback before applying. In UI-00 they are
        intentionally read-only.
      </StateBox>
    </>
  )
}
