# Phase 9 Performance & Scalability Benchmark Results

- **Cold-Start Health Latency**: 7.81 ms
- **Warm-Request Health Latency (Avg)**: 4.62 ms

## Batch Processing Throughput & Memory Metrics

| Batch Size | Total Latency (ms) | Throughput (rec/s) | Flagged Anomalies | Feature Gen (ms) | Detection (ms) | RAG Retrieval (ms) | LLM Explainer (ms) | Peak RAM (MB) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 100 | 1771.5 | 56.4 | 90 | 525.1 | 856.4 | 106.1 | 191.0 | 33.14 |
| 1,000 | 9177.1 | 109.0 | 900 | 4524.0 | 1060.8 | 1052.6 | 1839.9 | 33.14 |
| 10,000 | 83736.1 | 119.4 | 9000 | 45485.7 | 1225.6 | 10775.8 | 18925.5 | 132.17 |

*Measurements taken on 64-bit AMD64 architecture with deterministic in-memory Mock LLM provider.*