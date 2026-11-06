# Benchmark

Run `python scripts/benchmark.py --shots 500 --runs 3`. The script creates a deterministic synthetic
CSV fixture and times full CSV validation, planning, and output generation. Fixture creation and
setup are excluded. Results are local throughput observations, not production-scale guarantees.

## Measured result

On Windows 11 build 26300 with Python 3.12.10, the 500-shot / three-run benchmark completed in
0.031123, 0.032656, and 0.023222 seconds. Median elapsed time was **0.031123 seconds**, or
**16,065.39 shots/second**. CSV fixture generation and setup were outside the timed runs. This is a
local synthetic workload measurement, not a production-scale guarantee.
