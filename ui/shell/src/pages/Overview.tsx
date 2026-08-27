import { Link } from 'react-router-dom'
import { Card, PageHead, Pill, SimTag, Meter, StateBox } from '../components/ui'
import { system, capabilities, workers, jobs, resources, updates, evaluations } from '../fixture/ui00'

export default function Overview() {
  const families = [
    { name: 'Text', ready: capabilities.filter((c) => c.family === 'text' && c.availability === 'simulated-ready').length, total: capabilities.filter((c) => c.family === 'text').length },
    { name: 'Vision', ready: capabilities.filter((c) => c.family === 'vision' && c.availability === 'simulated-ready').length, total: capabilities.filter((c) => c.family === 'vision').length },
    { name: 'Documents', ready: capabilities.filter((c) => c.family === 'document' && c.availability === 'simulated-ready').length, total: capabilities.filter((c) => c.family === 'document').length },
    { name: 'Search', ready: capabilities.filter((c) => c.family === 'search' && c.availability === 'simulated-ready').length, total: capabilities.filter((c) => c.family === 'search').length },
    { name: 'Audio', ready: capabilities.filter((c) => c.family === 'audio' && c.availability === 'simulated-ready').length, total: capabilities.filter((c) => c.family === 'audio').length },
  ]

  const queued = jobs.filter((j) => j.status === 'queued').length
  const rejected = jobs.filter((j) => j.status === 'rejected-resources').length
  const pendingUpdates = updates.filter((u) => u.status !== 'blocked').length
  const blockedItems = updates.filter((u) => u.status === 'blocked').length

  return (
    <>
      <PageHead
        title="Overview"
        purpose="Is the runtime ready, what can it do right now, and what needs an operator's attention."
      >
        <SimTag label="all values simulated" />
      </PageHead>

      <Card title="Runtime status">
        <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
          <Pill tone="danger">Not connected</Pill>
          <span className="note">
            This console is the UI-00 shell. It shows how a running installation would look, using
            simulated data only.
          </span>
        </div>
        <ul style={{ margin: 0, paddingLeft: '1.2em' }}>
          {system.reasons.map((r) => (
            <li key={r}>{r}</li>
          ))}
        </ul>
        <div className="note">
          Next operator action: review this shell, then decide whether the runtime backend may be
          built (UI-00 verdict).
        </div>
      </Card>

      <div className="grid cols-3">
        <Card title="Capability coverage" sub="Families ready in the simulated installation">
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th scope="col">Family</th>
                  <th scope="col">Routes ready</th>
                </tr>
              </thead>
              <tbody>
                {families.map((f) => (
                  <tr key={f.name}>
                    <td>{f.name}</td>
                    <td>
                      {f.ready > 0 ? (
                        <Pill tone="ok">
                          {f.ready} of {f.total}
                        </Pill>
                      ) : (
                        <Pill tone="neutral">0 of {f.total}</Pill>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Link to="/capabilities">All capabilities →</Link>
        </Card>

        <Card title="Workers and models" sub="What would be loaded right now">
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th scope="col">Worker</th>
                  <th scope="col">State</th>
                </tr>
              </thead>
              <tbody>
                {workers.map((w) => (
                  <tr key={w.id}>
                    <td>{w.kind}</td>
                    <td>
                      {w.state === 'ready' ? (
                        <Pill tone="ok">ready</Pill>
                      ) : w.state === 'starting' ? (
                        <Pill tone="info">starting</Pill>
                      ) : (
                        <Pill tone="neutral">stopped</Pill>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Link to="/models">Model lifecycle →</Link>
        </Card>

        <Card title="Queue and pressure" sub="Simulated moment in time">
          <Meter
            label="Queue"
            used={resources.queue.depth}
            max={resources.queue.max}
            unit="jobs"
            detail={`${queued} queued, ${rejected} refused for resources in the recent window.`}
          />
          <Meter
            label="Memory (runtime budget)"
            used={resources.memory.usedGib}
            max={resources.memory.hardGib}
            unit="GiB"
            detail="Hard budget. The runtime refuses work before crossing it."
          />
          <div>
            <Pill tone="ok">Pressure: normal</Pill>
          </div>
          <Link to="/resources">Resource detail →</Link>
        </Card>
      </div>

      <div className="grid cols-2">
        <Card title="Waiting on you" sub="Items that need an operator decision">
          <ul style={{ margin: 0, paddingLeft: '1.2em' }}>
            <li>
              {pendingUpdates} update candidate detected — requires evaluation before promotion.{' '}
              <Link to="/updates">Updates</Link>
            </li>
            <li>
              {blockedItems} candidate blocked by licence. Nothing to do unless the licence changes.{' '}
              <Link to="/models">Models</Link>
            </li>
            <li>
              1 evaluation not yet run (update comparison). <Link to="/evaluations">Evaluations</Link>
            </li>
          </ul>
        </Card>

        <Card title="Latest evaluations" sub="Most recent quality checks">
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th scope="col">Suite</th>
                  <th scope="col">Verdict</th>
                </tr>
              </thead>
              <tbody>
                {evaluations.map((e) => (
                  <tr key={e.id}>
                    <td>{e.suite}</td>
                    <td>
                      {e.verdict === 'pass' ? (
                        <Pill tone="ok">pass</Pill>
                      ) : e.verdict === 'regression' ? (
                        <Pill tone="danger">regression</Pill>
                      ) : (
                        <Pill tone="neutral">not run</Pill>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      <StateBox kind="unavailable" title="Live metrics unavailable">
        Real readiness, queue and pressure numbers appear here once a runtime backend exists and
        passes its gates. Until then this page intentionally shows fixture data.
      </StateBox>
    </>
  )
}
