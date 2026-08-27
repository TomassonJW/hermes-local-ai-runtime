import { Card, Meter, PageHead, Pill, SimTag, StateBox } from '../components/ui'
import { resources, system, workers } from '../fixture/ui00'

export default function Resources() {
  const r = resources
  return (
    <>
      <PageHead
        title="Resources"
        purpose="What the runtime is allowed to use, what it would be using now, and what it refused. Allocated, budgeted, used and estimated are different numbers."
      >
        <SimTag label="simulated pressure" />
      </PageHead>

      <div className="grid cols-2">
        <Card title="Hardware profile" sub="Pinned deployment target">
          <dl className="kv">
            <dt>Profile</dt>
            <dd>
              <span className="mono">{system.hardwareProfile.id}</span>
            </dd>
            <dt>CPU</dt>
            <dd>{system.hardwareProfile.cpu}</dd>
            <dt>Memory</dt>
            <dd>{system.hardwareProfile.ram}</dd>
            <dt>GPU</dt>
            <dd>{system.hardwareProfile.gpu}</dd>
            <dt>Note</dt>
            <dd>{system.hardwareProfile.note}</dd>
          </dl>
        </Card>

        <Card title="Current pressure" sub="Simulated moment in time">
          <div>
            <Pill tone="ok">normal</Pill>{' '}
            <span className="note">
              Health, status and cancel stay responsive even under pressure; batch work is refused
              first.
            </span>
          </div>
          <Meter
            label="CPU (runtime, normal budget)"
            used={r.cpu.usedCores}
            max={r.cpu.budgetNormal}
            unit="cores"
            detail={`Allocated to VM: ${r.cpu.allocatedCores} vCPU. Runtime normal budget: ${r.cpu.budgetNormal}, burst: ${r.cpu.budgetBurst}.`}
          />
          <Meter
            label="Memory (runtime)"
            used={r.memory.usedGib}
            max={r.memory.hardGib}
            unit="GiB"
            detail={`Soft budget ${r.memory.softGib} GiB, hard ${r.memory.hardGib} GiB of ${r.memory.allocatedGib} GiB allocated. Estimated next model load: +${r.memory.estimatedNextLoadGib} GiB (estimate, not a measurement).`}
          />
          <Meter
            label="Queue"
            used={r.queue.depth}
            max={r.queue.max}
            unit="jobs"
            detail={`Oldest waiting ${r.queue.oldestWaitS}s (simulated).`}
          />
        </Card>
      </div>

      <div className="grid cols-2">
        <Card title="Workers and residency" sub="Loaded models consume the budget even when idle">
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th scope="col">Worker</th>
                  <th scope="col">State</th>
                  <th scope="col">Memory</th>
                  <th scope="col">Leases</th>
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
                    <td>{w.memMib > 0 ? `${w.memMib} MiB` : '—'}</td>
                    <td>{w.leases}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <span className="note">
            A lease means a job is actively using the worker; a leased model is never unloaded.
          </span>
        </Card>

        <Card title="Disk and swap">
          <Meter
            label="Model store"
            used={r.disk.modelStoreGib}
            max={r.disk.quotaGib}
            unit="GiB"
            detail={`Quota keeps model downloads from filling the disk. ${r.disk.freeGib} GiB free on the volume.`}
          />
          <div className="callout warn">
            <strong>No swap device.</strong> {r.swap.note}
          </div>
        </Card>
      </div>

      <Card title="Recent admission decisions" sub="Why work was accepted, queued or refused" flush>
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th scope="col">When</th>
                <th scope="col">Event</th>
                <th scope="col">Detail</th>
              </tr>
            </thead>
            <tbody>
              {r.events.map((e) => (
                <tr key={e.text}>
                  <td style={{ whiteSpace: 'nowrap' }}>{e.at}</td>
                  <td>
                    {e.kind === 'admission-refused' ? (
                      <Pill tone="warn">refused</Pill>
                    ) : e.kind === 'queue' ? (
                      <Pill tone="info">queued</Pill>
                    ) : (
                      <Pill tone="neutral">unloaded</Pill>
                    )}
                  </td>
                  <td>{e.text}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <StateBox kind="unavailable" title="No live measurement">
        Real pressure data comes from the runtime's own metrics once it exists. This page shows the
        layout and vocabulary with fixture values.
      </StateBox>
    </>
  )
}
