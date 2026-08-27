import { Link, useNavigate, useParams } from 'react-router-dom'
import { Card, PageHead, Pill, SimTag, StateBox } from '../components/ui'
import { models } from '../fixture/ui00'
import type { ModelEntry, ModelStatus } from '../fixture/ui00'

const STATUS_LABEL: Record<ModelStatus, { label: string; tone: 'ok' | 'warn' | 'danger' | 'info' | 'neutral'; help: string }> = {
  discovered: { label: 'discovered', tone: 'neutral', help: 'Metadata only. Nothing downloaded.' },
  candidate: { label: 'candidate', tone: 'info', help: 'May be evaluated in isolation. Not used by applications.' },
  compatible: { label: 'compatible', tone: 'info', help: 'Loads and passes a smoke test.' },
  benchmarked: { label: 'benchmarked', tone: 'info', help: 'Has reproducible quality and resource results.' },
  approved: { label: 'approved', tone: 'ok', help: 'May serve named routes.' },
  deprecated: { label: 'deprecated', tone: 'warn', help: 'Kept for rollback and compatibility.' },
  blocked: { label: 'blocked', tone: 'danger', help: 'Cannot download, execute or route.' },
}

function StatusPill({ s }: { s: ModelStatus }) {
  const meta = STATUS_LABEL[s]
  return <Pill tone={meta.tone}>{meta.label}</Pill>
}

const LIFECYCLE_ORDER: ModelStatus[] = [
  'approved',
  'benchmarked',
  'compatible',
  'candidate',
  'discovered',
  'deprecated',
  'blocked',
]

export function ModelsPage() {
  const navigate = useNavigate()
  const groups = LIFECYCLE_ORDER.map((s) => ({
    status: s,
    items: models.filter((m) => m.status === s),
  })).filter((g) => g.items.length > 0)

  return (
    <>
      <PageHead
        title="Models"
        purpose="Model lifecycle from discovery to approval. Newest is never equivalent to recommended; only approved models serve applications."
      >
        <SimTag label="simulated catalogue" />
      </PageHead>

      {groups.map((g) => (
        <Card
          key={g.status}
          title={`${STATUS_LABEL[g.status].label} (${g.items.length})`}
          sub={STATUS_LABEL[g.status].help}
          flush
        >
          <div className="table-wrap">
            <table className="data stack">
              <thead>
                <tr>
                  <th scope="col">Model</th>
                  <th scope="col">Licence</th>
                  <th scope="col">Size</th>
                  <th scope="col">Loaded</th>
                  <th scope="col">Serves</th>
                </tr>
              </thead>
              <tbody>
                {g.items.map((m) => (
                  <tr
                    key={m.id}
                    className="rowlink"
                    tabIndex={0}
                    onClick={() => navigate(`/models/${m.id}`)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') navigate(`/models/${m.id}`)
                    }}
                  >
                    <td data-label="Model">
                      <span>{m.family}</span>
                      {m.alias ? (
                        <span className="note" style={{ display: 'block' }}>
                          route alias: <span className="mono">{m.alias}</span>
                        </span>
                      ) : null}
                    </td>
                    <td data-label="Licence">
                      {m.licenceOk === false ? (
                        <Pill tone="danger">{m.licence}</Pill>
                      ) : (
                        m.licence
                      )}
                    </td>
                    <td data-label="Size">{m.sizeGib != null ? `${m.sizeGib} GiB` : 'unknown'}</td>
                    <td data-label="Loaded">
                      {m.loaded === 'loaded' ? (
                        <Pill tone="ok">loaded</Pill>
                      ) : m.loaded === 'unloaded' ? (
                        <Pill tone="neutral">unloaded</Pill>
                      ) : (
                        <Pill tone="neutral">not installed</Pill>
                      )}
                    </td>
                    <td data-label="Serves">
                      {m.capabilities.map((c) => (
                        <span key={c} className="mono" style={{ marginRight: 8 }}>
                          {c}
                        </span>
                      ))}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      ))}
    </>
  )
}

export function ModelDetail() {
  const { id } = useParams()
  const model = models.find((m) => m.id === id)

  if (!model) {
    return (
      <>
        <Link to="/models" className="back-link">
          ← Models
        </Link>
        <StateBox kind="failure" title="Unknown model">
          No model with id <span className="mono">{id}</span> in this fixture.
        </StateBox>
      </>
    )
  }

  return <ModelDetailBody model={model} />
}

function ModelDetailBody({ model }: { model: ModelEntry }) {
  return (
    <>
      <Link to="/models" className="back-link">
        ← Models
      </Link>
      <PageHead title={model.family} purpose={model.note}>
        <StatusPill s={model.status} />
        <SimTag />
      </PageHead>

      <div className="grid cols-2">
        <Card title="Identity and provenance">
          <dl className="kv">
            <dt>Fixture id</dt>
            <dd>
              <span className="mono">{model.id}</span>
            </dd>
            <dt>Route alias</dt>
            <dd>{model.alias ? <span className="mono">{model.alias}</span> : 'none — not routed'}</dd>
            <dt>Licence</dt>
            <dd>
              {model.licence}{' '}
              {model.licenceOk === false ? <Pill tone="danger">incompatible</Pill> : <Pill tone="ok">allowed</Pill>}
            </dd>
            <dt>Artefact hash</dt>
            <dd>
              <span className="mono">sha256:… (recorded at real download; none exists yet)</span>
            </dd>
            <dt>Quantisation</dt>
            <dd>{model.quant ?? 'not applicable'}</dd>
            <dt>Engines</dt>
            <dd>{model.engines.join(', ')}</dd>
            <dt>Disk</dt>
            <dd>{model.sizeGib != null ? `${model.sizeGib} GiB` : 'unknown until download'}</dd>
          </dl>
        </Card>

        <Card title="Operational state">
          <dl className="kv">
            <dt>Loaded</dt>
            <dd>
              {model.loaded === 'loaded'
                ? 'Loaded in memory (simulated)'
                : model.loaded === 'unloaded'
                  ? 'Installed, not in memory. Next call pays a cold load.'
                  : 'Not installed on disk.'}
            </dd>
            <dt>Serves</dt>
            <dd>
              {model.capabilities.map((c) => (
                <Link key={c} to={`/capabilities/${c}`} className="mono" style={{ marginRight: 8 }}>
                  {c}
                </Link>
              ))}
            </dd>
            <dt>Update</dt>
            <dd>
              {model.updateCandidate ? (
                <>
                  <Pill tone="warn">newer revision detected</Pill>{' '}
                  <Link to="/updates">See Updates</Link>
                </>
              ) : (
                'No newer revision known.'
              )}
            </dd>
          </dl>
        </Card>
      </div>

      <Card title="Lifecycle actions" sub="What an operator could do from here, with consequences shown first">
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <button type="button" className="btn" disabled title="Disabled in UI-00: no runtime backend">
            Run benchmark…
          </button>
          <button type="button" className="btn" disabled title="Disabled in UI-00: no runtime backend">
            {model.status === 'approved' ? 'Deprecate…' : 'Promote…'}
          </button>
        </div>
        <span className="note">
          Actions are disabled in UI-00 because no runtime exists. In the real console each action
          first shows its impact (routes affected, disk, rollback path) before asking for
          confirmation.
        </span>
        {model.status === 'blocked' ? (
          <StateBox kind="blocked" title="Why this model is blocked">
            Its licence does not permit this deployment. A blocked model cannot be downloaded,
            executed or routed, whatever its quality claims.
          </StateBox>
        ) : null}
      </Card>
    </>
  )
}
