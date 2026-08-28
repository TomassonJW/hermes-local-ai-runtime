# Synthetic evaluation fixtures

Generator: `benchmarks/synthetic/generate.py`.

Public-safe generated cases for:

- JSON schema extraction;
- French text and number formats (`SYN-0042`, `123,45 EUR`);
- OCR with a clean invoice image and an image-only PDF;
- UI screenshot with fictional error `E42`;
- tiny unreadable crop;
- synthetic object/image tests (red/blue boxes, near-duplicate, checkerboard).

Rules:

- no real company invoice template;
- no real addresses, IBANs, account numbers, signatures, or personal identities;
- generator and expected fields versioned together;
- hard cases test abstention, not only success.

Generated binaries stay local (`benchmarks/synthetic/generated/`, gitignored).
