# RQ7: overhead and break-even (B1, scenario S)

Medians over pairs. Agent task = one map per task, 8.8 test runs per task. Break-even = test runs on one map before its one-time collection has paid off (n/a: the tool's run is not cheaper than running everything).

| Project | Tool | Pairs | Run all (s) | One-time collection (s) | Run with the tool (s) | Offline | Online (collect every commit) | Break-even (runs) | Agent task |
|---|---|---|---|---|---|---|---|---|---|
| sphinx | namerts | 5 | 79.1 | 98.3 | 57.7 | 72% | 195% | 3.2 (1 never) | 86% |
| sphinx | proviso | 5 | 79.1 | 38.1 | 79.3 | 99% | 147% | 35.3 (2 never) | 105% |
| sphinx | run_all | 5 | 79.1 | 0.0 | 79.1 | 100% | 100% | n/a | 100% |
| sphinx | tdad | 5 | 79.1 | 1.7 | 32.2 | 40% | 43% | 0.0 | 40% |
| sphinx | testmon | 5 | 79.1 | 165.2 | 79.0 | 100% | 303% | 698.5 (1 never) | 123% |
| sphinx | traditional | 5 | 79.1 | 38.1 | 79.1 | 100% | 148% | 0.7 (4 never) | 105% |
| sqlglot | namerts | 5 | 51.8 | 68.2 | 42.6 | 83% | 214% | 7.4 (2 never) | 98% |
| sqlglot | proviso | 5 | 51.8 | 74.0 | 43.5 | 83% | 223% | 8.1 | 99% |
| sqlglot | run_all | 5 | 51.8 | 0.0 | 51.8 | 100% | 100% | n/a | 100% |
| sqlglot | tdad | 5 | 51.8 | 1.9 | 15.1 | 28% | 32% | 0.1 | 29% |
| sqlglot | testmon | 5 | 51.8 | 127.5 | 40.7 | 79% | 328% | 4.1 (2 never) | 107% |
| sqlglot | traditional | 5 | 51.8 | 74.0 | 51.7 | 100% | 240% | 5.3 (4 never) | 116% |
| **all** | namerts | 10 | 66.2 | 82.8 | 48.2 | 78% | 205% | 4.4 | 93% |
| **all** | proviso | 10 | 66.2 | 55.1 | 48.2 | 86% | 184% | 8.7 | 102% |
| **all** | run_all | 10 | 66.2 | 0.0 | 66.2 | 100% | 100% | n/a | 100% |
| **all** | tdad | 10 | 66.2 | 1.9 | 30.2 | 38% | 40% | 0.0 | 38% |
| **all** | testmon | 10 | 66.2 | 146.6 | 54.1 | 89% | 306% | 8.7 | 115% |
| **all** | traditional | 10 | 66.2 | 55.1 | 53.5 | 100% | 183% | 3.0 | 105% |
