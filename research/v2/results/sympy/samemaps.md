# sympy: current Proviso (snapshot format 16) vs v1, both on the v1 dependency maps

| change set | changes | v1 misses | current misses | new misses (v1 caught) | v1 time share | current time share |
|---|---|---|---|---|---|---|
| planted | 91 | 3 | 26 | 23 | 56.5% | 10.1% |
|  new miss: class:sympy/functions/combinatorial/numbers.py:1821 | | | | 1 tests, e.g. sympy/functions/combinatorial/tests/test_comb_numbers.py::test_udivisor_sigma | | |
|  new miss: class:sympy/core/numbers.py:4127 | | | | 39 tests, e.g. sympy/functions/combinatorial/tests/test_comb_factorials.py::test_rf_eval_apply | | |
|  new miss: class:sympy/functions/combinatorial/numbers.py:2043 | | | | 1 tests, e.g. sympy/functions/combinatorial/tests/test_comb_numbers.py::test_mobius | | |
|  new miss: class:sympy/core/basic.py:257 | | | | 1 tests, e.g. sympy/functions/elementary/tests/test_exponential.py::test_log_product | | |
|  new miss: module:sympy/core/assumptions_generated.py:1481 | | | | 3 tests, e.g. sympy/functions/elementary/tests/test_complexes.py::test_Abs | | |
|  new miss: class:sympy/core/numbers.py:3216 | | | | 581 tests, e.g. sympy/functions/combinatorial/tests/test_comb_factorials.py::test_binomial | | |
|  new miss: class:sympy/core/numbers.py:3217 | | | | 581 tests, e.g. sympy/functions/combinatorial/tests/test_comb_factorials.py::test_binomial | | |
|  new miss: class:sympy/core/numbers.py:3060 | | | | 2 tests, e.g. sympy/functions/elementary/tests/test_integers.py::test_frac | | |
|  new miss: class:sympy/core/function.py:327 | | | | 24 tests, e.g. sympy/functions/combinatorial/tests/test_comb_numbers.py::test_bell | | |
|  new miss: class:sympy/functions/elementary/complexes.py:203 | | | | 20 tests, e.g. sympy/functions/combinatorial/tests/test_comb_numbers.py::test_nD_derangements | | |
|  new miss: class:sympy/functions/combinatorial/numbers.py:1869 | | | | 1 tests, e.g. sympy/functions/combinatorial/tests/test_comb_numbers.py::test_legendre_symbol | | |
|  new miss: module:sympy/core/relational.py:1586 | | | | 1 tests, e.g. sympy/functions/elementary/tests/test_piecewise.py::test_issue_10122 | | |
|  new miss: module:sympy/core/assumptions_generated.py:1519 | | | | 2 tests, e.g. sympy/functions/elementary/tests/test_complexes.py::test_Abs_properties | | |
|  new miss: function:sympy/core/operations.py:645 | | | | 581 tests, e.g. sympy/functions/combinatorial/tests/test_comb_factorials.py::test_binomial | | |
|  new miss: class:sympy/core/numbers.py:3568 | | | | 581 tests, e.g. sympy/functions/combinatorial/tests/test_comb_factorials.py::test_binomial | | |
|  new miss: class:sympy/core/numbers.py:2826 | | | | 581 tests, e.g. sympy/functions/combinatorial/tests/test_comb_factorials.py::test_binomial | | |
|  new miss: class:sympy/core/numbers.py:775 | | | | 581 tests, e.g. sympy/functions/combinatorial/tests/test_comb_factorials.py::test_binomial | | |
|  new miss: class:sympy/functions/combinatorial/numbers.py:1983 | | | | 1 tests, e.g. sympy/functions/combinatorial/tests/test_comb_numbers.py::test_kronecker_symbol | | |
|  new miss: class:sympy/functions/special/error_functions.py:129 | | | | 1 tests, e.g. sympy/functions/elementary/tests/test_complexes.py::test_unpolarify | | |
|  new miss: module:sympy/core/assumptions_generated.py:1488 | | | | 1 tests, e.g. sympy/functions/elementary/tests/test_trigonometric.py::test_atan | | |
|  new miss: module:sympy/core/assumptions_generated.py:1484 | | | | 1 tests, e.g. sympy/functions/elementary/tests/test_exponential.py::test_issue_9116 | | |
|  new miss: class:sympy/core/numbers.py:3950 | | | | 581 tests, e.g. sympy/functions/combinatorial/tests/test_comb_factorials.py::test_binomial | | |
|  new miss: class:sympy/core/numbers.py:3520 | | | | 581 tests, e.g. sympy/functions/combinatorial/tests/test_comb_factorials.py::test_binomial | | |
| real | 21 | 0 | 0 | 0 | 44.0% | 42.6% |
