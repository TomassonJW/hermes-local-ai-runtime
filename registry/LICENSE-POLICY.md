# Third-party licence policy

## Scope

This policy applies to models, runtimes, libraries, datasets, evaluation corpora, conversion tools, and generated bundles.

## Approval questions

Before a component becomes `candidate` or `approved`, record:

1. exact licence text and identifier;
2. source and revision;
3. whether inference, modification, redistribution, commercial use, hosted use, or derived artefacts are restricted;
4. attribution and notice requirements;
5. acceptable-use or behavioural terms;
6. whether click-through or account-specific acceptance exists;
7. whether converted/quantised artefacts may be redistributed;
8. whether weights may be bundled with a release;
9. whether the licence can change by revision;
10. reviewer and date.

## Repository rules

- Apache-2.0 covers only original repository work.
- Model weights are never committed.
- Public install scripts may download only after displaying source, size, licence, and status.
- An OSI-approved code licence does not automatically cover model weights.
- A permissive model licence still requires source revision and notices.
- Unknown or contradictory terms produce `blocked`, not “probably fine”.
- A component acceptable for private internal inference may still be non-redistributable.
- Generated third-party notices are part of release gates.

## Status

- `pending`: not enough evidence to download in automated flows;
- `accepted`: allowed for declared use;
- `restricted`: allowed only under recorded deployment/distribution constraints;
- `blocked`: not allowed.

## Current candidate policy

Apache-2.0 model artefacts from official repositories are generally eligible for evaluation after revision/hash recording.

Custom licences, including LFM terms or dataset-specific agreements, require explicit review before evaluation or redistribution. This document does not offer legal advice; uncertainty is a release blocker.
