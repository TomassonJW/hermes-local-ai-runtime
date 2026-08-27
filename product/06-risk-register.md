# Risk register

| ID | Risk | Impact | Control |
| --- | --- | --- | --- |
| R-01 | Platform sprawl | High | Thin control plane; compare LocalAI |
| R-02 | CPU/RAM starvation | High | Admission, cgroups, one heavy, pressure metrics |
| R-03 | False vision equivalence | High | Task-family evaluation and abstention |
| R-04 | Consumer/model coupling | High | Capability aliases/registry |
| R-05 | Licence incompatibility | High | Licence gate and notices |
| R-06 | Private data leak | Critical | No payload logs; private mounts |
| R-07 | Supply-chain drift | High | Revision/hash/conversion provenance |
| R-08 | Hidden cloud fallback | Critical | Disabled by default; explicit audit |
| R-09 | API instability | High | Versioned contracts/tests |
| R-10 | Engine lock-in | Medium | Adapter boundary/spike |
| R-11 | Premature GPU design | Medium | Generic workers; defer vendor |
| R-12 | UI becomes playground | Medium | Operator workflows/strong defaults |
| R-13 | Benchmark overfitting | High | Public/private/holdout sets |
| R-14 | Confidence theatre | High | Evidence/calibration, not self-report |
| R-15 | Queue abuse | High | Auth/quotas/size/time limits |
| R-16 | Malformed-media exploit | High | Isolation/limits/patching |
| R-17 | State corruption | Medium | Atomic state/migrations/backups |
| R-18 | Maintenance exceeds value | High | Two-consumer gate/thin architecture |
| R-19 | Hermes integration drift | Medium | Version compatibility tests |
| R-20 | Claims exceed evidence | High | Status language/release gate |

The project accepts slower initial delivery for reversibility and low blast radius. It does not accept best-effort behaviour that silently changes privacy, cost or business data.
