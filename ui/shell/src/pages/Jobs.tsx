import { Link, useNavigate, useParams } from 'react-router-dom'
import { Card, PageHead, Pill, SimTag, StateBox } from '../components/ui'
import { jobs } from '../fixture/ui00'
import type { JobStatus } from '../fixture/ui00'

function JobStatusPill({ s }: { s: JobStatus }) {
  switch (s) {
    case 'succeeded':
      return <Pill tone="ok">succeeded</Pill>
    case 'queued':
      return <Pill tone="info">queued</Pill>
    case 'running':
      return <Pill tone="info">running</Pill>
    case 'rejected-resources':
      return <Pill tone="warn">refused — not enough resources</Pill>
    case 'failed':
      return <Pill tone="danger">failed</Pill>
    case 'cancelled':
      return <Pill tone="neutral">cancelled</Pill>
  }
}

export function JobsPage() {
  const navigate = useNavigate()
  return (
    <>
      <PageHead
        title="Jobs"
        purpose="Every execution the runtime accepted or refused. Request content is never shown here — only metadata."
      >
        <SimTag label="3 simulated jobs" />
      </PageHead>

      <Card flush>
        <div className="table-wrap">
          <table className="data stack">
            <thead>
              <tr>
                <th scope="col">Job</th>
                <th scope="col">Consumer</th>
                <th scope="col">Capability</th>
                <th scope="col">Status</th>
                <th scope="col">Durations</th>
                <th scope="col">Class</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((j) => (
                <tr
                  key={j.id}
                  className="rowlink"
                  tabIndex={0}
                  onClick={() => navigate(`/jobs/${j.id}`)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') navigate(`/jobs/${j.id}`)
                  }}
                >
                  <td data-label="Job">
                    <span className="mono">{j.id}</span>
                  </td>
                  <td data-label="Consumer">{j.consumer}</td>
                  <td data-label="Capability">
                    <span className="mono">
                      {j.capability}
                    </span>{' '}
                    <span className="note">({j.profile})</span>
                  </td>
                  <td data-label="Status">
                    <JobStatusPill s={j.status} />
                  </td>
                  <td data-label="Durations">
                    {j.status === 'succeeded'
                      ? `queue ${j.queuedMs} ms · load ${j.loadMs} ms · run ${j.runMs} ms`
                      : j.status === 'queued'
                        ? 'waiting for a slot'
                        : '—'}
                  </td>
                  <td data-label="Class">{j.resourceClass}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <StateBox kind="empty" title="No live stream">
        In a running installation this list updates as jobs move through accepted → queued →
        running → finished. UI-00 shows a fixed simulated moment.
      </StateBox>
    </>
  )
}

export function JobDetail() {
  const { id } = useParams()
  const job = jobs.find((j) => j.id === id)

  if (!job) {
    return (
      <>
        <Link to="/jobs" className="back-link">
          ← Jobs
        </Link>
        <StateBox kind="failure" title="Unknown job">
          No job with id <span className="mono">{id}</span> in this fixture.
        </StateBox>
      </>
    )
  }

  const canCancel = job.status === 'queued' || job.status === 'running'

  return (
    <>
      <Link to="/jobs" className="back-link">
        ← Jobs
      </Link>
      <PageHead title={job.id} purpose={job.detail}>
        <JobStatusPill s={job.status} />
        <SimTag />
      </PageHead>

      <div className="grid cols-2">
        <Card title="Execution">
          <dl className="kv">
            <dt>Consumer</dt>
            <dd>{job.consumer}</dd>
            <dt>Capability</dt>
            <dd>
              <Link to={`/capabilities/${job.capability}`} className="mono">
                {job.capability}
              </Link>{' '}
              — profile {job.profile}
            </dd>
            <dt>Submitted</dt>
            <dd>{job.submitted}</dd>
            <dt>Resource class</dt>
            <dd>{job.resourceClass}</dd>
            <dt>Route</dt>
            <dd>{job.route ? <span className="mono">{job.route}</span> : 'none — refused before routing'}</dd>
            <dt>Durations</dt>
            <dd>
              {job.status === 'succeeded'
                ? `queued ${job.queuedMs} ms · model load ${job.loadMs} ms · inference ${job.runMs} ms`
                : 'not applicable'}
            </dd>
            <dt>Review required</dt>
            <dd>{job.reviewRequired ? 'Yes — a human should check the result' : 'No'}</dd>
          </dl>
        </Card>

        <Card title="Payload and provenance">
          <StateBox kind="permission" title="Payload hidden">
            Request and result content are never displayed or logged by default. Inspecting a
            payload is a separate privileged action, disabled in this installation.
          </StateBox>
          {job.warnings.length > 0 ? (
            <div className="callout warn">
              <strong>Warnings:</strong>
              <ul style={{ margin: '4px 0 0', paddingLeft: '1.2em' }}>
                {job.warnings.map((w) => (
                  <li key={w}>{w}</li>
                ))}
              </ul>
            </div>
          ) : (
            <span className="note">No warnings recorded.</span>
          )}
          {job.status === 'rejected-resources' ? (
            <div className="callout">
              <strong>Why refused?</strong> The admission check estimated this job would push memory
              past the hard budget. Refusing before starting protects the other services on this
              machine. The consumer received an explicit resource error, not a timeout.
            </div>
          ) : null}
        </Card>
      </div>

      {canCancel ? (
        <div className="bottom-bar">
          <span className="msg">
            This job is {job.status}. Cancelling would remove it before it consumes resources.
          </span>
          <span style={{ flex: 1 }} />
          <button type="button" className="btn" disabled title="Disabled in UI-00: no runtime backend">
            Cancel job
          </button>
        </div>
      ) : null}
    </>
  )
}
