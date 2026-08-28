import { PageHead, StateBox } from '../components/ui'

export function ModelsPage() {
  return (
    <>
      <PageHead
        title="Modèles"
        purpose="Le cycle de vie (découvert → approuvé) n’est pas encore un magasin opérateur."
      />
      <StateBox kind="blocked" title="Pas un sélecteur de fichier">
        Les applications choisissent une fonction et une qualité. Les poids restent hors Git, dans le
        spike local, et ne sont pas promus.
      </StateBox>
    </>
  )
}

export function ModelDetail() {
  return <StateBox kind="blocked" title="Fiche modèle absente de UI-01" />
}
