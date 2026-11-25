"""Apply the emphasis conventions of recent ISSTA/ICSE/ASE RTS papers to paper/main.tex."""
import re
import sys

p = sys.argv[1]
s = open(p).read()


def R(old, new, count=1):
    global s
    n = s.count(old)
    assert n == count, (n, old[:90])
    s = s.replace(old, new)


# ---------- preamble ----------
R(r"""\usepackage{xcolor}
""", r"""\usepackage{xcolor}
\usepackage{xspace}
\usepackage[most]{tcolorbox}
\usepackage{enumitem}
\setlist[itemize,enumerate]{leftmargin=*,topsep=2pt,partopsep=0pt,itemsep=1pt,parsep=0pt}
""")
R(r"""\newcommand{\ph}[1]{\textcolor{red}{[#1]}}
""", r"""\newcommand{\ph}[1]{\textcolor{red}{[#1]}}
% Style conventions (as in recent ISSTA/ICSE/ASE RTS papers):
% - our tool's name in small caps through one macro; baselines keep their authors' spelling, in plain text;
% - run-in paragraph headings in bold sentence case ending with a period, through one macro;
% - italics only for a term at its definition and for the key insight; no bold inside sentences;
% - research questions as a list with bold labels; each RQ ends with a shaded "Answer to RQn" box.
\newcommand{\tool}{\textsc{Proviso}\xspace}
\newcommand{\para}[1]{\smallskip\noindent\textbf{#1}\hspace{0.4em}}
\newtcolorbox{answerbox}[1]{enhanced,breakable,colback=black!5,colframe=black!45,boxrule=0.5pt,arc=1.5pt,
  left=5pt,right=5pt,top=3pt,bottom=3pt,fontupper=\small,before skip=6pt,after skip=6pt,
  title={\textbf{Answer to RQ#1}},coltitle=black,attach title to upper={:\ }}
""")

# ---------- tool name -> \tool in the body (not the title or comments) ----------
s = s.replace(r"\textbf{Proviso}", "Proviso")
head, body = s.split(r"\begin{abstract}", 1)
out = []
for ln in body.split("\n"):
    if not ln.lstrip().startswith("%"):
        ln = re.sub(r"(?<![\w{/\\-])Proviso(?![\w-])", r"\\tool", ln)
    out.append(ln)
s = head + r"\begin{abstract}" + "\n".join(out)
s = s.replace(r"\textbf{\tool}", r"\tool")

# ---------- introduction ----------
R(r"built on one idea: \emph{", r"built on one key insight: \emph{")
R("This paper makes the following contributions:\n\n\\begin{enumerate}",
  "In summary, this paper makes the following contributions:\n\n\\begin{itemize}")
R(r"\item \textbf{Import-time snapshot.} To our knowledge, the first RTS technique that compares,",
  r"\item \textbf{Technique.} We propose, to our knowledge, the first RTS technique that compares,")
R(r"\item \textbf{Per-test attribution of shared execution.} A dynamic recording that credits",
  r"\item \textbf{Attribution.} We record shared execution per test, crediting")
R(r"\item \tool, an open-source RTS tool for pytest", r"\item \textbf{Tool.} We implement \tool, an open-source RTS tool for pytest")
R(r"\item \textbf{An evaluation at the field's standard and beyond:} real history,",
  r"\item \textbf{Evaluation.} We evaluate on real history,")
R(r"We evaluate on real history, real bugs and real agent regressions, six tools, one frozen setup, held-out projects, missed failures and the classic safety measure side by side.",
  r"We evaluate six tools on real history, real bugs and real agent regressions, in one frozen setup with held-out projects, and report missed failures and the classic safety measure side by side.")
R(r"""\item \textbf{A benchmark of \ph{B3: N} real agent regressions} from published SWE-bench agents, reproduced and released with a full-suite ground truth.
\end{enumerate}""", r"""\item \textbf{Benchmark.} We release \ph{B3: N} real agent regressions from published SWE-bench agents, reproduced with a full-suite ground truth.
\end{itemize}""")

