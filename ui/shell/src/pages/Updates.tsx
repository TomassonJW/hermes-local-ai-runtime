import { PageHead, StateBox } from '../components/ui'

export default function Updates() {
  return (
    <>
      <PageHead title="Mises à jour" purpose="Rien ne se promeut tout seul." />
      <StateBox kind="empty" title="Aucun candidat à promouvoir">
        UI-01 n’installe pas de nouveau poids.
      </StateBox>
    </>
  )
}
