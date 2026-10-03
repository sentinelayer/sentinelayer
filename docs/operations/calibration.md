# Offline WAF calibration

Run from `gateway`:

```sh
go run ./cmd/waf-calibrate -rules ../waf/rules -corpus ../tests/fixtures/waf-synthetic-labelled.jsonl -provenance synthetic > /tmp/waf-report.json
```

For a sanitized labelled held-out corpus, use `-provenance held-out`. Each JSONL line contains a unique non-sensitive `id`, `label` (`attack` or `benign`), relative `path`, optional `method`, `headers`, and `body`. Example:

```json
{"id":"sample-001","label":"benign","method":"GET","path":"/search?q=hello"}
```

The command inspects requests using the repository's actual Coraza/CRS engine without sending traffic. It rejects unknown fields, duplicate IDs, invalid labels, absolute destinations and extra JSON. Budgets: 10 MiB file, 10,000 cases, 256 KiB per line, 32 headers. It outputs per-case verdict/rule ID, corpus SHA256, attack-block and benign-block rates, and Wilson 95% intervals. Request paths/bodies/headers are not copied into the report. Review IDs for sensitive information before sharing. Raw customer corpora must remain private; only the developer-authored synthetic fixture belongs in the public repository.

Provenance is a declaration, not verification of representativeness, independent sampling or absence of training/tuning leakage. The report always sets `production_acceptance` to `not_evaluated`. A perfect 10-attack/10-benign synthetic result has a detection lower interval near72% and benign-block upper interval near28%; it cannot establish detection>95% or false positives<5%. Correlated variants do not constitute independent customer evidence.

Customer acceptance requires a separately held-out, labelled and reviewed traffic set with sufficient independent samples, meaningful application/attack categories, recorded CRS/config version, an agreed error budget and full-pipeline behavior/signed-policy evaluation. Do not tune against the final acceptance set or infer full-pipeline accuracy from this WAF-only tool.
