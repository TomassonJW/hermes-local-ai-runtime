import { Card, PageHead, Pill, SimTag, StateBox } from '../components/ui'
import { updates } from '../fixture/ui00'

export default function Updates() {
  return (
    <>
      <PageHead
        title="Updates"
        purpose="Newer revisions and engine versions the runtime has detected. Detection is information, never action: nothing updates itself."
      >
        <SimTag label="simulated detections" />
      </PageHead>

      <Card flush>
        <div className="table-wrap">
          <table className="data stack">
            <thead>
              <tr>
                <th scope="col">Target</th>
                <th scope="col">Kind</th>
                <th scope="col">Detected</th>
                <th scope="col">Disk impact</th>
                <th scope="col">Status</th>
              </tr>
            </thead>
            <tbody>
              {updates.map((u) => (
                <tr key={u.id}>
                  <td data-label="Target">
                    {u.target}
                    <span className="note" style={{ display: 'block' }}>
                      {u.summary}
                    </span>
                  </td>
                  <td data-label="Kind">
                    {u.kind === 'model-revision'
                      ? 'model revision'
                      : u.kind === 'engine-version'
                        ? 'engine version'
                        : 'licence change'}
                  </td>
                  <td data-label="Detected">{u.detected}</td>
                  <td data-label="Disk">{u.diskDeltaGib != null ? `+${u.diskDeltaGib} GiB` : '—'}</td>
                  <td data-label="Status">
                    {u.status === 'evaluation-required' ? (
                      <Pill tone="warn">evaluation required</Pill>
                    ) : u.status === 'blocked' ? (
                      <Pill tone="danger">blocked</Pill>
                    ) : (
                      <Pill tone="info">detected</Pill>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Card title="Update rules" sub="Why there is no update button on this page">
        <ul style={{ margin: 0, paddingLeft: '1.2em' }}>
          <li>Detected only means a newer artefact exists upstream. It says nothing about quality.</li>
          <li>An update candidate must pass the same evaluation suite as the current stable route.</li>
          <li>Promotion is an explicit operator decision with a rollback path.</li>
          <li>An approved route is never switched automatically, even for security releases — those raise a visible alert instead.</li>
        </ul>
      </Card>

      <StateBox kind="empty" title="No engine updates listed">
        Engine version tracking starts once an engine is actually installed (after the G-03 spike).
      </StateBox>
    </>
  )
}
