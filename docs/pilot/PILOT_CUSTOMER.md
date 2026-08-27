# SentinelLayer Pilot Customer Program

## Target Customers

Program pilot ini ditujukan untuk organisasi dengan 100–1.000 karyawan, aplikasi yang banyak menggunakan API, infrastruktur cloud-native di AWS/GCP/Azure, dan kebutuhan keamanan yang dapat diuji secara terukur.

## Pilot Details

Pilot berlangsung selama 4–6 minggu dengan cakupan awal satu atau dua API non-kritis atau staging yang disepakati bersama. Program dapat diberikan tanpa biaya selama tahap evaluasi, dengan dukungan teknis yang didefinisikan di awal. Production traffic hanya boleh diaktifkan setelah threat model, data handling, rollback path, dan owner operasional disetujui oleh pelanggan.

## Pilot Outcomes dan Evidence

SentinelLayer tidak menjanjikan pemblokiran serangan 100 persen, zero false positives, atau latency tertentu sebelum pengukuran. Pilot harus mengukur detection/block rate pada attack corpus yang disepakati, false-positive dan false-negative samples, p50/p95/p99 latency overhead, availability, error rate, usability dashboard, kualitas audit evidence, serta keberhasilan rollback. Setiap hasil dicatat bersama traffic volume, rule/policy version, environment, dan keterbatasan pengujian.

Keberhasilan pilot ditentukan oleh acceptance criteria tertulis yang disetujui kedua pihak, bukan oleh klaim pemasaran umum. Pelanggan tetap memiliki kontrol untuk memulai dari monitor-only mode, menetapkan exclusions melalui proses change control, dan mengembalikan traffic ke upstream ketika acceptance criteria atau safety condition tidak terpenuhi.

## Outreach Email Template

Subject: SentinelLayer Pilot Program — API Security Evaluation

Hi [Name],

I'm reaching out to offer early access to SentinelLayer, an API security platform with WAF/CRS inspection, rate limiting, behavior signals, risk decisions, and audit-oriented controls.

We're looking for a small number of pilot customers for a 4–6 week evaluation on one or two agreed APIs. The pilot will measure detection quality, false positives, latency overhead, operational workflow, and rollback safety using agreed test traffic and evidence rather than unsupported performance guarantees.

Would you be interested in a 15-minute call to discuss whether the evaluation scope fits your environment?

Best,
[Founder Name]
SentinelLayer

## Next Steps

1. Identify potential customers whose API scope and data handling requirements fit the pilot.
2. Agree on threat model, test corpus, success criteria, access boundaries, retention, and rollback procedure.
3. Run staging or monitor-only evaluation before any production traffic.
4. Enable narrowly scoped enforcement only after customer approval and evidence review.
5. Record measured outcomes, incidents, false positives, false negatives, latency, and operational feedback.
6. Produce a joint acceptance record and decide whether the pilot should end, extend, or proceed to a separately reviewed production engagement.