# contributions: plain bullets starting with "We ...", as in NameRTS (ISSTA 2026); no bold labels
n_before = s.count(r"\item \textbf{")
s = re.sub(r"\\item \\textbf\{(Technique|Attribution|Tool|Evaluation|Benchmark)\.\} ", r"\\item ", s)
assert n_before - s.count(r"\item \textbf{") == 5, "contribution labels"

# ---------- approach ----------
R(r"\textbf{record} once at a base commit, \textbf{snapshot} the import-time state, \textbf{compare} after each change, and \textbf{select}.",
  r"\emph{record} once at a base commit, \emph{snapshot} the import-time state, \emph{compare} after each change, and \emph{select}.")
for c in ["C1. Detecting import-time changes.", "C2. Linking changed values to tests.", "C3. Execution shared between tests.",
          "C4. Dependencies outside Python code.", "C5. Precision must cost less than it saves."]:
    R(r"\textbf{%s}" % c, r"\textbf{%s}" % c.replace(". ", ": ", 1))
for t in ["changed functions", "changed import-time values", "changed files", "new tests"]:
    R(r"\item \textbf{%s}" % t, r"\item \emph{%s}" % t)

# ---------- evaluation setup: RQs as a list ----------
i = s.index(r"\subsection{Research questions}")
j = s.index(r"\subsection{Benchmarks}")
s = s[:i] + r"""\subsection{Research questions}
We answer four research questions.

\begin{description}
  \item[RQ1 (Effectiveness):] How often does each tool miss a failing test on real changes, and at what cost? We split the results by whether the change touches import-time state.
  \item[RQ2 (Ablation):] What does each part of \tool contribute, and what does the traditional rule cost?
  \item[RQ3 (AI agents):] Does each tool select the tests that AI agents actually break, and does \tool in the loop change agent outcomes, time or cost?
  \item[RQ4 (Overhead):] What do recording and selection cost, and when does recording pay for itself?
\end{description}

RQ1 uses B1 and B1b, with B2 as a secondary benchmark for change kinds; RQ2 uses B1 and B2; RQ3 uses B3 and B4; RQ4 uses B1 and B1b.


""" + s[j:]
for a, b in [("B1, real history.", "B1: Real history."), ("B1b, real bugs.", "B1b: Real bugs."),
             ("B2, targeted changes.", "B2: Targeted changes."), ("B3, agent regressions.", "B3: Agent regressions."),
             ("B4, agents in the loop.", "B4: Agents in the loop.")]:
    R(r"\textbf{%s}" % a, r"\textbf{%s}" % b)
R(r"two scenarios: \textbf{S}, the commit's", r"two scenarios: \emph{S}, the commit's")
R(r"and \textbf{F}, the whole commit", r"and \emph{F}, the whole commit")
for t in ["pytest-testmon", "NameRTS", "EkstaP", "TDAD"]:
    R(r"\textbf{%s}" % t, t)
R(r"\tool's \textbf{traditional} variant", r"\tool's \emph{traditional} variant")
R(r"\item \textbf{Failures} (main measure). Tests that fail", r"\item \textbf{Failures (main measure).} Tests that fail")
R(r"\item \textbf{Affected tests} (the classic safety measure). Tests whose",
  r"\item \textbf{Affected tests (classic safety measure).} Tests whose")
R(r"\item \textbf{NameRTS's own metrics} on its 500 commits: SafeR,", r"\item \textbf{NameRTS's metrics.} On its 500 commits: SafeR,")
R(r"for RQ7, one-time data collection", r"for RQ4, one-time data collection")

# ---------- results: a results placeholder at the top, an answer box at the end of each RQ ----------
R(r"""\subsection{RQ1: Effectiveness on real changes}
\ph{Finding in one sentence: \tool misses X\% of failure-inducing changes vs Y\% (NameRTS) and Z\% (testmon), at T\% of test time.}
""", r"""\subsection{RQ1: Effectiveness on real changes}
\ph{Results paragraph: missed failures and cost per tool (Table~\ref{tab:t2}).}
""")
R(r"""\ph{Finding: X\% of B1 commits change import-time statements; on those changes NameRTS misses Y\% and the traditional rule runs Z\% of test time, while \tool ...}""",
  r"""\ph{X\% of B1 commits change import-time statements; on those changes NameRTS misses Y\% and the traditional rule runs Z\% of test time, while \tool ... (Table~\ref{tab:t3}).}""")
