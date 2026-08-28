import { useEffect, useMemo, useState } from 'react'
import { Card, PageHead, Pill, StateBox } from '../components/ui'
import { FUNCTIONS, PROFILE_LABELS, type FnDef } from '../catalog'
import { useRuntime } from '../runtime'
import { ApiError, submitJob, uploadBytes, waitJob } from '../api'

function ResultView({ data }: { data: Record<string, unknown> }) {
  const result = (data.result as Record<string, unknown>) || data
  const fields = (result.data as Record<string, unknown>) || (result.fields as Record<string, unknown>)
  const text = typeof result.text === 'string' ? result.text : typeof result.output === 'string' ? result.output : null
  return (
    <div className="result-block">
      {fields ? (
        <dl className="kv">
          {Object.entries(fields).map(([k, v]) => (
            <div key={k}>
              <dt>{k}</dt>
              <dd>{v == null || v === '' ? '—' : String(v)}</dd>
            </div>
          ))}
        </dl>
      ) : null}
      {text ? <pre className="result-text">{text}</pre> : null}
      {Array.isArray(result.candidates) ? (
        <ol className="rank-list">
          {(result.candidates as { id: string; score: number; rank: number }[]).map((c) => (
            <li key={c.id}>
              {c.rank}. {c.id} <span className="note">({c.score.toFixed(3)})</span>
            </li>
          ))}
        </ol>
      ) : null}
      {typeof result.dimensions === 'number' ? (
        <p>
          {result.dimensions} dimensions · espace <span className="mono">{String(result.space_id)}</span>
          . Les vecteurs restent chez toi, pas dans le runtime.
        </p>
      ) : null}
      <details>
        <summary>Détail technique</summary>
        <pre className="result-json">{JSON.stringify(data, null, 2)}</pre>
      </details>
    </div>
  )
}

