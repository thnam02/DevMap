"""Convert the Proviso paper draft (Claude Docs XML) into an acmart LaTeX file."""
import html
import re
import sys
import xml.etree.ElementTree as ET

SRC, OUT = sys.argv[1], sys.argv[2]
x = open(SRC).read()
# the doc's XML uses single-quoted attributes and html entities; make it parseable
x = html.unescape(x).replace("&", "&amp;")
root = ET.fromstring(x)

CITES = {
    "Alonso et al., 2026": "alonso2026tdad", "Bell and Kaiser, ICSE 2014": "bell2014vmvm",
    "Chen et al., FSE 2026": "chen2026oldtests", "Gligoric et al., ISSTA 2015": "gligoric2015ekstazi",
    "Gyori et al., ISSTA 2015": "gyori2015poldet", "Jimenez et al., ICLR 2024": "jimenez2024swebench",
    "Kauhanen et al., VST 2021": "kauhanen2021rts", "Lam et al., ISSTA 2020": "lam2020dependent",
    "Legunsen et al., ASE 2017": "legunsen2017starts", "Legunsen et al., FSE 2016": "legunsen2016static",
    "Lin et al., ISSTA 2026": "lin2026runornot", "Liu et al., ISSTA 2023": "liu2023fineekstazi",
    "Machalica et al., ICSE-SEIP 2019": "machalica2019predictive", "Malhotra, 2026": "malhotra2026ci",
    "Shi et al., OOPSLA 2019": "shi2019reflection", "Shu et al., 2026": "shu2026resolve",
    "Wang et al., ASE 2024": "wang2024ijacoco", "Wang et al., ICSE 2023": "wang2023urts",
    "Wang et al., ISSTA 2026": "wang2026namerts", "Yoo and Harman, 2012": "yoo2012survey",
    "Zhu et al., ICSE 2019": "zhu2019rtscheck", "pytest-testmon": "testmon",
    "ISSTA 2026": "lin2026runornot", "TOSEM 2024": "lou2024apr", "TSE 2009": "chittimalli2009recomputing",
}
used = set()


def esc(s: str, code: bool = False) -> str:
    s = s.replace("\\", "\x00")
    for a, b in [("&", r"\&"), ("%", r"\%"), ("$", r"\$"), ("#", r"\#"), ("_", r"\_"), ("{", r"\{"), ("}", r"\}"),
                 ("~", r"\textasciitilde{}"), ("^", r"\textasciicircum{}")]:
        s = s.replace(a, b)
    s = s.replace("\x00", r"\textbackslash{}")
    for a, b in [("\u2013", "--"), ("\u2014", "---"), ("\u00d7", r"$\times$"), ("\u2026", r"\ldots{}"),
                 ("\u2019", "'"), ("\u2018", "`"), ("\u2264", r"$\le$"), ("\u2265", r"$\ge$"),
                 ("\u00b7", r"$\cdot$"), ("\u2192", r"$\rightarrow$")]:
        s = s.replace(a, b)
    if code:
        return s
    return re.sub(r'"([^"]*)"', r"``\1''", s)


def brackets(s: str) -> str:
    """[citation] -> \\cite{key}; any other [..] -> \\ph{..} (a placeholder). Input is already escaped."""
    def rep(m):
        inner = m.group(1)
        plain = inner.replace(r"\%", "%")
        if plain in CITES:
            used.add(CITES[plain])
            return "~\\cite{%s}" % CITES[plain]
        return "\\ph{%s}" % inner
    s = re.sub(r"\s*\[([^\[\]]+)\]", lambda m: rep(m) if m.group(1).replace(r"\%", "%") in CITES
               else " " * (m.group(0)[0] == " ") + rep(m), s)
    return s


def runs(el) -> str:
    """Inline content of a paragraph or cell. Brackets are resolved on the joined text, since a placeholder can span
    several runs; code runs are kept out of that pass."""
    out, codes = [], []
    for t in el.iter("text"):
        parts = []
        if t.text:
            parts.append(("plain", t.text))
        for c in t:
            parts.append((c.tag, "".join(c.itertext())))
            if c.tail:
                parts.append(("plain", c.tail))
        for kind, s in parts:
            if kind == "code":
                codes.append("\\texttt{%s}" % esc(s, code=True))
                out.append("\x01%d\x02" % (len(codes) - 1))
            elif kind == "bold":
                out.append("\\textbf{%s}" % esc(s))
            elif kind == "italic":
                out.append("\\emph{%s}" % esc(s))
            else:
                out.append(esc(s))
    s = brackets("".join(out))
    s = re.sub("\x01(\\d+)\x02", lambda m: codes[int(m.group(1))], s)
    return s.strip()


def heading_title(t: str) -> str:
    return re.sub(r"^\d+(\.\d+)*\s+", "", t)


def table(el, n) -> str:
    rows = el.findall("row")
    cols = len(rows[0].findall("cell"))
    head = rows[0]
    widths = ">{\\raggedright\\arraybackslash}p{%.2f\\linewidth}" % FIRST_COL.get(n, 0.16) + ">{\\raggedright\\arraybackslash}X" * (cols - 1)
    lines = ["\\begin{table}[t]", "\\small" if cols < 5 else "\\footnotesize", "\\caption{%s}" % TABLE_CAPTIONS.get(n, "\\ph{caption}"),
             "\\label{tab:t%d}" % n, "\\begin{tabularx}{\\linewidth}{%s}" % widths, "\\toprule"]
    lines.append(" & ".join("\\textbf{%s}" % runs(c) for c in head.findall("cell")) + " \\\\")
    lines.append("\\midrule")
    for r in rows[1:]:
        lines.append(" & ".join(runs(c) for c in r.findall("cell")) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabularx}", "\\end{table}"]
    return "\n".join(lines)


