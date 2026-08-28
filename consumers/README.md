# Independent consumers

These adapters speak the native capability API. They are examples, not the
product.

- `client.py`: discover, upload, invoke. No model names.
- `hermes_app.py`: Hermes-shaped text consumer.
- `sillage_app.py`: document intake that persists locally. Sillage does not
  define the runtime.

To wire a new app, load
`integration/hermes/skill/hermes-local-ai-runtime/SKILL.md`. Replace a route
engine without editing consumers. A different `space_id` or capability version
is the only consumer-visible change that forces re-embed or re-extract.
