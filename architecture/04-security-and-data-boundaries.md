# Security and data boundaries

## Network

Bind `127.0.0.1` by default. Use authenticated local reverse proxy or tailnet route only after explicit mission. Never enable public tunnel/wildcard silently. Health may be unauthenticated only on loopback; metrics contain no payloads.

## Auth scopes

Candidates: `capability:invoke:<family>`, `job:read:self`, `job:cancel:self`, `model:read`, `evaluation:run`, `operator:routes`, `operator:models`, `operator:payload-inspect`.

Secrets stay runtime-only. Public config contains names/scopes.

## Inputs

Validate MIME/magic, compressed/decoded size, image dimensions/pixels, PDF pages/parser limits, audio duration/rate/channels, token estimate, JSON depth/schema size. Remote URLs disabled initially. No arbitrary local path. Temporary files random/restricted/quota/cleaned.

## Logging

Metadata yes; content no; hashes policy-dependent; debug payload capture disabled. Any capture is time-bounded, scoped, visibly active and excluded from public support bundles.

## Workers

Read-only models, one bounded input/output workspace, no caller shell template, no consumer credentials, no unrelated paths, no network unless policy requires. Download/conversion separate.

## Supply chain

Record source/revision, filenames/hashes, licence/date, conversion tool/version/parameters, quantisation, compatible engines and remote-code requirement. Remote code blocked by default.

## Consumer boundary

Runtime may rerank bounded candidate records but never connects to consumer DB. Consumer validates and writes.

## Cloud

Remote route is separate adapter/policy. Local failure cannot silently change transport. Record provider/reason/redaction/confirmation/budget.

Public examples use placeholders; actual IP/domain/path/credentials/private corpora are Git-ignored local configuration.