export default function Try() {
  const { connected, loading, capabilities, resources } = useRuntime()
  const available = useMemo(() => new Set(capabilities.map((c) => c.id)), [capabilities])
  const [fnId, setFnId] = useState('document.extract_structured')
  useEffect(() => {
    if (available.has(fnId)) return
    const first = FUNCTIONS.find((item) => available.has(item.id))
    if (first) setFnId(first.id)
  }, [available, fnId])
  const fn = FUNCTIONS.find((f) => f.id === fnId) as FnDef
  const cap = capabilities.find((c) => c.id === fnId)
  const profiles = cap?.profiles?.length ? cap.profiles : ['balanced']
  const [profile, setProfile] = useState('balanced')
  const activeProfile = profiles.includes(profile) ? profile : profiles[0]
  const [text, setText] = useState('')
  const [question, setQuestion] = useState('Que se passe-t-il sur cette image ?')
  const [query, setQuery] = useState('')
  const [docs, setDocs] = useState('')
  const [fileA, setFileA] = useState<File | null>(null)
  const [fileB, setFileB] = useState<File | null>(null)
  const [busy, setBusy] = useState(false)
  const [status, setStatus] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<Record<string, unknown> | null>(null)

  const memGi = resources ? (resources.admission.mem_available_mib / 1024).toFixed(1) : null
  const missing = connected && !available.has(fnId)

  async function run() {
    setBusy(true)
    setError(null)
    setResult(null)
    setStatus('envoi')
    try {
      let input: Record<string, unknown> = {}
      if (fn.input === 'text') {
        if (!text.trim()) throw new Error('Écris un texte.')
        input = { prompt: text }
      } else if (fn.input === 'texts') {
        const items = text.split('\n').map((line) => line.trim()).filter(Boolean)
        if (!items.length) throw new Error('Une ligne = un texte.')
        input = { texts: items }
      } else if (fn.input === 'query-docs') {
        const candidates = docs.split('\n').map((line) => line.trim()).filter(Boolean)
        if (!query.trim() || candidates.length < 2) throw new Error('Une requête et au moins deux passages.')
        input = { query, candidates }
      } else if (fn.input === 'file-question') {
        if (!fileA) throw new Error('Choisis une image.')
        if (!question.trim()) throw new Error('Pose une question.')
        setStatus('téléversement')
        const upload_id = await uploadBytes(await fileA.arrayBuffer(), fileA.type || 'image/png')
        input = { upload_id, question }
      } else if (fn.input === 'two-files') {
        if (!fileA || !fileB) throw new Error('Deux images sont nécessaires.')
        setStatus('téléversement')
        const a = await uploadBytes(await fileA.arrayBuffer(), fileA.type || 'image/png')
        const b = await uploadBytes(await fileB.arrayBuffer(), fileB.type || 'image/png')
        input = { images: [{ upload_id: a }, { upload_id: b }] }
      } else {
        if (!fileA) throw new Error('Choisis un fichier.')
        setStatus('téléversement')
        const upload_id = await uploadBytes(await fileA.arrayBuffer(), fileA.type || 'application/octet-stream')
        input = { upload_id }
      }
      setStatus('file d’attente')
      const submitted = await submitJob(fnId, input, activeProfile, cap?.version || '1.0.0')
      const payload = await waitJob(submitted.job_id, fn.timeoutMs, setStatus)
      setResult(payload)
      setStatus('terminé')
    } catch (err) {
      setStatus(null)
      setError(err instanceof ApiError ? err.message : err instanceof Error ? err.message : 'échec')
    } finally {
      setBusy(false)
    }
  }

  if (!connected && !loading) {
    return (
      <>
        <PageHead title="Essayer" purpose="Envoie un fichier ou un texte au runtime local, sans passer par le cloud." />
        <StateBox kind="unavailable" title="Runtime éteint">
          Le moteur n’écoute pas. Rien n’est simulé ici. Relance le runtime loopback, puis rafraîchis.
        </StateBox>
      </>
    )
  }

  return (
    <>
      <PageHead title="Essayer" purpose="Choisis une fonction, une qualité, puis envoie un fichier ou un texte. Un seul gros travail à la fois.">
        {memGi ? (
          <Pill tone="ok">{memGi} Gio libres</Pill>
        ) : (
          <Pill tone="neutral">connexion…</Pill>
        )}
      </PageHead>

      <div className="try-layout">
        <Card title="Fonction" sub="Ce que tu veux obtenir, pas un nom de fichier modèle">
          <div className="fn-grid" role="list">
            {FUNCTIONS.map((item) => {
              const on = available.has(item.id)
              return (
                <button
                  key={item.id}
                  type="button"
                  className={`fn-card${fnId === item.id ? ' selected' : ''}${on ? '' : ' missing'}`}
                  onClick={() => {
                    setFnId(item.id)
                    setResult(null)
                    setError(null)
                  }}
                >
                  <strong>{item.title}</strong>
                  <span>{item.blurb}</span>
                  {!on && connected ? <em>pas branchée</em> : null}
                </button>
              )
            })}
          </div>
        </Card>

        <Card
          title={fn.title}
          sub={fn.blurb}
        >
          {missing ? (
            <StateBox kind="blocked" title="Cette fonction n’est pas allumée">
              Le runtime tourne, mais aucune route n’est configurée pour {fn.id}.
            </StateBox>
          ) : (
            <>
              <div className="field">
                <label id="lbl-profile">Qualité</label>
                <div className="seg" role="group" aria-labelledby="lbl-profile">
                  {profiles.map((p) => (
                    <button
                      key={p}
                      type="button"
                      aria-pressed={activeProfile === p}
                      onClick={() => setProfile(p)}
                    >
                      {PROFILE_LABELS[p] || p}
                    </button>
                  ))}
                </div>
                <span className="hint">Rapide = plus léger. Équilibré = le défaut. Précis seulement s’il est proposé.</span>
              </div>

              {fn.input === 'text' || fn.input === 'texts' ? (
                <div className="field">
                  <label htmlFor="try-text">{fn.input === 'texts' ? 'Textes (une ligne chacun)' : 'Texte'}</label>
                  <textarea id="try-text" rows={6} value={text} onChange={(e) => setText(e.target.value)} />
                </div>
              ) : null}

              {fn.input === 'query-docs' ? (
                <>
                  <div className="field">
                    <label htmlFor="try-query">Requête</label>
                    <input id="try-query" value={query} onChange={(e) => setQuery(e.target.value)} />
                  </div>
                  <div className="field">
                    <label htmlFor="try-docs">Passages (une ligne chacun)</label>
                    <textarea id="try-docs" rows={6} value={docs} onChange={(e) => setDocs(e.target.value)} />
                  </div>
                </>
              ) : null}

              {fn.input === 'file-question' || fn.input === 'file' || fn.input === 'two-files' ? (
                <div className="field">
                  <span id="try-file-lbl">{fn.input === 'two-files' ? 'Image A' : 'Fichier'}</span>
                  <div className="file-row">
                    <label className="btn" htmlFor="try-file">
                      {fileA ? 'Changer de fichier' : 'Choisir un fichier'}
                    </label>
                    <input
                      id="try-file"
                      className="sr-only"
                      type="file"
                      accept={fn.accept}
                      onChange={(e) => setFileA(e.target.files?.[0] || null)}
                    />
                    <span className="hint">{fileA ? fileA.name : 'Aucun fichier'}</span>
                  </div>
                </div>
              ) : null}

              {fn.input === 'two-files' ? (
                <div className="field">
                  <span id="try-file-b-lbl">Image B</span>
                  <div className="file-row">
                    <label className="btn" htmlFor="try-file-b">
                      {fileB ? 'Changer de fichier' : 'Choisir un fichier'}
                    </label>
                    <input
                      id="try-file-b"
                      className="sr-only"
                      type="file"
                      accept={fn.accept}
                      onChange={(e) => setFileB(e.target.files?.[0] || null)}
                    />
                    <span className="hint">{fileB ? fileB.name : 'Aucun fichier'}</span>
                  </div>
                </div>
              ) : null}

              {fn.input === 'file-question' ? (
                <div className="field">
                  <label htmlFor="try-q">Question</label>
                  <input id="try-q" value={question} onChange={(e) => setQuestion(e.target.value)} />
                </div>
              ) : null}

              <div className="row" style={{ marginTop: 12, gap: 12 }}>
                <button type="button" className="btn primary" disabled={busy || loading} onClick={() => void run()}>
                  {busy ? 'En cours…' : 'Lancer'}
                </button>
                {status ? <span className="note">État : {status}</span> : null}
              </div>
              {error ? (
                <StateBox kind="failure" title="Pas de résultat">
                  {error}
                </StateBox>
              ) : null}
              {result ? (
                <div style={{ marginTop: 16 }}>
                  <h3 className="subhead">Résultat</h3>
                  <ResultView data={result} />
                </div>
              ) : null}
            </>
          )}
        </Card>
      </div>
    </>
  )
}
