# Agent patches that leave a Python file unparsable (where the v2.2.1 parse check fires)

449 cases checked; 19 with a changed non-test Python file that parsed at base and no longer parses; 11 not checkable.

| instance | case | sample | broken file(s) | eval-v2.2.jsonl: reproduced / missed | full suite | test time |
|---|---|---|---|---|---|---|
| pallets__flask-4575 | 0 | core | src/flask/app.py | 0 / 0 | True | 100% |
| pallets__flask-5063 | 2 | core | src/flask/cli.py | 0 / 0 | True | 100% |
| pylint-dev__pylint-4970 | 2 | core | pylint/checkers/similar.py | 0 / 0 | False | 80% |
| pallets__flask-4045 | 0 | core | src/flask/blueprints.py | 0 / 0 | False | 43% |
| pydata__xarray-4939 | 1 | core | xarray/core/rolling.py | 0 / 0 | True | 100% |
| sympy__sympy-23117 | 0 | core | sympy/tensor/array/ndim_array.py | 0 / 0 | False | 24% |
| mwaskom__seaborn-3187 | 2 | core | seaborn/_core/scales.py | 0 / 0 | True | 100% |
| sphinx-doc__sphinx-10673 | 0 | core | sphinx/directives/other.py | 9 / 0 | True | 100% |
| pydata__xarray-6744 | 3 | core | clean_iter_method.py, final_clean_iter.py, new_iter_method.py | 2 / 0 | True | 100% |
| sympy__sympy-24539 | 1 | held-out | sympy/polys/rings.py | no row |  |  |
| pydata__xarray-6938 | 1 | held-out | xarray/core/dataset.py | 0 / 0 | True | 100% |
| pydata__xarray-7393 | 0 | held-out | xarray/core/dataset.py | 0 / 0 | False | 1% |
| pydata__xarray-7233 | 1 | held-out | xarray/core/rolling.py | 189 / 187 | False | 0% |
| sphinx-doc__sphinx-9602 | 2 | held-out | sphinx/util/typing.py | 0 / 0 | False | 9% |
| pydata__xarray-7229 | 1 | held-out | xarray/core/computation.py | 0 / 0 | True | 100% |
| sympy__sympy-22914 | 2 | held-out | sympy/printing/pycode.py | no row |  |  |
| sympy__sympy-21930 | 1 | held-out | sympy/printing/latex.py | no row |  |  |
| sympy__sympy-23262 | 3 | held-out | sympy/utilities/lambdify.py | no row |  |  |
| sphinx-doc__sphinx-10451 | 3 | held-out | sphinx/ext/autodoc/__init__.py | 0 / 0 | True | 100% |

Not checkable: pallets__flask-5063 c0: patch does not apply: agent patch does not apply: error: src/flask/cli.py: No such file or directory
e; sympy__sympy-21055 c1: patch does not apply: agent patch does not apply: error: git diff header lacks filename information (l; pytest-dev__pytest-11148 c0: patch does not apply: agent patch does not apply: error: src/_pytest/pathlib.py: No such file or direc; sphinx-doc__sphinx-11445 c0: patch does not apply: agent patch does not apply: <stdin>:16: trailing whitespace.
    
<stdin>:47: tr; sympy__sympy-24562 c4: patch does not apply: agent patch does not apply: error: sympy/core/numbers.py: No such file or direct; sympy__sympy-22456 c1: patch does not apply: agent patch does not apply: error: sympy/codegen/ast.py: No such file or directo; sympy__sympy-23262 c2: patch does not apply: agent patch does not apply: iled: sympy/printing/pycode.py:553
error: sympy/prin; sympy__sympy-24661 c1: patch does not apply: agent patch does not apply: stdin>:25: trailing whitespace.
            
<stdin>; sphinx-doc__sphinx-10451 c0: patch does not apply: agent patch does not apply: <stdin>:16: trailing whitespace.
            
error:; sphinx-doc__sphinx-9658 c4: patch does not apply: agent patch does not apply: error: sphinx/util/typing.py: No such file or direct; sphinx-doc__sphinx-10325 c2: patch does not apply: agent patch does not apply: ctory
error: tests/test_ext_autodoc.py: No such file
