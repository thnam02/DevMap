| Project | Changes | Full suite, median s | Proviso end to end, median s | End to end / full (total) | End to end / full (median) | Faster than full | Selection median / p90 / max s | Selection / full (total) | Full-suite selections |
|---|---|---|---|---|---|---|---|---|---|
| sqlglot | 147 | 27.4 | 3.6 | 27.6% | 13.1% | 123 of 147 | 1.59 / 3.54 / 10.2 | 6.7% | 20 |
| sympy | 112 | 58.0 | 33.5 | 63.8% | 56.7% | 70 of 112 | 3.43 / 5.97 / 132.5 | 12.2% | 38 |
| sqlalchemy | 124 | 24.2 | 26.9 | 102.6% | 111.0% | 45 of 124 | 2.67 / 5.00 / 38.0 | 14.2% | 78 |
| pygments | 148 | 7.9 | 2.1 | 42.4% | 25.7% | 121 of 148 | 1.74 / 3.36 / 4.2 | 21.4% | 24 |
| datasette | 119 | 63.2 | 64.0 | 73.8% | 101.2% | 49 of 119 | 1.83 / 2.20 / 14.0 | 2.5% | 7 |
| all | 650 | 27.4 | 9.8 | 64.2% | 46.3% | 408 of 650 | 1.78 / 3.75 / 132.5 | 8.7% | 167 |

Slower than the full suite: 242 changes; of these 167 ran the full suite (selection time added on top) and 75 selected less but spent longer selecting than the skipped tests take.
