# System context

```text
Hermes Agent      Hermes applications      Other local apps
     \                    |                      /
      +-------------------+---------------------+
                          |
             Hermes Local AI Runtime
                          |
  llama.cpp | OCR/layout | ONNX/vector | whisper.cpp | future workers
                          |
        immutable model store and provenance
```

## Trust zones

Consumers authenticate and submit bounded inputs. They cannot choose arbitrary commands/paths, bypass limits, inspect other jobs or alter routes without operator scope.

The control plane validates, resolves routes, admits resources, coordinates jobs and starts known workers. It never holds consumer database credentials.

Workers receive only required input/config, no consumer credentials, bounded CPU/RAM/time, explicit model paths and isolated writable areas. Model download/conversion is separate maintenance context.

Operators install/promote/deprecate models, change routes and run evaluations. Payload inspection is a separate privileged disabled-by-default action.

Cloud providers and public registries are external. Downloads/fallbacks need explicit policies, pinned provenance and network controls.

## Data classes

| Class | Example | Default |
| --- | --- | --- |
| Public | synthetic fixture/model metadata | public CI allowed |
| Internal | non-sensitive app text | local; metadata logs |
| Confidential | invoices/screenshots/recordings | local only; no payload logs |
| Restricted | credentials/high-risk data | reject absent dedicated policy |
| Secret | keys/tokens | never intentionally accepted/logged |

## Records

Consumer app owns business data/decisions. Runtime metadata owns jobs/routes/models/evaluation/resource events. Model store owns immutable artefacts/manifests. Private corpus mount stays outside Git. Repository owns public-safe code/docs/schemas/fixtures.

A failed worker must not crash the control plane. A process is not ready merely because it exists; it must pass health and capability checks.
