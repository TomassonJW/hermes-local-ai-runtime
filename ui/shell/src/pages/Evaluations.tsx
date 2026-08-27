import { Card, PageHead, Pill, SimTag, StateBox } from '../components/ui'
import { evaluations } from '../fixture/ui00'

export default function Evaluations() {
  return (
    <>
      <PageHead
        title="Evaluations"
        purpose="Quality and resource comparisons that justify promotions. A model serves applications only after its evaluation passes."
      >
        <SimTag label="simulated results" />
      </PageHead>

      <Card flush>
        <div className="table-wrap">
          <table className="data stack">
            <thead>
              <tr>
                <th scope="col">Suite</th>
                <th scope="col">Corpus</th>
                <th scope="col">Target</th>
                <th scope="col">Ran</th>
                <th scope="col">Verdict</th>
              </tr>
            </thead>
            <tbody>
              {evaluations.map((e) => (
                <tr key={e.id}>
                  <td data-label="Suite">
                    {e.suite}
                    <span className="note" style={{ display: 'block' }}>
                      {e.summary}
                    </span>
                  </td>
                  <td data-label="Corpus">
                    {e.corpus === 'public-synthetic' ? (
                      <Pill tone="info">public synthetic</Pill>
                    ) : e.corpus === 'private-local' ? (
                      <Pill tone="neutral">private local</Pill>
                    ) : (
                      <Pill tone="neutral">holdout</Pill>
                    )}
                  </td>
                  <td data-label="Target">
                    <span className="mono">{e.target}</span>
                  </td>
                  <td data-label="Ran">{e.ranAt}</td>
                  <td data-label="Verdict">
                    {e.verdict === 'pass' ? (
                      <Pill tone="ok">pass</Pill>
                    ) : e.verdict === 'regression' ? (
                      <Pill tone="danger">regression</Pill>
                    ) : (
                      <Pill tone="neutral">not run</Pill>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <div className="grid cols-2">
        <Card title="How promotion works" sub="Same corpus, same hardware, same contract">
          <ol style={{ margin: 0, paddingLeft: '1.3em' }}>
            <li>The candidate runs the same suite as the current stable route.</li>
            <li>Quality, latency, memory and failure classes are compared side by side.</li>
            <li>A critical regression blocks promotion, whatever else improved.</li>
            <li>Promotion always preserves a rollback to the previous route.</li>
          </ol>
        </Card>

        <Card title="Corpora" sub="Where evaluation data comes from">
          <dl className="kv">
            <dt>Public synthetic</dt>
            <dd>Openly licensed fixtures committed to the repository. Reproducible by anyone.</dd>
            <dt>Private local</dt>
            <dd>Mounted locally, never committed. Only aggregate scores are stored.</dd>
            <dt>Holdout</dt>
            <dd>Kept aside to detect overfitting to the public set.</dd>
          </dl>
        </Card>
      </div>

      <StateBox kind="stale" title="No real benchmark has run">
        These rows illustrate the evaluation surface. Real numbers appear after the engine spike
        (G-03) produces measured results on the target hardware.
      </StateBox>
    </>
  )
}
