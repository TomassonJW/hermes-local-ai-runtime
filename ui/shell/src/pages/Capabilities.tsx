import { Link, useNavigate, useParams } from 'react-router-dom'
import { Card, PageHead, Pill, SimTag, StateBox } from '../components/ui'
import { capabilities } from '../fixture/ui00'
import type { Capability } from '../fixture/ui00'

function AvailabilityPill({ a }: { a: Capability['availability'] }) {
  if (a === 'simulated-ready') return <Pill tone="ok">route ready (simulated)</Pill>
  if (a === 'no-route') return <Pill tone="neutral">no approved route</Pill>
  return <Pill tone="warn">blocked by gate</Pill>
}

export function CapabilitiesPage() {
  const navigate = useNavigate()
  return (
    <>
      <PageHead
        title="Capabilities"
        purpose="The stable contracts applications call. Capabilities stay the same while models and engines behind them change."
      >
        <SimTag label="simulated installation" />
      </PageHead>

      <Card flush>
        <div className="table-wrap">
          <table className="data stack">
            <thead>
              <tr>
                <th scope="col">Capability</th>
                <th scope="col">Availability</th>
                <th scope="col">Active route</th>
                <th scope="col">Profiles</th>
                <th scope="col">Priority</th>
              </tr>
            </thead>
            <tbody>
              {capabilities.map((c) => (
                <tr
                  key={c.id}
                  className="rowlink"
                  tabIndex={0}
                  onClick={() => navigate(`/capabilities/${c.id}`)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') navigate(`/capabilities/${c.id}`)
                  }}
                >
                  <td data-label="Capability">
                    <span className="mono">{c.id}</span>
                    <span className="note" style={{ display: 'block' }}>
                      {c.summary}
                    </span>
                  </td>
                  <td data-label="Availability">
                    <AvailabilityPill a={c.availability} />
                  </td>
                  <td data-label="Route">
                    {c.activeRoute ? <span className="mono">{c.activeRoute}</span> : '—'}
                  </td>
                  <td data-label="Profiles">{c.profiles.join(', ')}</td>
                  <td data-label="Priority">{c.priority}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <StateBox kind="empty" title="No consumer registered yet">
        When applications integrate, each capability lists who uses it. The simulated installation
        has no real consumer.
      </StateBox>
    </>
  )
}

export function CapabilityDetail() {
  const { id } = useParams()
  const cap = capabilities.find((c) => c.id === id)

  if (!cap) {
    return (
      <>
        <Link to="/capabilities" className="back-link">
          ← Capabilities
        </Link>
        <StateBox kind="failure" title="Unknown capability">
          No capability named <span className="mono">{id}</span> exists in this fixture. Pick one
          from the list.
        </StateBox>
      </>
    )
  }

  return (
    <>
      <Link to="/capabilities" className="back-link">
        ← Capabilities
      </Link>
      <PageHead title={cap.id} purpose={cap.summary}>
        <AvailabilityPill a={cap.availability} />
        <SimTag />
      </PageHead>

      <div className="grid cols-2">
        <Card title="Contract">
          <dl className="kv">
            <dt>Version</dt>
            <dd>
              <span className="mono">{cap.id}@{cap.version}</span>
            </dd>
            <dt>Profiles</dt>
            <dd>{cap.profiles.join(', ')} — accurate never means cloud</dd>
            <dt>Sync / async</dt>
            <dd>{cap.sync}</dd>
            <dt>Limits</dt>
            <dd>{cap.limits}</dd>
            <dt>Max data class</dt>
            <dd>{cap.dataClassMax} — content is processed locally, never logged</dd>
            <dt>Cloud fallback</dt>
            <dd>
              <Pill tone="ok">disabled</Pill>
            </dd>
          </dl>
        </Card>

        <Card title="Route" sub="What would execute this capability">
          {cap.activeRoute ? (
            <dl className="kv">
              <dt>Active route</dt>
              <dd>
                <span className="mono">{cap.activeRoute}</span>
              </dd>
              <dt>Meaning</dt>
              <dd>
                The application calls <span className="mono">{cap.id}</span>; the runtime picks this
                route. Swapping the model behind it never changes the application.
              </dd>
            </dl>
          ) : cap.availability === 'blocked-by-gate' ? (
            <StateBox kind="blocked" title="Blocked by gate">
              The audio family opens at gate G-08. Until then this capability cannot receive a
              route. Nothing is downloadable from this page.
            </StateBox>
          ) : (
            <StateBox kind="empty" title="No approved route">
              A model must reach the approved state on a benchmark before it can serve this
              capability. See Models for candidates.
            </StateBox>
          )}
        </Card>
      </div>

      <Card title="Example" sub="Request and result envelope (fixture)">
        <pre className="code">{`POST /api/v1/jobs
{
  "capability": "${cap.id}",
  "capability_version": "${cap.version}",
  "profile": "balanced",
  "input": { … },
  "policy": { "data_classification": "confidential", "cloud_fallback_allowed": false }
}

→ 200 (simulated)
{
  "status": "succeeded",
  "result": { … },
  "review_required": false,
  "provenance": { "route": "${cap.activeRoute ?? '<no route>'}", "engine": "…", "model_artifacts": ["sha256:…"] }
}`}</pre>
        <span className="note">
          Illustrative only. The exact schema lives in the repository contracts
          (contracts/openapi.yaml).
        </span>
      </Card>
    </>
  )
}
