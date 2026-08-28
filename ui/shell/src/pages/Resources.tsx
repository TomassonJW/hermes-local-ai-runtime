import { Card, Meter, PageHead, Pill, StateBox } from '../components/ui'
import { useRuntime } from '../runtime'

export default function Resources() {
  const { connected, resources } = useRuntime()
  if (!connected || !resources) {
    return (
      <>
        <PageHead title="Ressources" purpose="Mémoire, files et slots mesurés maintenant." />
        <StateBox kind="unavailable" title="Runtime éteint">
          Aucune jauge d’ambiance.
        </StateBox>
      </>
    )
  }
  const a = resources.admission
  const b = resources.budget
  const memUsedEst = Math.max(0, b.hard_memory_mib - a.mem_available_mib)
  const pressure = a.mem_available_mib < a.memory_floor_mib + 1024
  return (
    <>
      <PageHead title="Ressources" purpose="Alloué, budget, utilisé et estimé sont des chiffres différents.">
        <Pill tone={pressure ? 'warn' : 'ok'}>{pressure ? 'pression' : 'calme'}</Pill>
      </PageHead>
      <div className="grid cols-2">
        <Card title="Mémoire" sub="Mesure /proc, pas une démo">
          <Meter
            label="Disponible (machine)"
            used={Number((a.mem_available_mib / 1024).toFixed(1))}
            max={Number((b.hard_memory_mib / 1024).toFixed(1))}
            unit="Gio"
            tone={pressure ? 'warn' : 'ok'}
            detail={`Plancher à laisser : ${(a.memory_floor_mib / 1024).toFixed(1)} Gio. Budget dur runtime ${(b.hard_memory_mib / 1024).toFixed(0)} Gio.`}
          />
          <p className="note">
            Estimé occupé par le reste du système ~{(memUsedEst / 1024).toFixed(1)} Gio — ce n’est pas le RSS du
            modèle.
          </p>
        </Card>
        <Card title="Slots" sub="Un gros job à la fois">
          <Meter label="Jobs lourds" used={a.heavy_leases} max={b.heavy_slots} unit="slot" />
          <Meter label="Jobs légers" used={a.light_leases} max={b.light_slots} unit="slots" />
          <Meter label="File" used={a.queued} max={b.queue_max} unit="jobs" />
          <p className="note">Charge machine (load) : {resources.loadavg.map((n) => n.toFixed(2)).join(' · ')}</p>
        </Card>
      </div>
    </>
  )
}
