# Sillage consumer example

Sillage is a future consumer example, not the product boundary and not an active integration in this bootstrap.

## Ownership

Sillage owns:

- document intake;
- supplier/customer/expense data;
- deterministic document-family rules;
- candidate retrieval;
- amount/date/identifier invariants;
- user confirmation;
- database writes;
- retention of business evidence.

The runtime owns:

- OCR/layout execution;
- structured extraction;
- embedding;
- reranking of a bounded candidate list;
- general visual interpretation;
- route provenance and resource policy.

The runtime does not hold consumer database credentials.

## Candidate flow

```text
Sillage receives document
  -> extract native PDF text locally/application-side or through capability
  -> deterministic family and field readers
  -> request OCR/parse only where needed
  -> retrieve plausible Sillage candidates
  -> send bounded candidates to reranker
  -> request VLM second pass only for missing/ambiguous fields
  -> validate invariants
  -> display proposal and reasons
  -> user confirms
  -> Sillage writes
```

## Prohibited coupling

- no Sillage database connection string in runtime;
- no model name in Sillage;
- no automatic expense creation;
- no hidden cloud fallback;
- no real Sillage documents in this public repository;
- no Sillage-specific field schema promoted as universal runtime schema.

## Integration timing

Only after the runtime passes the relevant gates. The Sillage repository then owns its adapter and contract tests.
