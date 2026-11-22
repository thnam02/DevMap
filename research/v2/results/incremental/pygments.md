# Incremental recording check: pygments

- Steps: 20; full re-recordings (selection ran the whole suite, or no clean map): 1
- First full recording: 344.16 s; fresh recordings at check points: median 346.26 s
- Incremental update: median 15.53 s, max 352.74 s; test files re-recorded: median 15
- Map comparisons: 4; tests whose fresh record has something the incremental one lacks: 137; tests only in the fresh map: 0; global record missing: 0
- Selection at the next commit: 3 checks; tests selected only with the fresh map: 0
  - step 5 (e1d0cd038c): [{"test": "tests/test_basic_api.py::test_random_input[BBCBasicLexer]", "missing_in_a": {}, "extra_in_a": {"funcs": [["pygments/lexer.py", 389]]}}, {"test": "tests/test_basic_api.py::test_random_input[BashSessionLexer]", "missing_in_a": {"funcs": [["pygments/lexer.py", 702], ["pygments/lexer.py", 851]]}, "extra_in_a": {}}]
  - step 10 (5b57beacc2): [{"test": "tests/test_basic_api.py::test_random_input[ActionScript3Lexer]", "missing_in_a": {}, "extra_in_a": {"funcs": [["pygments/lexer.py", 389]]}}, {"test": "tests/test_basic_api.py::test_random_input[AntlrRubyLexer]", "missing_in_a": {}, "extra_in_a": {"funcs": [["pygments/lexers/ruby.py", 103]]}}]
  - step 15 (8549c5a796): [{"test": "tests/test_basic_api.py::test_random_input[AmbientTalkLexer]", "missing_in_a": {}, "extra_in_a": {"funcs": [["pygments/lexer.py", 389]]}}, {"test": "tests/test_basic_api.py::test_random_input[BashLexer]", "missing_in_a": {"funcs": [["pygments/lexer.py", 389]]}, "extra_in_a": {}}]
  - step 20 (a43b45dcf0): [{"test": "tests/test_basic_api.py::test_random_input[AspectJLexer]", "missing_in_a": {"funcs": [["pygments/lexer.py", 389]]}, "extra_in_a": {}}, {"test": "tests/test_basic_api.py::test_random_input[AutohotkeyLexer]", "missing_in_a": {}, "extra_in_a": {"funcs": [["pygments/lexer.py", 389]]}}]
