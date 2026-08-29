\# P1 Simulator Benchmark



\## Purpose



This benchmark validates the P1 requirement that IndustriePulse can represent and generate telemetry for 10,000 virtual industrial devices locally.



The benchmark measures deterministic telemetry generation and JSON serialization independently of Azure services, network transport, and filesystem write throughput.



\## Environment



\* Platform: Windows

\* Python: 3.14.2

\* Simulator: IndustriePulse Python simulator

\* Execution mode: local

\* Deterministic seed: 42



\## Workload



\* Virtual machines: 10,000

\* Telemetry cycles: 100

\* Events generated: 1,000,000

\* Logical telemetry interval: 5 seconds

\* Machine types: CNC, compressor, robot



Command:



```text

python benchmark.py --machines 10000 --cycles 100 --seed 42 --result benchmark-result-1m.json

```



\## Results



| Metric                               |             Result |

| ------------------------------------ | -----------------: |

| Virtual machines                     |             10,000 |

| Telemetry cycles                     |                100 |

| Events generated                     |          1,000,000 |

| Inventory creation time              |           0.0671 s |

| Generation and serialization time    |          91.1021 s |

| Total benchmark time                 |          91.1692 s |

| Generation throughput                | 10,976.69 events/s |

| Average serialized payload           |       270.62 bytes |

| Serialized payload throughput        |         2.971 MB/s |

| Peak Python-tracked allocated memory |            1.13 MB |



\## Interpretation



The executed benchmark demonstrates that the local simulator can represent 10,000 virtual machines and generate 1,000,000 deterministic telemetry events across those machines.



Measured generation and JSON serialization throughput was approximately 10,977 events/s. This is roughly 11 times the P0 demo workload of 1,000 events/s.



This comparison demonstrates local simulator generation headroom only. It does not establish equivalent Azure Event Hubs ingestion throughput, end-to-end system throughput, network throughput, consumer capacity, or production infrastructure capacity. Those concerns are measured separately in later phases.



The measured average serialized event size was 270.62 bytes. P0 uses a 350-byte average event size as a conservative production planning assumption. The P1 measurement does not replace that planning assumption.



The benchmark uses `tracemalloc` for memory instrumentation. The reported 1.13 MB value therefore represents peak Python-tracked allocated memory during the measured workload, not the operating system's total process working set.



\## Reproducibility



The simulator uses deterministic machine inventory generation and SHA-256-derived pseudo-random seeds based on the configured seed, machine identity, sequence number, and decision type.



Given identical simulator configuration, seed, machine inventory, sequence, and logical timestamps, the generated telemetry is reproducible.



CLI-level reproducibility is additionally verified by generating equivalent datasets with the same seed and comparing their SHA-256 file hashes.



\## Benchmark Scope



This is an application-level simulator benchmark. It intentionally excludes:



\* Azure Event Hubs ingestion

\* network latency and bandwidth

\* consumer processing

\* checkpoint persistence

\* downstream state storage

\* Service Bus maintenance workflows

\* filesystem write throughput

\* end-to-end processing latency



The benchmark therefore demonstrates simulator capacity rather than complete distributed-system capacity.



Production-scale sizing and executed low-cost infrastructure benchmarks remain separate concerns.



\## P1 Exit Criterion



P1 requirement:



> 10k virtual devices possible locally.



\*\*Status: Passed.\*\*



The executed benchmark represented 10,000 virtual machines and generated 1,000,000 telemetry events locally at 10,976.69 events/s.