R(r"""\textbf{Targeted changes}\textbf{ (B2).}

\ph{Finding: which change kinds each tool misses, from B2's mutants. Table: change kind by tool, missed / total.}
""", r"""\para{Targeted changes (B2).}\ph{Which change kinds each tool misses, from B2's mutants. Table: change kind by tool, missed / total.}

\begin{answerbox}{1}
\ph{\tool misses X\% of failure-inducing changes against Y\% for NameRTS and Z\% for testmon, at T\% of test time. On changes that touch import-time state, ...}
\end{answerbox}
""")
R(r"""\subsection{RQ2: Ablation}
\ph{Finding: the snapshot is the part that carries safety; the traditional rule is about as safe at much higher cost.}
""", r"""\subsection{RQ2: Ablation}
\ph{Results paragraph: each part switched off in turn (Table~\ref{tab:t4}).}
""")
R(r"""\subsection{RQ3: AI agents}""", r"""\begin{answerbox}{2}
\ph{The import-time snapshot carries most of the safety; the traditional rule is about as safe at much higher cost.}
\end{answerbox}

\subsection{RQ3: AI agents}""")
R(r"""\textbf{Agent regressions (B3).}

\ph{Finding: regressions with every broken test missed, and broken tests missed, per tool, on the full suite.}
""", r"""\para{Agent regressions (B3).}\ph{Regressions with every broken test missed, and broken tests missed, per tool, on the full suite (Table~\ref{tab:t5}).}
""")
R(r"""\textbf{Agents in the loop}\textbf{ (B4).}

\ph{Depends on B4's design. Report outcomes (resolved, tests broken at the end), time and cost per arm, with paired tests; a null result is reported as such.}
""", r"""\para{Agents in the loop (B4).}\ph{Depends on B4's design. Report outcomes (resolved, tests broken at the end), time and cost per arm, with paired tests; a null result is reported as such.}

\begin{answerbox}{3}
\ph{On agent regressions \tool misses X\% of broken tests against Y\% for NameRTS. In the loop, ...}
\end{answerbox}
""")
R(r"""\subsection{RQ4: Overhead}
\ph{Finding: recording takes R minutes per base commit; selection a median of S seconds; recording pays for itself after K test runs, and an agent task with about 9 test runs costs P\% of running everything. Small, fast suites do not pay back within one task.}
""", r"""\subsection{RQ4: Overhead}
\ph{Results paragraph: recording, selection and break-even per project (Table~\ref{tab:t6}).}
""")
R(r"""Other tools' one-time costs (testmon's recording run, NameRTS's initial run, TDAD's index) are reported in the same table.
""", r"""Other tools' one-time costs (testmon's recording run, NameRTS's initial run, TDAD's index) are reported in the same table.

\begin{answerbox}{4}
\ph{Recording takes R minutes per base commit and selection a median of S seconds; recording pays for itself after K test runs, and an agent task with about 9 test runs costs P\% of running everything. Small, fast suites do not pay back within one task.}
\end{answerbox}
""")

# ---------- run-in paragraph headings at the start of a line -> \para ----------
s = re.sub(r"(?m)^\\textbf\{([^{}]*\.)\} ", lambda m: "\\para{%s}" % m.group(1), s)
# the tool's name where it starts a caption or a table header (the \\w lookbehind above skips "{Proviso")
s = s.replace(r"\caption{Proviso end to end", r"\caption{\tool end to end")
for h in ["Proviso missed", "Proviso recording (s)", r"Proviso \% time"]:
    s = s.replace(r"\textbf{%s}" % h, r"\textbf{%s}" % h.replace("Proviso", r"\tool"))
open(p, "w").write(s)
body = s.split(r"\maketitle")[1]
left = [ln[:90] for ln in body.split("\n") if r"\textbf" in ln and not ln.lstrip().startswith((r"\item", "&")) and r"& \textbf" not in ln]
print("bold left outside items/tables:", left)