FIRST_COL = {1: 0.18, 4: 0.40}
TABLE_CAPTIONS = {
    1: "Research questions and the benchmarks that answer them.",
    2: "RQ1: missed failures and cost on real changes (B1, scenario S; B1b).",
    3: "RQ1: changes that touch import-time state against the rest (B1).",
    4: "RQ2: Proviso with one part switched off, and the traditional rule (B1).",
    5: "RQ3: agent regressions (B3), full-suite ground truth.",
    6: "RQ4: overhead and break-even per project (B1).",
}

body, abstract, title = [], [], ""
in_abstract = skip = False
tcount = 0
children = list(root)
i = 0
while i < len(children):
    el = children[i]
    i += 1
    tag = el.tag
    if tag == "paragraph" and el.get("heading"):
        lvl, t = el.get("heading"), "".join(el.itertext()).strip()
        if lvl == "1":
            title = t.replace(" (ISSTA 2027)", "").replace(" Paper Draft", "")
            continue
        in_abstract = t == "Abstract"
        skip = t == "References"
        if in_abstract or skip:
            continue
        if t == "Data Availability":
            body.append("\n\\section*{Data Availability}")
        elif lvl == "2":
            body.append("\n\\section{%s}\\label{sec:%s}" % (esc(heading_title(t)), re.sub(r"\W+", "-", heading_title(t).lower()).strip("-")))
        else:
            body.append("\n\\subsection{%s}" % brackets(esc(heading_title(t))))
            if heading_title(t) == "Research questions":
                body.append("Table~\\ref{tab:t1} lists the four research questions and the benchmarks that answer each.\n")
        continue
    if skip:
        continue
    if tag == "paragraph" and not title:
        continue
    if tag == "paragraph":
        s = runs(el)
        if not s or s.startswith("First full draft") or "date" in [c.tag for c in el]:
            continue
        (abstract if in_abstract else body).append(s + "\n")
    elif tag == "list":
        env = "enumerate" if el.get("kind") == "ordered" else "itemize"
        items = ["  \\item " + " ".join(runs(p) for p in li.findall("paragraph")) for li in el.findall("listItem")]
        body.append("\\begin{%s}\n%s\n\\end{%s}\n" % (env, "\n".join(items), env))
    elif tag == "table":
        tcount += 1
        body.append(table(el, tcount) + "\n")
    elif tag == "codeBlock":
        body.append("\\begin{lstlisting}[language=Python]\n%s\n\\end{lstlisting}\n" % "".join(el.itertext()).rstrip())
    elif tag == "embed":
        # the next paragraph is the figure's reading sentence: it becomes the caption
        cap = runs(children[i]) if i < len(children) and children[i].tag == "paragraph" else ""
        i += 1
        body.append("\\begin{figure}[t]\n\\centering\n\\includegraphics[width=\\linewidth]{figures/overview.png}\n"
                    "\\caption{Proviso end to end. %s}\n\\label{fig:overview}\n\\end{figure}\n" % cap)

tex = r"""%% Proviso: ISSTA 2027 submission draft, generated from the paper draft doc on 26 Nov 2026.
%% Red [..] marks are placeholders, filled after the 13 Dec run freeze.
\documentclass[acmsmall,screen,review,anonymous]{acmart}
\usepackage{booktabs}
\usepackage{tabularx}
\usepackage{listings}
\usepackage{xcolor}
\lstset{basicstyle=\ttfamily\small,columns=fullflexible,keepspaces=true,frame=single,showstringspaces=false}
\newcommand{\ph}[1]{\textcolor{red}{[#1]}}

\setcopyright{none}
\acmConference[ISSTA 2027]{ACM SIGSOFT International Symposium on Software Testing and Analysis}{2027}{}

\begin{document}

%% Working title, not yet agreed: settle it with Dr Li (it cannot change after submission).
\title{%(title)s}
\author{Anonymous Author(s)}
\affiliation{\institution{Anonymous Institution}\country{Anonymous}}

\begin{abstract}
%(abstract)s\end{abstract}

\begin{CCSXML}
<ccs2012>
<concept><concept_id>10011007.10011074.10011099.10011102.10011103</concept_id>
<concept_desc>Software and its engineering~Software testing and debugging</concept_desc>
<concept_significance>500</concept_significance></concept>
</ccs2012>
\end{CCSXML}
\ccsdesc[500]{Software and its engineering~Software testing and debugging}
\keywords{regression test selection, Python, import-time state, AI coding agents}

\maketitle
%(body)s
\bibliographystyle{ACM-Reference-Format}
\bibliography{references}

\end{document}
""" % {"title": "Proviso: Regression Test Selection for Python That Sees Import-Time State", "abstract": "\n".join(abstract), "body": "\n".join(body)}
SECS = ["introduction", "background-and-motivating-example", "approach", "implementation", "evaluation-setup",
        "results", "threats-to-validity", "related-work", "conclusion"]
tex = re.sub(r"Section (\d)\b", lambda m: "Section~\\ref{sec:%s}" % SECS[int(m.group(1)) - 1], tex)
tex = tex.replace("(Figure 1)", "(Figure~\\ref{fig:overview})").replace("Figure 1 ", "Figure~\\ref{fig:overview} ")
open(OUT, "w").write(tex)
print("written", OUT, "tables", tcount, "cites used", sorted(used))
