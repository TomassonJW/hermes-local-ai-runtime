import { PageHead, StateBox } from '../components/ui'

export default function Evaluations() {
  return (
    <>
      <PageHead title="Mesures" purpose="Les rapports publics restent dans le dépôt Git, pas dans cette console." />
      <StateBox kind="stale" title="Pas de campagne live">
        Les lots G-06 à G-08 ont des rapports dans benchmarks/results. Cette page ne relance pas les
        benches.
      </StateBox>
    </>
  )
}
