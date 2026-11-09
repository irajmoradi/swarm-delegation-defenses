# Independence references and failure sensitivity

These are exploratory plug-in diagnostics, not a test proving conditional dependence. Calibration is thin.

| Pool | Strategy | W | Observed | Complete case | Worst-case failure upper bound | Continue reference | Absorbing-error reference |
|---|---|---:|---:|---:|---:|---:|---:|
| gpt | reroute | 1 | 18.8% | 18.8% | 18.8% | 17.7% | 17.7% |
| gpt | reroute | 3 | 22.9% | 22.9% | 22.9% | 26.9% | 26.9% |
| gpt | reroute | 6 | 29.2% | 29.2% | 29.2% | 31.4% | 31.4% |
| gpt | retry | 3 | 18.8% | 18.8% | 18.8% | 26.9% | 26.9% |
| gpt | retry | 6 | 14.6% | 14.6% | 14.6% | 31.4% | 31.4% |
| mistral | reroute | 1 | 12.5% | 12.5% | 12.5% | 10.8% | 10.8% |
| mistral | reroute | 3 | 12.5% | 12.5% | 12.5% | 15.6% | 15.6% |
| mistral | reroute | 6 | 22.9% | 22.9% | 22.9% | 18.3% | 18.3% |
| mixed | reroute | 3 | 31.9% | 31.9% | 31.9% | 35.6% | 35.6% |
| mixed | reroute | 6 | 44.1% | 44.1% | 44.1% | 44.5% | 44.5% |
| qwen | reroute | 1 | 20.8% | 20.8% | 20.8% | 17.0% | 17.0% |
| qwen | reroute | 3 | 20.8% | 20.8% | 20.8% | 25.7% | 25.7% |
| qwen | reroute | 6 | 33.3% | 33.3% | 33.3% | 29.9% | 29.9% |

Neither reference models history-retaining retries. Both references include all calibration attempts; absorbing-error additionally terminates on operational/protocol failure. The upper bound treats every failed forbidden episode as a possible violation. It is a sensitivity bound, not a confidence interval.
