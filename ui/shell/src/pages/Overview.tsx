import { Link } from 'react-router-dom'
import { Card, PageHead, Pill, StateBox } from '../components/ui'
import { FUNCTIONS } from '../catalog'
import { useRuntime } from '../runtime'

export default function Overview() {
  const { connected, loading, capabilities, resources, jobs } = useRuntime()
  const ready = capabilities.filter((c) => c.status === 'available').length
  const running = jobs.filter((j) => j.status === 'running' || j.status === 'queued').length

  return (
    <>
      <PageHead
        title="Vue d’ensemble"
        purpose="Le runtime est-il allumé, que peut-il faire, et le serveur est-il sous pression ?"
      >
        {loading ? (
          <Pill tone="neutral">chargement</Pill>
        ) : connected ? (
          <Pill tone="ok">allumé</Pill>
        ) : (
          <Pill tone="danger">éteint</Pill>
        )}
      </PageHead>

      {!connected && !loading ? (
        <StateBox kind="unavailable" title="Pas de moteur">
          La console est là ; le runtime n’écoute pas. Rien n’est inventé.
        </StateBox>
      ) : (
        <div className="grid cols-2">
          <Card title="Maintenant" sub="Mesure live, pas une démo">
            <dl className="kv">
              <dt>Fonctions branchées</dt>
              <dd>{ready}</dd>
              <dt>Jobs en cours / file</dt>
              <dd>{running}</dd>
              <dt>Mémoire encore dispo</dt>
              <dd>
                {resources
                  ? `${(resources.admission.mem_available_mib / 1024).toFixed(1)} Gio`
                  : '—'}
              </dd>
              <dt>Cloud</dt>
              <dd>désactivé</dd>
            </dl>
            <p style={{ marginTop: 12 }}>
              <Link to="/" className="btn primary">
                Essayer une fonction
              </Link>
            </p>
          </Card>
          <Card title="Ce qui est mesuré" sub="Borné, pas universel">
            <ul className="plain">
              {FUNCTIONS.slice(0, 6).map((f) => (
                <li key={f.id}>{f.title}</li>
              ))}
            </ul>
          </Card>
        </div>
      )}
    </>
  )
}
