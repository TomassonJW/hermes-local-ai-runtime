import { Link, useParams } from 'react-router-dom'
import { Card, PageHead, Pill, StateBox } from '../components/ui'
import { FUNCTIONS, PROFILE_LABELS } from '../catalog'
import { useRuntime } from '../runtime'

export function CapabilitiesPage() {
  const { connected, capabilities } = useRuntime()
  return (
    <>
      <PageHead title="Fonctions" purpose="Contrats stables que les applis appellent. Pas des noms de fichiers modèle." />
      {!connected ? (
        <StateBox kind="unavailable" title="Runtime éteint" />
      ) : (
        <Card flush>
          <div className="table-wrap">
            <table className="data stack">
              <thead>
                <tr>
                  <th>Fonction</th>
                  <th>Qualités</th>
                  <th>Moteur</th>
                </tr>
              </thead>
              <tbody>
                {capabilities.map((c) => {
                  const label = FUNCTIONS.find((f) => f.id === c.id)?.title || c.id
                  const engines = [...new Set(c.routes.map((r) => r.engine))]
                  return (
                    <tr key={`${c.id}@${c.version}`}>
                      <td>
                        <Link to={`/capabilities/${c.id}`}>{label}</Link>
                        <div className="note mono">{c.id}</div>
                      </td>
                      <td>{c.profiles.map((p) => PROFILE_LABELS[p] || p).join(' · ')}</td>
                      <td>{engines.join(' · ')}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </>
  )
}

export function CapabilityDetail() {
  const { id } = useParams()
  const { connected, capabilities } = useRuntime()
  const cap = capabilities.find((c) => c.id === id)
  const label = FUNCTIONS.find((f) => f.id === id)?.title || id
  if (!connected) return <StateBox kind="unavailable" title="Runtime éteint" />
  if (!cap) return <StateBox kind="failure" title="Fonction inconnue">{id}</StateBox>
  return (
    <>
      <PageHead title={label || cap.id} purpose={cap.id} />
      <Card title="Routes">
        <ul className="plain">
          {cap.routes.map((r, i) => (
            <li key={`${r.profile}-${i}`}>
              {PROFILE_LABELS[r.profile] || r.profile} · {r.engine} · {r.resource_class}
            </li>
          ))}
        </ul>
        <p>
          <Pill tone="ok">cloud désactivé</Pill>
        </p>
      </Card>
    </>
  )
}
