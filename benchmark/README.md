# Benchmark scripts

Code behind [../BENCHMARK_RESULTS.md](../BENCHMARK_RESULTS.md). Requires the packages in `../requirements.txt`.

1. Download the Tranco list (we used list ID **Q2464**) from https://tranco-list.eu and unzip `top-1m.csv`.
2. `python bench.py top-1m.csv results.jsonl`: 1,000 sampled sites (fixed seed) + one inner page each.
3. `python protected.py protected.jsonl`: 110 retail, travel, finance and other high-value sites.
4. `python retry_timeouts.py protected.jsonl protected_retry.json`: re-checks timeouts one at a time.
5. `python cleaning.py results.jsonl cleaning.jsonl`: raw HTML vs `/v1/scrape`-style cleaned text.

Run from this folder. Results vary with your network (home vs cloud) and over time.
