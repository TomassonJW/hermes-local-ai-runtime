import { useNavigate, useParams } from 'react-router-dom'
import { Card, PageHead, Pill, StateBox } from '../components/ui'
import { useRuntime } from '../runtime'

function StatusPill({ s }: { s: string }) {
  if (s === 'succeeded') return <Pill tone="ok">terminé</Pill>
  if (s === 'queued') return <Pill tone="info">en file</Pill>
  if (s === 'running') return <Pill tone="info">en cours</Pill>
  if (s === 'rejected') return <Pill tone="warn">refusé</Pill>
  if (s === 'failed') return <Pill tone="danger">échec</Pill>
  if (s === 'cancelled') return <Pill tone="neutral">annulé</Pill>
  return <Pill tone="neutral">{s}</Pill>
}

export function JobsPage() {
  const { connected, jobs } = useRuntime()
  const navigate = useNavigate()
  return (
    <>
      <PageHead title="Jobs" purpose="Exécutions réelles. Le contenu des fichiers n’est pas affiché." />
      {!connected ? (
        <StateBox kind="unavailable" title="Runtime éteint">
          Pas de liste simulée.
        </StateBox>
      ) : jobs.length === 0 ? (
        <StateBox kind="empty" title="Aucun job pour l’instant">
          Lance une fonction depuis Essayer.
        </StateBox>
      ) : (
        <Card flush>
          <div className="table-wrap">
            <table className="data stack">
              <thead>
                <tr>
                  <th scope="col">Job</th>
                  <th scope="col">Fonction</th>
                  <th scope="col">État</th>
                  <th scope="col">Durée</th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((j) => (
                  <tr
                    key={j.job_id}
                    className="rowlink"
                    tabIndex={0}
                    onClick={() => navigate(`/jobs/${j.job_id}`)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') navigate(`/jobs/${j.job_id}`)
                    }}
                  >
                    <td data-label="Job">
                      <span className="mono">{j.job_id}</span>
                    </td>
                    <td data-label="Fonction">
                      <span className="mono">{j.capability}</span>{' '}
                      <span className="note">({j.profile})</span>
                    </td>
                    <td data-label="État">
                      <StatusPill s={j.status} />
                    </td>
                    <td data-label="Durée">
                      {j.timing?.total_ms != null ? `${j.timing.total_ms} ms` : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </>
  )
}

export function JobDetail() {
  const { id } = useParams()
  const { jobs, connected } = useRuntime()
  const job = jobs.find((j) => j.job_id === id)
  if (!connected) {
    return <StateBox kind="unavailable" title="Runtime éteint" />
  }
  if (!job) {
    return <StateBox kind="failure" title="Job inconnu">{id}</StateBox>
  }
  return (
    <>
      <PageHead title={job.job_id} purpose={`${job.capability} · ${job.profile}`} />
      <Card title="Métadonnées">
        <dl className="kv">
          <dt>État</dt>
          <dd>
            <StatusPill s={job.status} />
          </dd>
          <dt>Route</dt>
          <dd className="mono">{job.route_id || '—'}</dd>
          <dt>Erreur</dt>
          <dd>{job.error?.message || '—'}</dd>
        </dl>
        <p className="note">Le contenu envoyé reste caché.</p>
      </Card>
    </>
  )
}
