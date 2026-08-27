# Mission 07 — Hermes integration

## Goal

Make the runtime a canonical Hermes capability source without adding a large duplicated skill.

## Deliverables

- verify supported Hermes version and exact config keys;
- install a thin skill/toolset from `integration/hermes`;
- expose auxiliary vision alias;
- expose MCP tools or native tool adapter for specialised capabilities;
- optional custom main model route remains disabled until hardware/model gate;
- integration tests;
- rollback;
- operator documentation;
- no secrets in Git.

## Hermes usage rules

When Hermes builds an application that needs local AI:

1. inspect runtime capability discovery;
2. select a capability/profile, not a model;
3. copy or generate a thin consumer adapter;
4. keep business rules and persistence in the application;
5. add synthetic contract tests;
6. fail explicitly if capability is unavailable;
7. never bypass runtime resource policy by launching a second unmanaged server.

## Acceptance

Hermes can correctly explain and use the runtime from the thin skill, and one synthetic application integration works.
